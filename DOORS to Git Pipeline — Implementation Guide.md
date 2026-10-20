# DOORS to Git Pipeline — Implementation Guide

Oct 20, 2026 · @sepric eye

Komplexný implementačný plán pre migráciu z IBM DOORS na Git-natívny requirements management stack s Claude Code.

## Level 1 — Základné demo

**Čas:** 2–3 hodiny | **Cieľ:** Ukázať že stack funguje end-to-end

### Repo štruktúra

```
reqs/
  .doorstop.yml          ← konfigurácia dokumentu
  SRD/                   ← System Requirements
    SRD001.yml
    SRD002.yml
    SRD003.yml
  SWR/                   ← Software Requirements
    SWR001.yml
    SWR002.yml
  TST/                   ← Test Cases
    TST001.yml
public/                  ← generovaný HTML report
CLAUDE.md                ← inštrukcie pre Claude Code
```

### Formát requirement súboru

```yaml
# reqs/SRD/SRD001.yml
uid: SRD001
level: 1.0
text: |
  The system shall authenticate users before granting access
  to any protected resource.
links: []
ref: ''
header: User Authentication
```

### CLAUDE.md — inštrukcie pre Claude Code

```markdown
# Requirements Management Guidelines

Ty si requirements engineer asistent. Pri každom novom requirement:
1. Vytvor YAML súbor v správnom adresári
2. UID musí byť unikátne a sekvenčné
3. Text musí byť v tvare "The system shall..."
4. Každý SWR musí linkovať na aspoň jeden SRD
5. Každý TST musí linkovať na aspoň jeden SWR

NIKDY neschvaľuj requirement sám — vždy počkaj na ľudský review.
```

### Príkazy

```bash
pip install doorstop
doorstop create SRD ./reqs/SRD
doorstop create SWR ./reqs/SWR --parent SRD
doorstop create TST ./reqs/TST --parent SWR
doorstop validate
doorstop publish all ./public
```

### Výsledok

HTML report v `./public` s kompletnou traceability matricou. Otvoriteľný v prehliadači, zdieľateľný cez GitHub Pages.

## Level 2 — ReqIF Pipeline

**Čas:** 1 deň | **Cieľ:** Realistìký import z DOORS cez ReqIF

### Instalácia

```bash
pip install reqif doorstop
```

### Konvertor `reqif_to_doorstop.py`

```python
import reqif
import yaml
import os
from pathlib import Path

def convert_reqif_to_doorstop(reqif_path: str, output_dir: str):
    """Konvertuje ReqIF export z DOORS do Doorstop YAML súborov."""
    bundle = reqif.ReqIFBundle.from_file(reqif_path)
    os.makedirs(output_dir, exist_ok=True)
    
    for spec in bundle.core_content.req_if_content.specifications:
        for i, req in enumerate(spec.children, 1):
            uid = req.identifier or f"REQ{i:03d}"
            text = req.get_value("ReqIF.Text") or ""
            
            data = {
                "uid": uid,
                "level": f"{i}.0",
                "text": text.strip(),
                "links": [],
                "header": req.get_value("ReqIF.Name") or ""
            }
            
            out_path = Path(output_dir) / f"{uid}.yml"
            with open(out_path, "w") as f:
                yaml.dump(data, f, allow_unicode=True, 
                         default_flow_style=False)
            print(f"Created: {out_path}")

if __name__ == "__main__":
    convert_reqif_to_doorstop("export.reqif", "./reqs/SRD")
```

### Dummy `.reqif` súbor na testovanie

Ak nemáš reálny DOORS export, vytvor `export.reqif` manuálne alebo poži Claude Code:

```
Claude, vytvor dummy export.reqif súbor s 5 systémovými požiadavkami
na autentifikáciu používateľov. Použi validý ReqIF XML formát.
```

### Workflow

```bash
# 1. Export z DOORS (alebo použij dummy)
python reqif_to_doorstop.py export.reqif ./reqs/SRD

# 2. Validuj že všetko skončilo správne
doorstop validate

# 3. Claude zkontrolvuje quality
# claude "Skontroluj requirements v reqs/SRD/ — sú v tvare 'The system shall'?
#         Chýbajú nejaké linky? Má každý requirement hlavičku?"

# 4. Publikuj
doorstop publish all ./public
```

