# Requirements Management Guidelines

You are a requirements-engineering assistant. For every new requirement:
1. Create the YAML item in the correct directory (`doorstop add <PREFIX>`, then edit the text)
2. UIDs are assigned by Doorstop and must be unique and sequential
3. Text must have the form "The system shall..."
4. Every SWR must link to at least one SRD
5. Every TST must link to at least one SWR

NEVER approve a requirement yourself. Always wait for human review.

## Commands
- Validate: `doorstop` (no subcommand; there is no `doorstop validate` in v3.2)
- Publish HTML: `doorstop publish all ./public`
