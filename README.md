# doors

Migration path from IBM DOORS to Git-native requirements management with [Doorstop](https://github.com/doorstop-dev/doorstop) and Claude Code. The full plan (in Slovak) is in [DOORS to Git Pipeline — Implementation Guide.md](<DOORS to Git Pipeline — Implementation Guide.md>). Live traceability report: <https://lafinak.github.io/doors/>

## What is here

| Level | What | Where |
|---|---|---|
| 1 | Doorstop demo: SRD → SWR → TST with traceability | `reqs/`, `CLAUDE.md` |
| 2 | ReqIF (DOORS export) → Doorstop converter and a synthetic export | `tools/reqif_to_doorstop.py`, `tools/make_dummy_reqif.py`, `samples/export.reqif` |
| 3 | CI: validate and test on every PR, publish HTML report to GitHub Pages | `.github/workflows/requirements.yml` |
| 4 | ISO 26262 schemas, validator, TCL1 dossier (draft) | `schemas/`, `scripts/validate_iso26262.py`, `docs/tool_qualification/` |
| 5 | GPG sign-off: a reviewed/approved item must be attributable to a commit signed by a trusted human, not just a correct content hash | `reviewers.yml`, `keys/`, `scripts/verify_review_signoff.py` |
| + | Regression tests (hostile input, forged approvals, forged signatures, scale) | `tests/` |
| + | Optional Dolt (SQL) mirror of the YAML | `tools/dolt_schema.sql`, `tools/sync_to_dolt.py` |

## Quick start

Use a venv, not `pip install --user`: the test suite and CI run `scripts/validate_iso26262.py`
under `python -I` (isolated mode, as a hardening measure -- see "What the checks enforce").
`-I` excludes `--user` site-packages, so a `--user` install makes `import doorstop` fail only
inside tests/CI while looking fine when you run the scripts directly, which is a confusing way
to debug.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python tools/validate.py                  # structural validation (read-only)
python scripts/validate_iso26262.py       # schema + traceability rules for SRD, SWR, TST
python scripts/verify_review_signoff.py   # GPG sign-off: who actually reviewed it (needs git history + reviewers.yml)
python -m pytest -q tests                 # regression tests
doorstop publish all ./public             # HTML report with traceability matrix
python tools/make_dummy_reqif.py          # regenerate the synthetic DOORS export
python tools/reqif_to_doorstop.py samples/export.reqif SRD   # import into an SRD document
```

The importer is safe to re-run: every imported item keeps its ReqIF identifier in `doors_id`, items already imported are skipped (never overwritten), and anything it cannot carry over (dangling links, unknown objects, or a source attribute not listed in `EXTRA_ATTRS`) is reported on stderr. Imported items are always `status: draft` and unreviewed, and the ISO validator flags them until an engineer adds `rationale` and `verification_method`.

## What the checks enforce

- Text starts with "The system shall" (SWR also accepts "The software shall"); ASIL, status, header, verification method and rationale are present and valid
- Every SWR links to an SRD, every TST to a SWR
- No link cycles or self-links
- `status: reviewed|approved` only when Doorstop confirms the review stamp matches the item's current content (a hand-written or stale stamp fails)
- `status: reviewed|approved` additionally only when `scripts/verify_review_signoff.py` finds, via `git blame`, that the commit which introduced the item's current `reviewed:` line carries a GPG signature from a fingerprint listed in `reviewers.yml` for a CODEOWNERS path owner -- this is the part that specifically can't be forged by computing the content hash yourself, since it needs a private key you don't hold (see "Known limits" for what it still doesn't prove)
- Nothing in the tooling approves anything: `tools/validate.py` never writes files

## Differences from the guide

These were found by actually running it:

- `doorstop validate` does not exist in Doorstop 3.2; validation is bare `doorstop`.
- Bare `doorstop` **auto-marks never-reviewed items as reviewed** and rewrites files, which defeats the "AI never approves" rule. Use `tools/validate.py` instead (it disables that).
- `reqif.ReqIFBundle.from_file` does not exist; the library uses `reqif.parser.ReqIFParser`.
- Doorstop items have no `uid` field (the UID is the file name), so the converter creates items through the Doorstop API and the ISO schemas take `uid` from the file name.
- The Pages deploy uses GitHub's official `deploy-pages` action (matches "Source: GitHub Actions") rather than `peaceiris/actions-gh-pages`.
- The ISO 26262 term is tool error *detection* (TD), not "TED".

## Setup needed on GitHub

- Settings → Pages → Source: **GitHub Actions**, and add `main` under Settings → Environments → `github-pages` → Deployment branches
- Branch protection on `main`: required approvals **and "Require review from Code Owners"** (see `.github/CODEOWNERS`). A sole maintainer cannot approve their own PR, so add a second reviewer or allow administrator bypass.
- GPG sign-off: each reviewer runs `gpg --gen-key` (or reuses an existing key), exports the public key with `gpg --export --armor <key-id> > keys/<name>.asc` and commits it, then adds the *signing subkey* fingerprint (the one `git log --format=%GF` reports for a signed commit of theirs, not necessarily the primary key fingerprint) to `reviewers.yml` under their CODEOWNERS username. Reviewers then commit with `git commit -S` (or `git config commit.gpgsign true`) when flipping an item's `status` to `reviewed`/`approved`. Until a reviewer has a fingerprint in `reviewers.yml`, every reviewed/approved item under their path fails closed in CI.

## Known limits

- A valid review stamp shows the content has not changed since `doorstop review` was run, not that a human ran it -- `scripts/verify_review_signoff.py` closes most of this gap by requiring a GPG signature from a trusted key, which can't be produced just by knowing the (public, secret-free) hash algorithm. It still doesn't prove a human, specifically, typed the review: a reviewer who lets an agent run with their signing key configured (`git config commit.gpgsign true` in an environment the agent controls) has handed that guarantee away. Branch protection with required human PR approval is the backstop for that case, because merging still needs a GitHub-side click the signing key alone doesn't grant.
- Images and nested tables in DOORS rich text are flattened on import (images become `[image: name]` markers, hyperlinks become `[text](href)`, merged header cells are padded so column counts stay consistent); check imported items against DOORS.
- A SPEC-RELATION's type (e.g. "Satisfies" vs. "Verifies") is not preserved: Doorstop links carry no type field, so distinct link kinds are all flattened to one plain parent/child link. The importer warns on stderr when the source distinguishes more than one type, but does not invent a schema field to hold it -- revisit if a client's review process depends on that distinction.
- Import speed is about 40 ms per requirement.

## Status

The TCL1 dossier is a **draft** and has not been reviewed by a functional-safety assessor.
