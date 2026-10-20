"""Read-only Doorstop validation.

Plain `doorstop` auto-reviews never-reviewed items (settings.REVIEW_NEW_ITEMS)
and rewrites item files. That would silently approve AI-drafted requirements,
so this wrapper turns both off. Exit code is non-zero on any validation error.
"""
import sys

import doorstop
from doorstop import settings

settings.REVIEW_NEW_ITEMS = False
settings.REFORMAT = False

tree = doorstop.build()
tree.load()
ok = tree.validate()

unreviewed = [str(i.uid) for doc in tree for i in doc if i.active and not i.reviewed]
if unreviewed:
    print(f"{len(unreviewed)} item(s) awaiting human review: {', '.join(unreviewed)}")
sys.exit(0 if ok else 1)
