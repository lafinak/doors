# Tool Qualification Dossier: Claude Code (DRAFT)

> **Status: DRAFT, not reviewed by a functional-safety assessor.** The classification
> below is an argument, not a certification. Clause and table numbers must be checked
> against the licensed ISO 26262-8:2018 text before this goes to an auditor.

Scope: use of Claude Code to **draft** requirement items (YAML) in this repository.
Out of scope: code generation, test generation, any other use of the tool.

## 1. Tool classification (ISO 26262-8:2018, clause 11)

| Criterion | Value |
|---|---|
| Tool | Claude Code (Anthropic), model version recorded per session |
| Use case | Drafting and quality-checking requirement items stored as Doorstop YAML |
| Tool Impact (TI) | **TI2**: an error in a drafted requirement could, if undetected, enter the safety work products |

TI1 cannot be argued: the tool's output is a work product, not an advisory view.

## 2. Tool error Detection (TD)

The standard's term is *tool error detection* (TD1/TD2/TD3). TD1 means a high degree of
confidence that a tool malfunction or erroneous output will be prevented or detected.

| Detection measure | Where implemented | Independent of the tool? |
|---|---|---|
| Engineer reviews every drafted item before it is merged | PR review, `CLAUDE.md` rule | Yes (human) |
| Visible diff of every change | Git / pull request | Yes |
| Structural checks (links, levels, suspect links) | `tools/validate.py` in CI | Yes (deterministic) |
| Schema checks (ASIL, status, verification method, rationale, "shall" form) | `tools/validate_iso26262.py` in CI | Yes (deterministic) |
| Two approvals required to merge to `main` | Branch protection (**must be enabled; not set by this repo**) | Yes |

**Proposed TD: TD1**, resting mainly on the human review. An assessor must decide whether
this is sufficient for the ASILs in scope, particularly ASIL C/D.

## 3. Resulting TCL

TI2 + TD1 gives **TCL1** (per the TCL determination table in clause 11). At TCL1 the
standard asks for no further tool qualification measures. If the assessor rates TD as
TD2, the result is TCL2 and a qualification method (e.g. increased confidence from use,
or validation of the tool) would be needed.

## 4. Process guarantees (what the repo enforces)

1. `CLAUDE.md` tells the tool to create items only with `status: draft`.
2. Plain `doorstop` auto-reviews new items; this repo uses `tools/validate.py`, which disables that.
3. `tools/validate_iso26262.py` fails any item with `reviewed`/`approved` status that has no Doorstop review stamp.
4. Only a human runs `doorstop review` and changes `status`.
5. Git history gives an audit trail of every change and its author.

Limits: items 1, 4 are instructions and team discipline, not technical locks. Item 3 only
checks that a stamp exists, not who made it. Branch protection and required reviewers must
be configured on the hosting platform.

## 5. Evidence still to collect

- [ ] Sample of at least 10 Claude-drafted requirements with the human review log
- [ ] CI run logs (GitHub Actions) showing both validators passing
- [ ] Branch protection settings screenshot (two approvals on `main`)
- [ ] Record of the model/version used per drafting session
- [ ] Assessor sign-off on the TI/TD/TCL classification
