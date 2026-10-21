"""Tests for scripts/verify_review_signoff.py using real, ephemeral GPG keys.

Proves the actual claim: an item forged with a correctly-computed doorstop
stamp (see test_hardening.py's forgery test) but committed unsigned, or
signed by a key nobody trusts, is rejected -- while the same item committed
with a trusted reviewer's real signature is accepted. Skips if `gpg` is not
installed.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "verify_review_signoff.py"

pytestmark = pytest.mark.skipif(shutil.which("gpg") is None, reason="gpg not installed")


def run(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


@pytest.fixture(scope="module")
def keys(tmp_path_factory):
    """Two ephemeral keypairs in an isolated keyring: alice (trusted), mallory (not)."""
    gnupghome = tmp_path_factory.mktemp("gnupg")
    gnupghome.chmod(0o700)
    import os
    # GIT_CONFIG_GLOBAL/NOSYSTEM: ignore the developer's own git config. A global
    # `gpg.format=ssh` / `commit.gpgsign=true` would otherwise SSH-sign the "unsigned"
    # commits and stop `-S` from using these throwaway GPG keys.
    env = {**os.environ, "GNUPGHOME": str(gnupghome), "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}

    fingerprints = {}
    for name, email in [("alice", "alice@example.com"), ("mallory", "mallory@example.com")]:
        spec = tmp_path_factory.mktemp(f"spec-{name}") / "keyspec.txt"
        spec.write_text(
            "%no-protection\nKey-Type: eddsa\nKey-Curve: ed25519\n"
            "Subkey-Type: eddsa\nSubkey-Curve: ed25519\n"
            f"Name-Real: {name.title()}\nName-Email: {email}\nExpire-Date: 0\n%commit\n"
        )
        r = run(["gpg", "--batch", "--gen-key", str(spec)], cwd=str(gnupghome), env=env)
        assert r.returncode == 0, r.stderr
        r = run(["gpg", "--list-secret-keys", "--with-colons", email], cwd=str(gnupghome), env=env)
        # the signing SUBkey fingerprint is what `git log --format=%GF` reports
        fpr_lines = [l for l in r.stdout.splitlines() if l.startswith("fpr")]
        fingerprints[name] = {"email": email, "primary_fpr": fpr_lines[0].split(":")[9],
                               "signing_fpr": fpr_lines[1].split(":")[9]}
    return {"env": env, "fingerprints": fingerprints}


GOOD_SRD = {
    "active": True, "derived": False, "normative": True, "ref": "", "links": [],
    "level": "1.0", "header": "Authn", "asil": "B",
    "text": "The system shall authenticate users.\n", "verification_method": "test",
    "rationale": "Because safety needs it.",
}


@pytest.fixture
def repo(tmp_path, keys):
    env = keys["env"]
    run(["git", "init", "-q"], cwd=str(tmp_path), env=env)
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "CODEOWNERS").write_text("/reqs/SRD/  @lafinak\n")
    alice_fpr = keys["fingerprints"]["alice"]["signing_fpr"]
    (tmp_path / "reviewers.yml").write_text(
        yaml.safe_dump({"reviewers": [{"codeowner": "lafinak", "gpg_fingerprints": [alice_fpr]}]})
    )
    r = run(["doorstop", "create", "SRD", "./reqs/SRD"], cwd=str(tmp_path), env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    return tmp_path


def commit_as(repo, who, keys, message="review"):
    env = keys["env"]
    fpr = keys["fingerprints"][who]["signing_fpr"]
    email = keys["fingerprints"][who]["email"]
    run(["git", "config", "user.name", who], cwd=str(repo), env=env)
    run(["git", "config", "user.email", email], cwd=str(repo), env=env)
    run(["git", "config", "user.signingkey", fpr], cwd=str(repo), env=env)
    run(["git", "add", "-A"], cwd=str(repo), env=env)
    return run(["git", "commit", "-S", "-m", message], cwd=str(repo), env=env)


def commit_unsigned(repo, keys, message="review"):
    env = keys["env"]
    run(["git", "config", "user.name", "nobody"], cwd=str(repo), env=env)
    run(["git", "config", "user.email", "nobody@example.com"], cwd=str(repo), env=env)
    run(["git", "add", "-A"], cwd=str(repo), env=env)
    return run(["git", "commit", "-m", message], cwd=str(repo), env=env)


def forged_stamp(repo, item):
    """Same forgery as test_hardening.py: a doorstop-correct hash, never reviewed."""
    import doorstop
    (repo / "reqs" / "SRD" / "SRD001.yml").write_text(yaml.safe_dump({**item, "reviewed": None}))
    run(["git", "-C", str(repo), "add", "-A"], cwd=str(repo))
    tree = doorstop.build(root=str(repo))
    tree.load()
    return tree.find_document("SRD").find_item("SRD001").stamp(links=True).value


def verify(repo, env):
    return run([sys.executable, str(SCRIPT), "--root", str(repo)], cwd=str(repo), env=env)


def test_forged_stamp_committed_unsigned_is_rejected(repo, keys):
    stamp = forged_stamp(repo, GOOD_SRD)
    (repo / "reqs" / "SRD" / "SRD001.yml").write_text(
        yaml.safe_dump({**GOOD_SRD, "status": "approved", "reviewed": stamp})
    )
    assert commit_unsigned(repo, keys).returncode == 0
    r = verify(repo, keys["env"])
    assert r.returncode == 1
    assert "not validly signed" in r.stdout or "unsigned" in r.stdout


def test_forged_stamp_signed_by_untrusted_key_is_rejected(repo, keys):
    stamp = forged_stamp(repo, GOOD_SRD)
    (repo / "reqs" / "SRD" / "SRD001.yml").write_text(
        yaml.safe_dump({**GOOD_SRD, "status": "approved", "reviewed": stamp})
    )
    assert commit_as(repo, "mallory", keys).returncode == 0
    r = verify(repo, keys["env"])
    assert r.returncode == 1
    assert "not a trusted reviewer" in r.stdout


def test_genuinely_signed_by_trusted_reviewer_is_accepted(repo, keys):
    stamp = forged_stamp(repo, GOOD_SRD)  # "forged" in the sense of hand-computed, but this time...
    (repo / "reqs" / "SRD" / "SRD001.yml").write_text(
        yaml.safe_dump({**GOOD_SRD, "status": "approved", "reviewed": stamp})
    )
    assert commit_as(repo, "alice", keys).returncode == 0  # ...alice's real signature backs it
    r = verify(repo, keys["env"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK: SRD001.yml" in r.stdout


def test_no_reviewers_configured_fails_closed(repo, keys):
    (repo / "reviewers.yml").write_text(yaml.safe_dump({"reviewers": []}))
    stamp = forged_stamp(repo, GOOD_SRD)
    (repo / "reqs" / "SRD" / "SRD001.yml").write_text(
        yaml.safe_dump({**GOOD_SRD, "status": "approved", "reviewed": stamp})
    )
    assert commit_as(repo, "alice", keys).returncode == 0
    r = verify(repo, keys["env"])
    assert r.returncode == 1
    assert "no trusted reviewer fingerprint configured" in r.stdout


def test_draft_items_need_no_signature(repo, keys):
    (repo / "reqs" / "SRD" / "SRD001.yml").write_text(yaml.safe_dump({**GOOD_SRD, "status": "draft", "reviewed": None}))
    commit_unsigned(repo, keys, "draft item")
    r = verify(repo, keys["env"])
    assert r.returncode == 0
    assert "OK: SRD001.yml" in r.stdout


def test_unsigned_status_flip_after_a_signed_review_is_rejected(repo, keys):
    """Alice signs the review while the item is still a draft; an unsigned commit then
    flips status to approved. The `reviewed:` line is still alice's, so checking only that
    line would pass -- the `status:` line must be attributable to a trusted signer too."""
    stamp = forged_stamp(repo, GOOD_SRD)
    item_file = repo / "reqs" / "SRD" / "SRD001.yml"
    item_file.write_text(yaml.safe_dump({**GOOD_SRD, "status": "draft", "reviewed": stamp}))
    assert commit_as(repo, "alice", keys, "alice reviews (still draft)").returncode == 0
    assert verify(repo, keys["env"]).returncode == 0  # a draft needs no sign-off

    item_file.write_text(yaml.safe_dump({**GOOD_SRD, "status": "approved", "reviewed": stamp}))
    assert commit_unsigned(repo, keys, "agent flips status").returncode == 0
    r = verify(repo, keys["env"])
    assert r.returncode == 1, r.stdout
    assert "status" in r.stdout


def test_signed_status_flip_by_the_trusted_reviewer_is_accepted(repo, keys):
    stamp = forged_stamp(repo, GOOD_SRD)
    item_file = repo / "reqs" / "SRD" / "SRD001.yml"
    item_file.write_text(yaml.safe_dump({**GOOD_SRD, "status": "draft", "reviewed": stamp}))
    assert commit_as(repo, "alice", keys, "alice reviews").returncode == 0
    item_file.write_text(yaml.safe_dump({**GOOD_SRD, "status": "approved", "reviewed": stamp}))
    assert commit_as(repo, "alice", keys, "alice approves").returncode == 0
    r = verify(repo, keys["env"])
    assert r.returncode == 0, r.stdout + r.stderr
