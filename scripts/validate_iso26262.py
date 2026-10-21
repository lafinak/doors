"""Validate Doorstop item files against the JSON schemas in schemas/.

Usage:
  python scripts/validate_iso26262.py                       # SRD, SWR and TST
  python scripts/validate_iso26262.py reqs/SRD schemas/srd_requirement.json   # one directory

Fails (exit 1) on schema errors, unreadable files, a missing or empty directory,
a SWR without a link to an SRD or a TST without a link to a SWR (CLAUDE.md rules),
and on `status: reviewed|approved` unless Doorstop confirms the item's review
stamp matches its current content (a forged or stale stamp is rejected).
"""
import json
import sys
from pathlib import Path

import doorstop
import jsonschema
import yaml


def reviewed_by_doorstop(req_dir: Path) -> set:
    """UIDs whose review stamp matches their current content."""
    try:
        tree = doorstop.build(root=str(req_dir.resolve().parent.parent))
        tree.load()
        return {str(item.uid) for doc in tree for item in doc if item.reviewed}
    except Exception as e:  # fail closed: if stamps cannot be verified, none count
        print(f"WARN: cannot verify review stamps ({type(e).__name__}: {e})")
        return set()


# document prefix -> prefix its links must point to
REQUIRED_PARENT = {"SWR": "SRD", "TST": "SWR"}
DOCUMENTS = [("reqs/SRD", "schemas/srd_requirement.json"),
             ("reqs/SWR", "schemas/swr_requirement.json"),
             ("reqs/TST", "schemas/tst_requirement.json")]


def link_uids(item: dict) -> list:
    return [next(iter(link)) if isinstance(link, dict) else str(link) for link in item.get("links") or []]


def validate_directory(req_dir: str, schema_path: str) -> bool:
    directory = Path(req_dir)
    if not directory.is_dir():
        print(f"FAIL: directory not found: {req_dir}")
        return False
    paths = [p for p in sorted(directory.glob("*.yml")) if not p.name.startswith(".")]
    if not paths:
        print(f"FAIL: no requirement files in {req_dir}")
        return False

    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    genuinely_reviewed = None
    errors = []
    for path in paths:
        try:
            item = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError) as e:
            errors.append(f"  FAIL {path.name}: cannot read YAML ({type(e).__name__})")
            continue
        if not isinstance(item, dict):
            errors.append(f"  FAIL {path.name}: not a YAML mapping")
            continue
        item["uid"] = path.stem
        item["level"] = str(item.get("level", ""))  # YAML parses 1.0 as float
        try:
            jsonschema.validate(item, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"  FAIL {path.name}: {e.message}")
            continue
        parent = REQUIRED_PARENT.get(directory.name)
        if parent and not any(uid.startswith(parent) for uid in link_uids(item)):
            errors.append(f"  FAIL {path.name}: must link to at least one {parent} item")
            continue
        if item["status"] in ("reviewed", "approved"):
            if genuinely_reviewed is None:
                genuinely_reviewed = reviewed_by_doorstop(directory)
            if path.stem not in genuinely_reviewed:
                errors.append(f"  FAIL {path.name}: status '{item['status']}' but the review stamp is missing, forged or stale")
                continue
        print(f"  OK: {path.name}")
    if errors:
        print("\nValidation errors:")
        print("\n".join(errors))
    return not errors


if __name__ == "__main__":
    if len(sys.argv) == 3:
        sys.exit(0 if validate_directory(sys.argv[1], sys.argv[2]) else 1)
    if len(sys.argv) != 1:
        sys.exit("usage: validate_iso26262.py [REQ_DIR SCHEMA]")
    results = []
    for req_dir, schema in DOCUMENTS:
        print(f"== {req_dir}")
        results.append(validate_directory(req_dir, schema))
    sys.exit(0 if all(results) else 1)
