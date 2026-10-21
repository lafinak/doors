"""Read-only Doorstop validation.

Plain `doorstop` auto-reviews never-reviewed items (settings.REVIEW_NEW_ITEMS)
and rewrites item files. That would silently approve AI-drafted requirements,
so this wrapper turns both off. It also fails on link cycles and self-links,
which Doorstop only reports as log lines. Exit code is non-zero on any error.
"""
import sys

import doorstop
from doorstop import settings

settings.REVIEW_NEW_ITEMS = False
settings.REFORMAT = False


def link_problems(tree) -> list:
    """Self-links and cycles in the item link graph."""
    graph = {str(item.uid): [str(link) for link in item.links] for doc in tree for item in doc}
    problems, state = [], {}

    def visit(uid, path):
        state[uid] = "open"
        for parent in graph.get(uid, []):
            if parent == uid:
                problems.append(f"{uid}: links to itself")
            elif state.get(parent) == "open":
                problems.append(f"cycle: {' -> '.join(path + [uid, parent])}")
            elif parent in graph and parent not in state:
                visit(parent, path + [uid])
        state[uid] = "done"

    for uid in graph:
        if uid not in state:
            visit(uid, [])
    return problems


tree = doorstop.build()
tree.load()
ok = tree.validate()

problems = link_problems(tree)
for problem in problems:
    print(f"ERROR: {problem}")

unreviewed = [str(i.uid) for doc in tree for i in doc if i.active and not i.reviewed]
if unreviewed:
    print(f"{len(unreviewed)} item(s) awaiting human review: {', '.join(unreviewed)}")
sys.exit(0 if ok and not problems else 1)
