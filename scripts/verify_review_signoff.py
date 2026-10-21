"""Verify that every reviewed/approved requirement is attributable to a
commit signed by a trusted human reviewer -- not just a correct content hash.

scripts/validate_iso26262.py's stamp check only proves an item's content has
not changed since *some* commit set `reviewed`. The stamp is
sha256(uid, text, ref, links, ...): a public, reproducible content hash with
no secret, so anyone who can `import doorstop` can compute the exact value
`doorstop review` would write, without ever running it or being a human (see
tests/test_hardening.py::test_iso_accepts_a_correctly_computed_stamp_without_doorstop_review).

This script closes that gap for the one thing a forger genuinely cannot
reproduce: a cryptographic signature from a private key they don't hold.
For each reviewed/approved item it finds, via `git blame`, the exact commits
that introduced the item's current `reviewed:` line AND its current `status:`
line, and requires each to carry a signature from a GPG fingerprint listed in
reviewers.yml for a GitHub username that owns the item's path in
.github/CODEOWNERS. Both lines matter: a human can sign the review while the
item is still a draft, and checking only the stamp would then let an unsigned
later commit flip `status: draft` to `approved`.

Usage: python scripts/verify_review_signoff.py [REQ_DIR ...] [--root PATH]
  (default REQ_DIRs: reqs/SRD reqs/SWR reqs/TST; default --root: cwd)

Exits 1 if any reviewed/approved item cannot be attributed this way. Fails
closed: an unsigned commit, a signature from an untrusted key, a key not in
the local keyring, unparseable blame output, or no reviewers.yml entry for
the owning path all count as failure, same as a missing stamp.
"""
import subprocess
import sys
from pathlib import Path

import yaml

DOCUMENTS = ["reqs/SRD", "reqs/SWR", "reqs/TST"]


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def load_reviewer_fingerprints(root: Path) -> dict:
    """codeowner username -> set of trusted GPG fingerprints."""
    reviewers_file = root / "reviewers.yml"
    if not reviewers_file.exists():
        return {}
    data = yaml.safe_load(reviewers_file.read_text(encoding="utf-8")) or {}
    out = {}
    for entry in data.get("reviewers", []) or []:
        owner = entry.get("codeowner")
        fps = {str(fp).replace(" ", "").upper() for fp in entry.get("gpg_fingerprints") or []}
        if owner:
            out[owner] = fps
    return out


def load_codeowners(root: Path) -> list:
    """[(path_prefix, {usernames})], in file order, first match wins (CODEOWNERS semantics)."""
    codeowners_file = root / ".github" / "CODEOWNERS"
    if not codeowners_file.exists():
        return []
    rules = []
    for line in codeowners_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        prefix = parts[0].lstrip("/")
        owners = {p.lstrip("@") for p in parts[1:]}
        rules.append((prefix, owners))
    return rules


def owners_for(path: Path, root: Path, codeowners: list) -> set:
    rel = str(path.relative_to(root))
    matches = set()
    for prefix, owners in codeowners:
        if rel.startswith(prefix):
            matches = owners  # last matching rule wins, as in real CODEOWNERS
    return matches


def trusted_fingerprints_for(path: Path, root: Path, codeowners: list, reviewer_fps: dict) -> set:
    fps = set()
    for owner in owners_for(path, root, codeowners):
        fps |= reviewer_fps.get(owner, set())
    return fps


def line_commit(path: Path, root: Path, key: str) -> str | None:
    """Commit hash that introduced the item's current `<key>:` line."""
    rel = str(path.relative_to(root))
    r = run(["git", "blame", "--porcelain", "-L", f"/^{key}:/,+1", "--", rel], cwd=root)
    if r.returncode != 0 or not r.stdout:
        return None
    return r.stdout.split()[0]


def commit_signature(commit: str, root: Path) -> tuple:
    """(status, fingerprint). status follows `git log --format=%G?`: G=good, U=good/untrusted,
    B=bad, N=no signature, X/Y=expired, R=revoked, E=cannot check (no pubkey)."""
    r = run(["git", "log", "-1", "--format=%G?%x1f%GF", commit], cwd=root)
    if r.returncode != 0 or not r.stdout.strip():
        return "N", ""
    status, _, fp = r.stdout.strip().partition("\x1f")
    return status, fp.replace(" ", "").upper()


def check_item(path: Path, root: Path, codeowners: list, reviewer_fps: dict) -> str | None:
    """None if fine, else an error string."""
    try:
        item = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError):
        return None  # schema validator's job; don't double-report
    if not isinstance(item, dict) or item.get("status") not in ("reviewed", "approved"):
        return None

    trusted = trusted_fingerprints_for(path, root, codeowners, reviewer_fps)
    if not trusted:
        return f"{path.name}: no trusted reviewer fingerprint configured for this path in reviewers.yml"

    for key in ("reviewed", "status"):
        error = check_line(path, root, key, trusted)
        if error:
            return error
    return None


def check_line(path: Path, root: Path, key: str, trusted: set) -> str | None:
    """None if the commit that set this item's `<key>:` line is signed by a trusted reviewer."""
    commit = line_commit(path, root, key)
    if not commit:
        return f"{path.name}: cannot attribute the '{key}:' line to a commit (git blame failed)"

    status, fingerprint = commit_signature(commit, root)
    if status in ("G", "U") and fingerprint in trusted:
        return None
    if status in ("G", "U"):
        return f"{path.name}: '{key}:' commit {commit[:12]} signed by {fingerprint or '(unknown)'}, not a trusted reviewer for this path"
    reason = {"N": "unsigned", "B": "bad signature", "E": "signing key not in local keyring",
              "X": "signature expired", "Y": "signing key expired", "R": "signing key revoked"}.get(status, status)
    return f"{path.name}: '{key}:' commit {commit[:12]} is not validly signed ({reason})"


def main(req_dirs: list, root: Path) -> int:
    codeowners = load_codeowners(root)
    reviewer_fps = load_reviewer_fingerprints(root)
    errors = []
    for req_dir in req_dirs:
        directory = root / req_dir
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.yml")):
            if path.name.startswith("."):
                continue
            err = check_item(path, root, codeowners, reviewer_fps)
            if err:
                errors.append(err)
            else:
                print(f"  OK: {path.name}")
    if errors:
        print("\nSign-off errors:")
        for e in errors:
            print(f"  FAIL {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    root = Path.cwd()
    if "--root" in args:
        i = args.index("--root")
        root = Path(args[i + 1]).resolve()
        del args[i:i + 2]
    dirs = args or DOCUMENTS
    sys.exit(main(dirs, root))
