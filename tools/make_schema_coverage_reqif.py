"""Generate a small, structurally-diverse synthetic ReqIF export targeting
everything about real DOORS exports not already covered by samples/export.reqif
or samples/export_enterprise.reqif. Kept tiny (8 spec objects) on purpose --
this is about hitting every remaining schema/structure shape once, not volume.

Covers:
- GUID-style object identifiers, as real DOORS exports use (not friendly
  "so-REQ-1" labels)
- A REAL (float) attribute
- A multi-valued ENUMERATION attribute (more than one ENUM-VALUE-REF selected)
- An attribute defined on the SPEC-OBJECT-TYPE but missing on one instance
  (sparse/optional attribute -- DOORS allows a column to be blank per row)
- Two distinct SPEC-RELATION-TYPEs ("Satisfies", "Derives"), to check whether
  link semantics survive the import or get silently flattened to one kind
- A direct self-link in the source file (source == target), to confirm the
  importer-level drop (tools/reqif_to_doorstop.py already warns on this) is
  actually exercised by a generated file, not just reasoned about
- Two separate top-level SPECIFICATIONs (real multi-module DOORS projects,
  not just folders within one module)
- Rich text: an ordered list, a table with a merged cell (colspan), and a
  hyperlink (<a href>) -- xhtml_to_text has no special case for <a>, so this
  checks whether the link target survives or just the visible text does
"""
import sys
from xml.sax.saxutils import escape

GUID = {
    "A": "_8f14e45f-ceea-467e-9b9c-0f2f1f47ec3a",
    "B": "_9bb58f26-903a-4b49-8a1d-71c4a5d0d2a9",
    "C": "_6c5e3f4a-1b2c-4d8e-9f0a-2b3c4d5e6f7a",
    "D": "_1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
}


def spec_object(uid, n, name, text_xhtml, priority_refs, score=None):
    score_xml = (
        f'<ATTRIBUTE-VALUE-REAL THE-VALUE="{score}"><DEFINITION><ATTRIBUTE-DEFINITION-REAL-REF>ad-score</ATTRIBUTE-DEFINITION-REAL-REF></DEFINITION></ATTRIBUTE-VALUE-REAL>'
        if score is not None else ""  # sparse: omitted entirely for one item
    )
    refs = "".join(f"<ENUM-VALUE-REF>{r}</ENUM-VALUE-REF>" for r in priority_refs)
    return f"""    <SPEC-OBJECT IDENTIFIER="{uid}" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPEC-OBJECT-TYPE-REF>sot-req</SPEC-OBJECT-TYPE-REF></TYPE>
      <VALUES>
        <ATTRIBUTE-VALUE-INTEGER THE-VALUE="{n}"><DEFINITION><ATTRIBUTE-DEFINITION-INTEGER-REF>ad-foreignid</ATTRIBUTE-DEFINITION-INTEGER-REF></DEFINITION></ATTRIBUTE-VALUE-INTEGER>
        <ATTRIBUTE-VALUE-STRING THE-VALUE="{escape(name)}"><DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>ad-name</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION></ATTRIBUTE-VALUE-STRING>
        <ATTRIBUTE-VALUE-XHTML><DEFINITION><ATTRIBUTE-DEFINITION-XHTML-REF>ad-text</ATTRIBUTE-DEFINITION-XHTML-REF></DEFINITION><THE-VALUE><xhtml:div>{text_xhtml}</xhtml:div></THE-VALUE></ATTRIBUTE-VALUE-XHTML>
        <ATTRIBUTE-VALUE-ENUMERATION><DEFINITION><ATTRIBUTE-DEFINITION-ENUMERATION-REF>ad-category</ATTRIBUTE-DEFINITION-ENUMERATION-REF></DEFINITION><VALUES>{refs}</VALUES></ATTRIBUTE-VALUE-ENUMERATION>
        {score_xml}
      </VALUES>
    </SPEC-OBJECT>"""