### Čo sa môže stratiť pri konverzii

- Bohaté formátovanie (tabeléky, obrázky v texte)
- Custom atribúty ktoré nie sú v ReqIF štandarde
- History zmien (Git bude nová história od nuly)
- Prílohy a linky na externé dokumenty

## Level 3 — CI/CD Pipeline

**Čas:** 2–4 hodiny | **Cieľ:** Automatická validácia na každý PR

### Sruktúra súborov

```
.github/
  workflows/
    requirements.yml    ← hlavný workflow
public/                 ← generované HTML
reqs/
```

### `.github/workflows/requirements.yml`

```yaml
name: Requirements Validation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
    paths:
      - 'reqs/**'
      - 'reqif_to_doorstop.py'

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Doorstop
        run: pip install doorstop

      - name: Validate requirements
        run: doorstop validate

      - name: Publish HTML docs
        run: doorstop publish all ./public

      - name: Upload HTML artifacts
        uses: actions/upload-artifact@v4
        with:
          name: requirements-docs
          path: public/

  publish:
    needs: validate
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    permissions:
      contents: write
      pages: write
      id-token: write
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Build docs
        run: |
          pip install doorstop
          doorstop publish all ./public

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
```

### Aktivová GitHub Pages

```bash
# 1. V GitHub repo ideš do Settings → Pages
# 2. Source: "GitHub Actions"
# 3. Po prvom merge do main bude docs na:
#    https://<org>.github.io/<repo>/
```

### PR workflow pre tím

```
dev branč           PR review          main
    │                    │               │
    ├─ Claude navrhne YAML
    ├─ Človek skontroluje
    ├─ git commit + push
                         │
                         ├─ CI: doorstop validate
                         ├─ CI: build HTML
                         ├─ Review: čudsé oči na req
                                         │
                                         └─ merge → Pages
```

### Testovanie lokálne pred pushom

```bash
# Vždy pred git push
doorstop validate && echo "OK" || echo "FAIL"

# Generuj HTML na náhľad
doorstop publish all ./public
python -m http.server 8000 -d ./public
# Otvor http://localhost:8000
```

## Level 4 — Rivet + ISO 26262 + TCL1 Dossier

**Čas:** 1–2 dni | **Cieľ:** Argument pre auditátora že Claude Code nepotrebuje formálnu kvalifikáciu

> ⚠️ **Rivet je research-stage** (2 stars, 0 forks k októbru 2026). Level 4 ti dáva ISO schemy a TCL1 argumentáciu, ktorú môžeš prezentovať auditorovi bez ohľadu na to či Rivet použiješ alebo nie.

---

### 4.1 ISO 26262 YAML schéma pre requirement

Ulož ako `schemas/srd_requirement.yml`:

```yaml
# ISO 26262-compliant requirement schema
# Ref: ISO 26262-8:2018 Clause 6 (Software requirements specification)
$schema: "https://json-schema.org/draft/2020-12/schema"
title: SRD Requirement
type: object

required:
  - uid
  - level  
  - text
  - asil           # ASIL level povinny!
  - status
  - header

properties:
  uid:
    type: string
    pattern: "^[A-Z]{3}[0-9]{3}$"
    description: "Unique identifier, e.g. SRD001"
  
  level:
    type: string
    pattern: "^[0-9]+\\.[0-9]+$"
  
  text:
    type: string
    pattern: "^The system shall.*"   # EARS / IEEE 830 form
    minLength: 20
  
  asil:
    type: string
    enum: ["QM", "A", "B", "C", "D"]
    description: "Automotive Safety Integrity Level"
  
  status:
    type: string
    enum: ["draft", "reviewed", "approved", "obsolete"]
    default: "draft"
  
  header:
    type: string
    minLength: 3
  
  links:
    type: array
    items:
      type: object
      required: [uid]
      properties:
        uid:
          type: string
  
  rationale:
    type: string
    description: "Preco tento req existuje"
  
  verification_method:
    type: string
    enum: ["test", "analysis", "inspection", "demonstration"]
```

### 4.2 Validator script `validate_iso26262.py`

