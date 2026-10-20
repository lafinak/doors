# Requirements Management Guidelines

You are a requirements-engineering assistant. For every new requirement:
1. Create the YAML item in the correct directory (`doorstop add <PREFIX>`, then edit the text)
2. UIDs are assigned by Doorstop and must be unique and sequential
3. Text must have the form "The system shall..."
4. Every SWR must link to at least one SRD
5. Every TST must link to at least one SWR

NEVER approve a requirement yourself. Always wait for human review.

## Commands
- Validate: `python tools/validate.py` (read-only). Do NOT run bare `doorstop`: in v3.2 it auto-marks never-reviewed items as reviewed and rewrites files. There is no `doorstop validate` subcommand.
- Publish HTML: `doorstop publish all ./public`
- Convert ReqIF: `python tools/reqif_to_doorstop.py samples/export.reqif SRD`
- Never run `doorstop review`; that is a human decision
