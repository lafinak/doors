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
| Structural checks (links, levels, suspect links, link cycles, self-links) | `tools/validate.py` in CI | Yes (deterministic) |
| Schema checks for SRD, SWR and TST (ASIL, status, verification method, rationale, "shall" form) | `scripts/validate_iso26262.py` in CI | Yes (deterministic) |
| Traceability rules: every SWR links to an SRD, every TST to a SWR | `scripts/validate_iso26262.py` in CI | Yes (deterministic) |
| `reviewed`/`approved` status only with a review stamp that matches the item's current content | `scripts/validate_iso26262.py` (forged or stale stamps rejected) | Yes (deterministic), but the stamp itself is a public content hash a non-human can reproduce -- see the limits below and the next row |
| `reviewed`/`approved` status additionally requires the commit that set the stamp to carry a GPG signature from a fingerprint a human configured in `reviewers.yml` for that path's code owner | `scripts/verify_review_signoff.py` in CI, via `git blame` | Yes (deterministic check; the trust set is a human-maintained file, not inferred) |
| Regression tests for the tooling itself (about 41 cases, incl. hostile input, forged stamps, and forged-vs-genuine signatures with real ephemeral GPG keys) | `tests/` in CI | Yes (deterministic) |
| Code-owner review for `reqs/`, `schemas/`, `scripts/`, `tools/`, `.github/` | `.github/CODEOWNERS` (**takes effect only when branch protection requires code-owner review; not set by this repo**) | Yes (human) |
| Required approvals to merge to `main` | Branch protection (**must be enabled; not set by this repo**) | Yes |

**Proposed TD: TD1** (written "TED1" in some project notes; the standard's term is TD), resting mainly on the human review: an engineer reviews every diff before it is merged. An assessor must decide whether
this is sufficient for the ASILs in scope, particularly ASIL C/D.

## 3. Resulting TCL

TI2 + TD1 gives **TCL1** (per the TCL determination table in clause 11). At TCL1 the
standard asks for no further tool qualification measures, so no formal qualification of Claude Code is proposed. If the assessor rates TD as
TD2, the result is TCL2 and a qualification method (e.g. increased confidence from use,
or validation of the tool) would be needed.

## 4. Process guarantees (what the repo enforces)

1. `CLAUDE.md` tells the tool to create items only with `status: draft`.
2. Plain `doorstop` auto-reviews new items; this repo uses `tools/validate.py`, which disables that.
3. `scripts/validate_iso26262.py` fails any item with `reviewed`/`approved` status unless Doorstop confirms the review stamp matches the item's current content. A hand-written stamp, or a stamp left stale by a later edit, is rejected.
3a. `scripts/verify_review_signoff.py` additionally fails that item unless the commit that introduced its current stamp carries a GPG signature from a fingerprint listed in `reviewers.yml`, which only a human with the private key can produce -- this is what stops a *correctly computed* stamp (see Limits below) from passing as a genuine review.
4. Only a human runs `doorstop review` and changes `status`.
5. Git history gives an audit trail of every change and its author.
6. The converter records each item's DOORS identifier (`doors_id`), never overwrites an item already imported, and reports links it cannot carry over.

Limits, stated plainly:
- Items 1 and 4 are instructions and team discipline, not technical locks.
- A valid stamp proves the content was not changed after someone ran `doorstop review`. It does **not** prove that person was a human engineer: the stamp is `sha256(uid, text, ref, links, ...)`, a public, secret-free hash anyone able to `import doorstop` can compute without ever running `doorstop review` -- confirmed exploitable, see `tests/test_hardening.py::test_iso_accepts_a_correctly_computed_stamp_without_doorstop_review`. `scripts/verify_review_signoff.py` narrows this to "whoever holds the private key behind a trusted fingerprint in `reviewers.yml`," which a hash computation alone cannot satisfy. It still does not prove a *human specifically* typed the review: a reviewer who configures `git config commit.gpgsign true` in an environment an agent also runs in has handed that guarantee away. Branch protection with required (code-owner) reviewers is the remaining backstop for that case, because merging still needs a GitHub-side approval the signing key alone doesn't grant, and it must be configured on the hosting platform.
- A sole maintainer cannot approve their own pull request, so a "2 approvals" rule needs a second reviewer or an administrator bypass; decide this before relying on the argument.
- Rich text in DOORS (images, nested tables) is flattened on import; images leave a visible `[image: ...]` marker. Check imported items against DOORS before review.

## 5. Evidence still to collect

- [ ] Sample of at least 10 Claude-drafted requirements with the human review log
- [ ] CI run logs (GitHub Actions) showing both validators passing
- [ ] Branch protection settings screenshot (two approvals on `main`)
- [ ] Reviewers' GPG public keys committed under `keys/`, fingerprints recorded in `reviewers.yml`, and at least one CI run showing `verify_review_signoff.py` passing against a genuinely signed review
- [ ] Record of the model/version used per drafting session
- [ ] Assessor sign-off on the TI/TD/TCL classification
