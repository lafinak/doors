"""Validate SRD item files against schemas/srd_requirement.json.

Usage: python scripts/validate_iso26262.py [reqs/SRD] [schemas/srd_requirement.json]

Fails (exit 1) on schema errors, unreadable files, a missing or empty directory,
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
    req_dir = sys.argv[1] if len(sys.argv) > 1 else "reqs/SRD"
    schema = sys.argv[2] if len(sys.argv) > 2 else "schemas/srd_requirement.json"
    sys.exit(0 if validate_directory(req_dir, schema) else 1)