```python
import yaml
import jsonschema
import sys
from pathlib import Path

def load_schema(schema_path: str) -> dict:
    with open(schema_path) as f:
        return yaml.safe_load(f)

def validate_directory(req_dir: str, schema_path: str) -> bool:
    schema = load_schema(schema_path)
    errors = []
    
    for yml_file in Path(req_dir).glob("*.yml"):
        if yml_file.name.startswith('.'):
            continue
        with open(yml_file) as f:
            req = yaml.safe_load(f)
        try:
            jsonschema.validate(req, schema)
            print(f"  OK: {yml_file.name}")
        except jsonschema.ValidationError as e:
            errors.append(f"  FAIL {yml_file.name}: {e.message}")
    
    if errors:
        print("\nValidation errors:")
        for err in errors:
            print(err)
        return False
    return True

if __name__ == "__main__":
    ok = validate_directory("./reqs/SRD", "./schemas/srd_requirement.yml")
    sys.exit(0 if ok else 1)
```

### 4.3 CLAUDE.md rozshirenie pre ISO 26262

Pridaj do existujúdeho `CLAUDE.md`:

```markdown
## ISO 26262 pravidlá

Každý SRD requirement MUSÍ obsahovať:
- `asil`: QM / A / B / C / D
- `status`: začne ako `draft`, len človek mäní na `reviewed` a `approved`
- `verification_method`: test / analysis / inspection / demonstration
- `rationale`: preco tento requirement existuje

NIKDY nenastavuj `status: approved` — to je výlučne rozhodnutie človeka.
NIKDY nemeň ASIL bez explicitného pokynú od inžyniera.
```

### 4.4 TCL1 Dossier (pre auditátora)

Ulož ako `docs/tool_qualification/tcl1_argument.md`:

```markdown
# Tool Qualification Dossier — Claude Code
## Argument pre TCL1 (bez formálnej kvalifikácie)

**ISO 26262-8:2018, Clause 11 — Tool qualification**

### 1. Tool Classification

| Kritérium | Hodnota | Zdroj |
|-----------|---------|-------|
| Názov nástroja | Claude Code (Anthropic) | - |
| Verzia | sonnet-4-6 alebo novší | Anthropic API |
| Použitie | Generovanie YAML requirements, revievw súborov | - |
| Tool Impact (TI) | **TI2** | Chyba môže prejsť do produktu |

### 2. Tool Error Detection (TED)

| Vrstva detekcie | Implementácia | Silu |
|-----------------|---------------|------|
| **Prímy ľudský review** | Každý YAML reviewuje inždyńer pred commitom | ✅ Primárna |
| Git diff na PR | Zmeny sú viditelné včloveku | ✅ |
| doorstop validate v CI | Automatická štruktúralna kontrola | ✅ |
| JSON Schema validácia | validate_iso26262.py | ✅ |
| 4-eyes principle | 2 aprovály na merge do main | ✅ |

**Záver TED: TED1** — nezávislé metódy detekcie na úrovni inžinierskeho procesu

### 3. Tool Confidence Level

```

TCL = f(TI, TED) TI2 + TED1 → TCL1

```

**TCL1: Nie je potrebná žiadna formálna tool qualification.**
(ISO 26262-8 Table 4)

### 4. Procesné záruky

1. Claude Code generuje len `status: draft` requirements
2. Inždyňer review + manuálne mení na `reviewed`
3. Safety manager aprovál mení na `approved`
4. Git história je plne auditovateľná
5. CLAUDE.md výslovne zakažuje auto-aprovál

### 5. Prílohy

- [ ] Vzorka 10 Claude-generovaných requirements + human review log
- [ ] CI pipeline výsledky (GitHub Actions logy)
- [ ] CLAUDE.md (procesné obmedzenia)
- [ ] validate_iso26262.py výsledky
```

---

### 4.5 Finálny príkáz pre Claude Code

Po nastavení všetkých 4 levelov pošli toto Claude Code:

```
Smeš na bezpečnostný requirements management systém.
Prečítaj CLAUDE.md, potom:

1. Nainstaluj: pip install doorstop reqif jsonschema
2. Inicializuj doorstop dokumenty (ak nie sú)
3. Spusti doorstop validate
4. Spusti python validate_iso26262.py
5. Reportuj všetky chyby

NIKDY neschvaľuj requirements automaticky.
Vždy potvrd môj review pred každým commitom.
```
