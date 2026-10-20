# doors

Migration path from IBM DOORS to Git-native requirements management with [Doorstop](https://github.com/doorstop-dev/doorstop) and Claude Code. The full plan (in Slovak) is in [DOORS to Git Pipeline — Implementation Guide.md](<DOORS to Git Pipeline — Implementation Guide.md>). Live traceability report: <https://lafinak.github.io/doors/>

## What is here

| Level | What | Where |
|---|---|---|
| 1 | Doorstop demo: SRD → SWR → TST with traceability | `reqs/`, `CLAUDE.md` |
| 2 | ReqIF (DOORS export) → Doorstop converter and a synthetic export | `tools/reqif_to_doorstop.py`, `tools/make_dummy_reqif.py`, `samples/export.reqif` |
| 3 | CI: validate and test on every PR, publish HTML report to GitHub Pages | `.github/workflows/requirements.yml` |
| 4 | ISO 26262 schemas, validator, TCL1 dossier (draft) | `schemas/`, `scripts/validate_iso26262.py`, `docs/tool_qualification/` |
| + | Regression tests (hostile input, forged approvals, scale) | `tests/` |
| + | Optional Dolt (SQL) mirror of the YAML | `tools/dolt_schema.sql`, `tools/sync_to_dolt.py` |

## Quick start

```bash
pip install -r requirements.txt
python tools/validate.py                  # structural validation (read-only)
python scripts/validate_iso26262.py       # schema + traceability rules for SRD, SWR, TST
python -m pytest -q tests                 # regression tests
doorstop publish all ./public             # HTML report with traceability matrix
python tools/make_dummy_reqif.py          # regenerate the synthetic DOORS export
python tools/reqif_to_doorstop.py samples/export.reqif SRD   # import into an SRD document
```

The importer is safe to re-run: every imported item keeps its ReqIF identifier in `doors_id`, items already imported are skipped (never overwritten), and anything it cannot carry over (dangling links, unknown objects) is reported on stderr. Imported items are always `status: draft` and unreviewed, and the ISO validator flags them until an engineer adds `rationale` and `verification_method`.

## What the checks enforce

- Text starts with "The system shall" (SWR also accepts "The software shall"); ASIL, status, header, verification method and rationale are present and valid
- Every SWR links to an SRD, every TST to a SWR
- No link cycles or self-links
- `status: reviewed|approved` only when Doorstop confirms the review stamp matches the item's current content (a hand-written or stale stamp fails)
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

## Known limits

- A valid review stamp shows the content has not changed since `doorstop review` was run, not that a human ran it. Branch protection with required reviewers is what makes review a human decision.
- Images and nested tables in DOORS rich text are flattened on import (images become `[image: name]` markers); check imported items against DOORS.
- Import speed is about 40 ms per requirement.

## Status

The TCL1 dossier is a **draft** and has not been reviewed by a functional-safety assessor.
