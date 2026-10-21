"""Mirror Doorstop YAML items (reqs/) into the Dolt database (dolt_reqs/).

Usage: python tools/sync_to_dolt.py [reqs_dir] [dolt_dir]

YAML stays the source of truth; this rewrites the Dolt tables from it. It does
NOT commit: the engineer reviews `dolt diff` and commits.
"""
import subprocess
import sys
from pathlib import Path

import yaml

COLUMNS = ["uid", "type", "level", "text", "asil", "status", "header", "rationale", "verification_method"]


def q(value) -> str:
    if value is None or value == "":
        return "NULL"
    escaped = str(value).strip().replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def load(reqs_dir: Path):
    rows, links = [], []
    for prefix in ("SRD", "SWR", "TST"):
        for path in sorted((reqs_dir / prefix).glob("*.yml")):
            if path.name.startswith("."):
                continue
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            rows.append({
                "uid": path.stem, "type": prefix, "level": data.get("level"),
                "text": data.get("text"), "asil": data.get("asil"),
                "status": data.get("status") or "draft", "header": data.get("header"),
                "rationale": data.get("rationale"), "verification_method": data.get("verification_method"),
                "reviewed": data.get("reviewed"),
            })
            for link in data.get("links") or []:
                links.append((path.stem, next(iter(link))))
    return rows, links


def main(reqs_dir="reqs", dolt_dir="dolt_reqs"):
    rows, links = load(Path(reqs_dir))
    for r in rows:
        if r["status"] in ("reviewed", "approved") and not r.get("reviewed"):
            sys.exit(f"ERROR: {r['uid']} has status '{r['status']}' but no review stamp; nothing synced")
    # One transaction: if any statement fails, the tables keep their old contents.
    sql = ["START TRANSACTION;", "DELETE FROM links;", "DELETE FROM requirements;"]
    for r in rows:
        values = ", ".join(q(r[c]) for c in COLUMNS)  # r also carries `reviewed`, not stored
        sql.append(f"INSERT INTO requirements ({', '.join(COLUMNS)}) VALUES ({values});")
    for child, parent in links:
        sql.append(f"INSERT INTO links (child_uid, parent_uid) VALUES ({q(child)}, {q(parent)});")
    sql.append("COMMIT;")
    subprocess.run(["dolt", "sql"], input="\n".join(sql), text=True, cwd=dolt_dir, check=True)
    print(f"Synced {len(rows)} requirements and {len(links)} links (uncommitted; review with `dolt diff`)")


if __name__ == "__main__":
    main(*sys.argv[1:3])
