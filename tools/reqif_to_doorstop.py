"""Convert a ReqIF export (e.g. from IBM DOORS) into Doorstop items.

Usage: python tools/reqif_to_doorstop.py export.reqif SRD

Safe to re-run: each imported item records its ReqIF identifier in `doors_id`,
and objects already imported are skipped (never overwritten). Anything that
cannot be imported is reported on stderr instead of being dropped silently.
"""
import re
import sys
from html import unescape

import doorstop
from reqif.models.reqif_spec_object_type import ReqIFSpecObjectType
from reqif.parser import ReqIFParser

TEXT_ATTR = "ReqIF.Text"
NAME_ATTR = "ReqIF.Name"
ID_ATTR = "ReqIF.ForeignID"
# attribute long-names copied into the Doorstop item as extended attributes
EXTRA_ATTRS = {"ASIL": "asil"}


def warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def xhtml_to_text(value: str) -> str:
    """Strip XHTML markup. Tables/images are lost (documented in the guide)."""
    value = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</tr>", "\n", value)
    value = re.sub(r"</td>|</th>", " | ", value)
    value = re.sub(r"<[^>]+>", "", value)
    return unescape(re.sub(r"[ \t]+", " ", value)).strip()


def attribute_names(bundle) -> dict:
    """definition identifier -> long name, across all spec object types."""
    names = {}
    for spec_type in bundle.core_content.req_if_content.spec_types or []:
        if isinstance(spec_type, ReqIFSpecObjectType):
            for definition in spec_type.attribute_definitions or []:
                names[definition.identifier] = definition.long_name
    return names


def parse_number(raw, fallback: int) -> int:
    """ForeignID as a positive item number; fall back to position if unusable."""
    try:
        number = int(raw)
    except (TypeError, ValueError):
        return fallback
    return number if number > 0 else fallback


def convert(reqif_path: str, prefix: str, root: str = ".") -> list:
    bundle = ReqIFParser.parse(reqif_path)
    content = bundle.core_content.req_if_content
    names = attribute_names(bundle)

    tree = doorstop.build(root=root)
    document = tree.find_document(prefix)

    already = {}
    for item in document:
        item.load()
        if item.get("doors_id"):
            already[item.get("doors_id")] = item

    order = [
        h.spec_object
        for spec in content.specifications
        for h in bundle.iterate_specification_hierarchy(spec)
    ]
    objects = {o.identifier: o for o in content.spec_objects}
    created, imported = {}, []
    for position, ref in enumerate(order, 1):
        obj = objects.get(ref)
        if obj is None:
            warn(f"hierarchy references undefined object '{ref}'; skipped")
            continue
        if ref in already:
            print(f"Skipped (already imported): {already[ref].uid} <- {ref}")
            created[ref] = already[ref]
            continue
        values = {}
        for attr in obj.attributes:
            name = names.get(attr.definition_ref, attr.definition_ref)
            raw = attr.value_stripped_xhtml or attr.value
            values[name] = xhtml_to_text(raw) if "xhtml" in str(attr.attribute_type).lower() else raw
        item = document.add_item(number=parse_number(values.get(ID_ATTR), position))
        item.text = values.get(TEXT_ATTR, "")
        item.header = values.get(NAME_ATTR, "")
        item.set("doors_id", ref)
        for source_name, key in EXTRA_ATTRS.items():
            if source_name in values:
                item.set(key, values[source_name])
        item.set("status", "draft")  # ISO 26262 lifecycle: only a human advances it
        item.reviewed = False  # imported items are drafts; only a human reviews
        created[ref] = item
        imported.append(item)

    for relation in content.spec_relations or []:
        source, target = created.get(relation.source), created.get(relation.target)
        if source is None or target is None:
            warn(f"link {relation.source} -> {relation.target} dropped: object not imported")
        elif source.uid == target.uid:
            warn(f"link {relation.source} -> {relation.target} dropped: self-link")
        else:
            source.link(target.uid)

    for item in created.values():
        item.save()
    return imported


if __name__ == "__main__":
    src, pfx = (sys.argv[1], sys.argv[2]) if len(sys.argv) == 3 else ("samples/export.reqif", "SRD")
    try:
        items = convert(src, pfx)
    except FileNotFoundError:
        sys.exit(f"ERROR: input file not found: {src}")
    except Exception as e:
        if type(e).__module__.startswith("reqif"):
            sys.exit(f"ERROR: not a valid ReqIF file ({src}): {e}")
        raise
    for it in items:
        print(f"Created: {it.uid} - {it.header} <- {it.get('doors_id')}")
