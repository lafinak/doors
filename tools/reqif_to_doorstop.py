"""Convert a ReqIF export (e.g. from IBM DOORS) into Doorstop items.

Usage: python tools/reqif_to_doorstop.py export.reqif SRD
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


def xhtml_to_text(value: str) -> str:
    """Strip XHTML markup. Tables/images are lost (documented in the guide)."""
    value = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", value)
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


def convert(reqif_path: str, prefix: str, root: str = ".") -> list:
    bundle = ReqIFParser.parse(reqif_path)
    content = bundle.core_content.req_if_content
    names = attribute_names(bundle)

    tree = doorstop.build(root=root)
    document = tree.find_document(prefix)

    # SPEC-OBJECT identifier -> Doorstop item, in document (hierarchy) order
    order = [
        h.spec_object
        for spec in content.specifications
        for h in bundle.iterate_specification_hierarchy(spec)
    ]
    objects = {o.identifier: o for o in content.spec_objects}
    created = {}
    for position, ref in enumerate(order, 1):
        obj = objects[ref]
        values = {}
        for attr in obj.attributes:
            name = names.get(attr.definition_ref, attr.definition_ref)
            raw = attr.value_stripped_xhtml or attr.value
            values[name] = xhtml_to_text(raw) if "xhtml" in str(attr.attribute_type).lower() else raw
        number = int(values.get(ID_ATTR) or position)
        item = document.add_item(number=number)
        item.text = values.get(TEXT_ATTR, "")
        item.header = values.get(NAME_ATTR, "")
        for source_name, key in EXTRA_ATTRS.items():
            if source_name in values:
                item.set(key, values[source_name])
        item.set("status", "draft")  # ISO 26262 lifecycle: only a human advances it
        item.reviewed = False  # imported items are drafts; only a human reviews
        created[ref] = item

    for relation in content.spec_relations or []:
        source, target = created.get(relation.source), created.get(relation.target)
        if source and target:
            source.link(target.uid)

    for item in created.values():
        item.save()
    return list(created.values())


if __name__ == "__main__":
    src, pfx = (sys.argv[1], sys.argv[2]) if len(sys.argv) == 3 else ("samples/export.reqif", "SRD")
    for it in convert(src, pfx):
        print(f"Created: {it.uid} - {it.header}")
