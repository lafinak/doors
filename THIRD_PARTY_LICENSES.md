# Third-Party Licenses

> Generated from `pip-licenses --with-urls` against `requirements.txt` on 2026-10-21.
> This is a technical reading of the license text, not legal advice. Confirm with
> counsel before relying on it in a client contract.

## Summary

Every direct and transitive dependency is permissively licensed (MIT, BSD-2/3,
Apache-2.0, PSF-2.0, MPL 2.0) **except `doorstop`, which is LGPLv3**. That is the
one dependency that needs a decision, and the decision depends on how this
project is delivered (see "What this means" below).

| Package | Version | License |
|---|---|---|
| doorstop | 3.2 | **GNU LGPLv3** |
| reqif | 0.1.0 | Apache-2.0 |
| lxml | 6.1.3 | BSD-3-Clause |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| referencing | 0.37.0 | MIT |
| rpds-py | 2026.9.1 | MIT |
| PyYAML | 6.0.3 | MIT |
| pytest | 9.1.1 | MIT |
| pluggy | 1.7.0 | MIT |
| iniconfig | 2.3.1 | MIT |
| elementpath | 5.1.4 | MIT |
| xmlschema | 4.3.2 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| certifi | 2026.10.19 | MPL-2.0 |
| charset-normalizer | 3.5.2 | MIT |
| idna | 3.20 | BSD-3-Clause |
| urllib3 | 2.8.0 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| typing_extensions | 4.16.0 | PSF-2.0 |
| six | 1.17.0 | MIT |
| Jinja2, MarkupSafe, Markdown, Pygments | — | BSD/BSD-3 |
| et_xmlfile, openpyxl, python-frontmatter, python-markdown-math, plantuml-markdown, bottle, verchew | — | MIT/BSD (doorstop's own transitive deps, pulled in for its publish feature) |

Full machine-readable detail: run `pip-licenses --format=plain --with-urls --with-description` in the project venv.

## Doorstop's LGPLv3: what this means

Verified against the actual license text shipped with the package (standard,
unmodified GNU LGPLv3 -- the extra "Other/Proprietary License" tag on PyPI's
own classifier list appears to be a packaging artifact, not a second term; no
other license file ships with it).

LGPLv3's copyleft provisions (Section 4, "Combined Works") are triggered by
**conveying** the software -- handing someone a copy -- not by merely running
it. This is the key fork:

- **Pure hosted/managed service** (the client only ever talks to a web UI or
  API; nobody receives a copy of this code): LGPLv3 does not require anything
  extra. LGPLv3 has no AGPL-style network-use clause -- SaaS use alone does not
  convey the software to the end user.
- **Handing over an installable package, repo, or deployable artifact**
  (a one-off migration handoff, or a white-label product installed on the
  client's own infrastructure): this *does* convey the software, so Section 4
  applies. In practice the obligations are mild and already satisfiable:
  - Give notice that Doorstop is used and under LGPLv3 (this file does that).
  - Accompany the delivery with a copy of the LGPLv3 and GPLv3 text (ship this
    file plus `.venv/lib/*/site-packages/doorstop-3.2.dist-info/licenses/LICENSE.md`,
    or just point to it).
  - Don't modify Doorstop's own source. We haven't -- everything in this repo
    calls Doorstop's public API from `tools/` and `scripts/`, never edits
    anything under `site-packages/doorstop/`. As long as that stays true, the
    "provide Minimal Corresponding Source" branch of Section 4(d) doesn't even
    come up -- the "suitable shared library mechanism" branch (4d1) is
    satisfied automatically, because `pip install doorstop==3.2` is already how
    a user would relink a different (modified) version of the Library.

**Bottom line**: this is a non-issue for a managed service, a light paperwork
item (include this file) for a packaged handoff, and only becomes a real
question if Doorstop's own source is ever forked/modified -- which this
project currently does not do. Revisit once `turbo-flow-pkx8` (service shape)
is decided, since the answer differs by shape.

## Not covered here

This only covers Python dependencies pulled in by `requirements.txt`. It does
not cover GitHub Actions used in `.github/workflows/requirements.yml`
(`actions/checkout`, `actions/setup-python`, `actions/upload-artifact`,
`actions/deploy-pages`, all MIT-licensed by GitHub, but not re-verified here),
or `dolt` (Apache-2.0, used only if `tools/sync_to_dolt.py` is exercised, not
re-verified here either).