OBJS = [
    spec_object(GUID["A"], 1, "Rendering Score",
                "The system shall render a weighted score. See steps below:"
                '<xhtml:ol><xhtml:li>collect inputs</xhtml:li><xhtml:li>weight them</xhtml:li></xhtml:ol>'
                '<xhtml:table><xhtml:tr><xhtml:td colspan="2">Summary (merged)</xhtml:td></xhtml:tr>'
                '<xhtml:tr><xhtml:td>Weight</xhtml:td><xhtml:td>0.8</xhtml:td></xhtml:tr></xhtml:table>'
                'See also <xhtml:a href="https://example.com/spec#sec-3">external spec section 3</xhtml:a>.',
                ["ev-safety", "ev-perf"], score=0.875),
    spec_object(GUID["B"], 2, "Sparse Attribute Case",
                "The system shall still import correctly when a defined attribute has no value on this particular item.",
                ["ev-safety"], score=None),
]
RELATIONS = [
    ("sr-1", GUID["A"], GUID["B"], "srt-satisfies"),
    ("sr-2", GUID["B"], GUID["A"], "srt-derives"),
    ("sr-3", GUID["A"], GUID["A"], "srt-satisfies"),  # direct self-link in the source file
]


def build() -> str:
    rels = "\n".join(f"""    <SPEC-RELATION IDENTIFIER="{rid}" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPEC-RELATION-TYPE-REF>{rtype}</SPEC-RELATION-TYPE-REF></TYPE>
      <SOURCE><SPEC-OBJECT-REF>{s}</SPEC-OBJECT-REF></SOURCE>
      <TARGET><SPEC-OBJECT-REF>{t}</SPEC-OBJECT-REF></TARGET>
    </SPEC-RELATION>""" for rid, s, t, rtype in RELATIONS)

    hier = "\n".join(f"""        <SPEC-HIERARCHY IDENTIFIER="sh-{i}" LAST-CHANGE="2026-10-20T10:00:00Z"><OBJECT><SPEC-OBJECT-REF>{GUID[k]}</SPEC-OBJECT-REF></OBJECT></SPEC-HIERARCHY>"""
                      for i, k in enumerate(["A", "B"], 1))

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <THE-HEADER><REQ-IF-HEADER IDENTIFIER="header-1">
    <CREATION-TIME>2026-10-20T10:00:00Z</CREATION-TIME>
    <REQ-IF-TOOL-ID>synthetic-doors-export-schema-coverage</REQ-IF-TOOL-ID>
    <REQ-IF-VERSION>1.0</REQ-IF-VERSION>
    <SOURCE-TOOL-ID>synthetic-doors-export-schema-coverage</SOURCE-TOOL-ID>
    <TITLE>Synthetic Schema-Coverage DOORS Export</TITLE>
  </REQ-IF-HEADER></THE-HEADER>
  <CORE-CONTENT><REQ-IF-CONTENT>
  <DATATYPES>
    <DATATYPE-DEFINITION-INTEGER IDENTIFIER="dt-int" LAST-CHANGE="2026-10-20T10:00:00Z" MAX="2147483647" MIN="0"/>
    <DATATYPE-DEFINITION-STRING IDENTIFIER="dt-str" LAST-CHANGE="2026-10-20T10:00:00Z" MAX-LENGTH="255"/>
    <DATATYPE-DEFINITION-XHTML IDENTIFIER="dt-xhtml" LAST-CHANGE="2026-10-20T10:00:00Z"/>
    <DATATYPE-DEFINITION-REAL IDENTIFIER="dt-real" LAST-CHANGE="2026-10-20T10:00:00Z"/>
    <DATATYPE-DEFINITION-ENUMERATION IDENTIFIER="dt-category" LONG-NAME="Category" LAST-CHANGE="2026-10-20T10:00:00Z">
      <SPECIFIED-VALUES>
        <ENUM-VALUE IDENTIFIER="ev-safety" LONG-NAME="Safety" LAST-CHANGE="2026-10-20T10:00:00Z"><PROPERTIES><EMBEDDED-VALUE KEY="0" OTHER-CONTENT=""/></PROPERTIES></ENUM-VALUE>
        <ENUM-VALUE IDENTIFIER="ev-perf" LONG-NAME="Performance" LAST-CHANGE="2026-10-20T10:00:00Z"><PROPERTIES><EMBEDDED-VALUE KEY="1" OTHER-CONTENT=""/></PROPERTIES></ENUM-VALUE>
      </SPECIFIED-VALUES>
    </DATATYPE-DEFINITION-ENUMERATION>
  </DATATYPES>
  <SPEC-TYPES>
    <SPEC-OBJECT-TYPE IDENTIFIER="sot-req" LONG-NAME="Requirement" LAST-CHANGE="2026-10-20T10:00:00Z">
      <SPEC-ATTRIBUTES>
        <ATTRIBUTE-DEFINITION-INTEGER IDENTIFIER="ad-foreignid" LONG-NAME="ReqIF.ForeignID" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-INTEGER-REF>dt-int</DATATYPE-DEFINITION-INTEGER-REF></TYPE></ATTRIBUTE-DEFINITION-INTEGER>
        <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ad-name" LONG-NAME="ReqIF.Name" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-STRING-REF>dt-str</DATATYPE-DEFINITION-STRING-REF></TYPE></ATTRIBUTE-DEFINITION-STRING>
        <ATTRIBUTE-DEFINITION-XHTML IDENTIFIER="ad-text" LONG-NAME="ReqIF.Text" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-XHTML-REF>dt-xhtml</DATATYPE-DEFINITION-XHTML-REF></TYPE></ATTRIBUTE-DEFINITION-XHTML>
        <ATTRIBUTE-DEFINITION-ENUMERATION IDENTIFIER="ad-category" LONG-NAME="Category" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-ENUMERATION-REF>dt-category</DATATYPE-DEFINITION-ENUMERATION-REF></TYPE></ATTRIBUTE-DEFINITION-ENUMERATION>
        <ATTRIBUTE-DEFINITION-REAL IDENTIFIER="ad-score" LONG-NAME="Score" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-REAL-REF>dt-real</DATATYPE-DEFINITION-REAL-REF></TYPE></ATTRIBUTE-DEFINITION-REAL>
      </SPEC-ATTRIBUTES>
    </SPEC-OBJECT-TYPE>
    <SPEC-RELATION-TYPE IDENTIFIER="srt-satisfies" LONG-NAME="Satisfies" LAST-CHANGE="2026-10-20T10:00:00Z"/>
    <SPEC-RELATION-TYPE IDENTIFIER="srt-derives" LONG-NAME="Derives" LAST-CHANGE="2026-10-20T10:00:00Z"/>
    <SPECIFICATION-TYPE IDENTIFIER="st-module" LONG-NAME="Module" LAST-CHANGE="2026-10-20T10:00:00Z"/>
  </SPEC-TYPES>
  <SPEC-OBJECTS>
{chr(10).join(OBJS)}
  </SPEC-OBJECTS>
  <SPEC-RELATIONS>
{rels}
  </SPEC-RELATIONS>
  <SPECIFICATIONS>
    <SPECIFICATION IDENTIFIER="spec-module-1" LONG-NAME="Module One" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPECIFICATION-TYPE-REF>st-module</SPECIFICATION-TYPE-REF></TYPE>
      <CHILDREN>
{hier}
      </CHILDREN>
    </SPECIFICATION>
    <SPECIFICATION IDENTIFIER="spec-module-2" LONG-NAME="Module Two (empty)" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPECIFICATION-TYPE-REF>st-module</SPECIFICATION-TYPE-REF></TYPE>
      <CHILDREN>
      </CHILDREN>
    </SPECIFICATION>
  </SPECIFICATIONS>
  </REQ-IF-CONTENT></CORE-CONTENT>
</REQ-IF>
"""


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "samples/export_schema_coverage.reqif"
    open(out, "w", encoding="utf-8").write(build())
    print(f"Wrote {out}")
