# doors

Migration path from IBM DOORS to Git-native requirements management with [Doorstop](https://github.com/doorstop-dev/doorstop) and Claude Code. The full plan (in Slovak) is in [DOORS to Git Pipeline — Implementation Guide.md](<DOORS to Git Pipeline — Implementation Guide.md>).

## What is here

| Level | What | Where |
|---|---|---|
| 1 | Doorstop demo: SRD → SWR → TST with traceability | `reqs/`, `CLAUDE.md` |
| 2 | ReqIF (DOORS export) → Doorstop converter and a synthetic export | `tools/reqif_to_doorstop.py`, `tools/make_dummy_reqif.py`, `samples/export.reqif` |
| 3 | CI: validate on every PR, publish HTML report to GitHub Pages | `.github/workflows/requirements.yml` |
| 4 | ISO 26262 schema, validator, TCL1 dossier (draft) | `schemas/`, `tools/validate_iso26262.py`, `docs/tool_qualification/` |

## Quick start

```bash
pip install -r requirements.txt
python tools/validate.py                  # structural validation (read-only)
python tools/validate_iso26262.py         # ISO 26262 schema check
doorstop publish all ./public             # HTML report with traceability matrix
python tools/make_dummy_reqif.py          # regenerate the synthetic DOORS export
python tools/reqif_to_doorstop.py samples/export.reqif SRD   # import into an SRD document
```

## Differences from the guide

These were found by actually running it:

- `doorstop validate` does not exist in Doorstop 3.2; validation is bare `doorstop`.
- Bare `doorstop` **auto-marks never-reviewed items as reviewed** and rewrites files, which defeats the "AI never approves" rule. Use `tools/validate.py` instead (it disables that).
- `reqif.ReqIFBundle.from_file` does not exist; the library uses `reqif.parser.ReqIFParser`.
- Doorstop items have no `uid` field (the UID is the file name), so the converter creates items through the Doorstop API and the ISO schema takes `uid` from the file name.
- The Pages deploy uses GitHub's official `deploy-pages` action (matches "Source: GitHub Actions") rather than `peaceiris/actions-gh-pages`.
- The ISO 26262 term is tool error *detection* (TD), not "TED".

## Setup needed on GitHub

- Settings → Pages → Source: **GitHub Actions**
- Branch protection on `main` with two required approvals (the TCL1 argument relies on it)

## Status

The TCL1 dossier is a **draft** and has not been reviewed by a functional-safety assessor.
