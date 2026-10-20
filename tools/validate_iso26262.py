"""Validate SRD item files against schemas/srd_requirement.yml.

Usage: python tools/validate_iso26262.py [reqs/SRD] [schemas/srd_requirement.yml]

Also enforces the process rule that the tool never approves: an item may only
carry `status: approved` if it has a Doorstop review stamp (a human ran review).
"""
import sys
from pathlib import Path

import jsonschema
import yaml


def validate_directory(req_dir: str, schema_path: str) -> bool:
    schema = yaml.safe_load(Path(schema_path).read_text(encoding="utf-8"))
    errors = []
    for path in sorted(Path(req_dir).glob("*.yml")):
        if path.name.startswith("."):
            continue
        item = yaml.safe_load(path.read_text(encoding="utf-8"))
        item["uid"] = path.stem
        item["level"] = str(item.get("level", ""))  # YAML parses 1.0 as float
        try:
            jsonschema.validate(item, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"  FAIL {path.name}: {e.message}")
            continue
        if item["status"] in ("reviewed", "approved") and not item.get("reviewed"):
            errors.append(f"  FAIL {path.name}: status '{item['status']}' without a review stamp")
            continue
        print(f"  OK: {path.name}")
    if errors:
        print("\nValidation errors:")
        print("\n".join(errors))
    return not errors


if __name__ == "__main__":
    req_dir = sys.argv[1] if len(sys.argv) > 1 else "reqs/SRD"
    schema = sys.argv[2] if len(sys.argv) > 2 else "schemas/srd_requirement.yml"
    ok = validate_directory(req_dir, schema)
    sys.exit(0 if ok else 1)
