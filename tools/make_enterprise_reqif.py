"""Generate a harder, still-small synthetic DOORS-style ReqIF export: more
attribute types and structural shapes than samples/export.reqif, to find
converter bugs that are domain-agnostic (not specific to any one client's
schema). Kept to ~14 objects across 2 modules on purpose -- this is about
variety, not volume.

Exercises, beyond what samples/export.reqif already covers:
- Two modules, each with a heading/folder object (no text, a DOORS pattern
  for section titles) with child requirements nested under it
- An ENUMERATION attribute (Priority), to check whether the converter
  resolves it to a human-readable value or leaves a raw ReqIF identifier
- A BOOLEAN attribute (a DOORS "suspect link" style flag) and a DATE
  attribute (last-reviewed), types the converter has not been exercised
  against before
- Slovak/Unicode text (diacritics) in both requirement text and headers
- An embedded OLE-style <object> reference (distinct from <img>) in rich text
"""
import sys
from xml.sax.saxutils import escape

# (identifier, foreign_id, name, text, asil, priority_enum_value_ref, suspect, last_reviewed)
REQS = [
    ("REQ-10", 10, "Overenie identity", "Systém musí overiť identitu užívateľa pred udelením prístupu k chránenému zdroju.", "B", "ev-high", "false", "2026-10-15"),
    ("REQ-11", 11, "Uzamknutie účtu", "Systém musí uzamknúť účet po piatich neúspešných pokusoch o prihlásenie.", "B", "ev-medium", "true", "2026-09-01"),
    ("REQ-12", 12, "Záznam udalostí", "Systém musí zaznamenať každý pokus o overenie s časovou pečiatkou a výsledkom. Príloha: [schéma architektúry]", "A", "ev-low", "false", "2026-10-15"),
]
HEADINGS = [("HEAD-1", "1. Bezpečnosť (Security)"), ("HEAD-2", "2. Prevádzka (Operations)")]
REQS_2 = [
    ("REQ-20", 20, "Časový limit relácie", "Systém musí ukončiť nečinnú relácie po pätnástich minútach.", "QM", "ev-low", "false", "2026-08-01"),
]
RELATIONS = [("REQ-11", "REQ-10"), ("REQ-12", "REQ-10")]


def spec_object(uid, n, name, text, asil, priority_ref, suspect, reviewed):
    return f"""    <SPEC-OBJECT IDENTIFIER="so-{uid}" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPEC-OBJECT-TYPE-REF>sot-req</SPEC-OBJECT-TYPE-REF></TYPE>
      <VALUES>
        <ATTRIBUTE-VALUE-INTEGER THE-VALUE="{n}"><DEFINITION><ATTRIBUTE-DEFINITION-INTEGER-REF>ad-foreignid</ATTRIBUTE-DEFINITION-INTEGER-REF></DEFINITION></ATTRIBUTE-VALUE-INTEGER>
        <ATTRIBUTE-VALUE-STRING THE-VALUE="{escape(name)}"><DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>ad-name</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION></ATTRIBUTE-VALUE-STRING>
        <ATTRIBUTE-VALUE-STRING THE-VALUE="{asil}"><DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>ad-asil</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION></ATTRIBUTE-VALUE-STRING>
        <ATTRIBUTE-VALUE-XHTML><DEFINITION><ATTRIBUTE-DEFINITION-XHTML-REF>ad-text</ATTRIBUTE-DEFINITION-XHTML-REF></DEFINITION><THE-VALUE><xhtml:div>{escape(text)} <xhtml:object data="arch.vsdx" alt="architecture diagram"/></xhtml:div></THE-VALUE></ATTRIBUTE-VALUE-XHTML>
        <ATTRIBUTE-VALUE-ENUMERATION><DEFINITION><ATTRIBUTE-DEFINITION-ENUMERATION-REF>ad-priority</ATTRIBUTE-DEFINITION-ENUMERATION-REF></DEFINITION><VALUES><ENUM-VALUE-REF>{priority_ref}</ENUM-VALUE-REF></VALUES></ATTRIBUTE-VALUE-ENUMERATION>
        <ATTRIBUTE-VALUE-BOOLEAN THE-VALUE="{suspect}"><DEFINITION><ATTRIBUTE-DEFINITION-BOOLEAN-REF>ad-suspect</ATTRIBUTE-DEFINITION-BOOLEAN-REF></DEFINITION></ATTRIBUTE-VALUE-BOOLEAN>
        <ATTRIBUTE-VALUE-DATE THE-VALUE="{reviewed}T00:00:00.000+02:00"><DEFINITION><ATTRIBUTE-DEFINITION-DATE-REF>ad-reviewed</ATTRIBUTE-DEFINITION-DATE-REF></DEFINITION></ATTRIBUTE-VALUE-DATE>
      </VALUES>
    </SPEC-OBJECT>"""


def heading_object(uid, name):
    """A DOORS section heading: has a Name but no ReqIF.Text -- tests the
    converter against an item with no requirement text at all."""
    return f"""    <SPEC-OBJECT IDENTIFIER="so-{uid}" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPEC-OBJECT-TYPE-REF>sot-heading</SPEC-OBJECT-TYPE-REF></TYPE>
      <VALUES>
        <ATTRIBUTE-VALUE-STRING THE-VALUE="{escape(name)}"><DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>ad-h-name</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION></ATTRIBUTE-VALUE-STRING>
      </VALUES>
    </SPEC-OBJECT>"""


def build() -> str:
    objs = [spec_object(*r) for r in REQS] + [spec_object(*r) for r in REQS_2]
    objs += [heading_object(uid, name) for uid, name in HEADINGS]

    rels = [f"""    <SPEC-RELATION IDENTIFIER="sr-{i}" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPEC-RELATION-TYPE-REF>srt-link</SPEC-RELATION-TYPE-REF></TYPE>
      <SOURCE><SPEC-OBJECT-REF>so-{s}</SPEC-OBJECT-REF></SOURCE>
      <TARGET><SPEC-OBJECT-REF>so-{t}</SPEC-OBJECT-REF></TARGET>
    </SPEC-RELATION>""" for i, (s, t) in enumerate(RELATIONS, 1)]

    # module 1: HEAD-1 folder containing REQ-10..12; module 2: HEAD-2 folder containing REQ-20
    def leaf(uid):
        return f"""        <SPEC-HIERARCHY IDENTIFIER="sh-{uid}" LAST-CHANGE="2026-10-20T10:00:00Z"><OBJECT><SPEC-OBJECT-REF>so-{uid}</SPEC-OBJECT-REF></OBJECT></SPEC-HIERARCHY>"""

    hier = f"""        <SPEC-HIERARCHY IDENTIFIER="sh-HEAD-1" LAST-CHANGE="2026-10-20T10:00:00Z">
          <OBJECT><SPEC-OBJECT-REF>so-HEAD-1</SPEC-OBJECT-REF></OBJECT>
          <CHILDREN>
{chr(10).join(leaf(uid) for uid, *_ in REQS)}
          </CHILDREN>
        </SPEC-HIERARCHY>
        <SPEC-HIERARCHY IDENTIFIER="sh-HEAD-2" LAST-CHANGE="2026-10-20T10:00:00Z">
          <OBJECT><SPEC-OBJECT-REF>so-HEAD-2</SPEC-OBJECT-REF></OBJECT>
          <CHILDREN>
{chr(10).join(leaf(uid) for uid, *_ in REQS_2)}
          </CHILDREN>
        </SPEC-HIERARCHY>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <THE-HEADER><REQ-IF-HEADER IDENTIFIER="header-1">
    <CREATION-TIME>2026-10-20T10:00:00Z</CREATION-TIME>
    <REQ-IF-TOOL-ID>synthetic-doors-export-enterprise</REQ-IF-TOOL-ID>
    <REQ-IF-VERSION>1.0</REQ-IF-VERSION>
    <SOURCE-TOOL-ID>synthetic-doors-export-enterprise</SOURCE-TOOL-ID>
    <TITLE>Synthetic Enterprise DOORS Export</TITLE>
  </REQ-IF-HEADER></THE-HEADER>
  <CORE-CONTENT><REQ-IF-CONTENT>
  <DATATYPES>
    <DATATYPE-DEFINITION-INTEGER IDENTIFIER="dt-int" LAST-CHANGE="2026-10-20T10:00:00Z" MAX="2147483647" MIN="0"/>
    <DATATYPE-DEFINITION-STRING IDENTIFIER="dt-str" LAST-CHANGE="2026-10-20T10:00:00Z" MAX-LENGTH="255"/>
    <DATATYPE-DEFINITION-XHTML IDENTIFIER="dt-xhtml" LAST-CHANGE="2026-10-20T10:00:00Z"/>
    <DATATYPE-DEFINITION-BOOLEAN IDENTIFIER="dt-bool" LAST-CHANGE="2026-10-20T10:00:00Z"/>
    <DATATYPE-DEFINITION-DATE IDENTIFIER="dt-date" LAST-CHANGE="2026-10-20T10:00:00Z"/>
    <DATATYPE-DEFINITION-ENUMERATION IDENTIFIER="dt-priority" LONG-NAME="Priority" LAST-CHANGE="2026-10-20T10:00:00Z">
      <SPECIFIED-VALUES>
        <ENUM-VALUE IDENTIFIER="ev-low" LONG-NAME="Low" LAST-CHANGE="2026-10-20T10:00:00Z"><PROPERTIES><EMBEDDED-VALUE KEY="0" OTHER-CONTENT=""/></PROPERTIES></ENUM-VALUE>
        <ENUM-VALUE IDENTIFIER="ev-medium" LONG-NAME="Medium" LAST-CHANGE="2026-10-20T10:00:00Z"><PROPERTIES><EMBEDDED-VALUE KEY="1" OTHER-CONTENT=""/></PROPERTIES></ENUM-VALUE>
        <ENUM-VALUE IDENTIFIER="ev-high" LONG-NAME="High" LAST-CHANGE="2026-10-20T10:00:00Z"><PROPERTIES><EMBEDDED-VALUE KEY="2" OTHER-CONTENT=""/></PROPERTIES></ENUM-VALUE>
      </SPECIFIED-VALUES>
    </DATATYPE-DEFINITION-ENUMERATION>
  </DATATYPES>
  <SPEC-TYPES>
    <SPEC-OBJECT-TYPE IDENTIFIER="sot-req" LONG-NAME="Requirement" LAST-CHANGE="2026-10-20T10:00:00Z">
      <SPEC-ATTRIBUTES>
        <ATTRIBUTE-DEFINITION-INTEGER IDENTIFIER="ad-foreignid" LONG-NAME="ReqIF.ForeignID" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-INTEGER-REF>dt-int</DATATYPE-DEFINITION-INTEGER-REF></TYPE></ATTRIBUTE-DEFINITION-INTEGER>
        <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ad-name" LONG-NAME="ReqIF.Name" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-STRING-REF>dt-str</DATATYPE-DEFINITION-STRING-REF></TYPE></ATTRIBUTE-DEFINITION-STRING>
        <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ad-asil" LONG-NAME="ASIL" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-STRING-REF>dt-str</DATATYPE-DEFINITION-STRING-REF></TYPE></ATTRIBUTE-DEFINITION-STRING>
        <ATTRIBUTE-DEFINITION-XHTML IDENTIFIER="ad-text" LONG-NAME="ReqIF.Text" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-XHTML-REF>dt-xhtml</DATATYPE-DEFINITION-XHTML-REF></TYPE></ATTRIBUTE-DEFINITION-XHTML>
        <ATTRIBUTE-DEFINITION-ENUMERATION IDENTIFIER="ad-priority" LONG-NAME="Priority" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-ENUMERATION-REF>dt-priority</DATATYPE-DEFINITION-ENUMERATION-REF></TYPE></ATTRIBUTE-DEFINITION-ENUMERATION>
        <ATTRIBUTE-DEFINITION-BOOLEAN IDENTIFIER="ad-suspect" LONG-NAME="ReqIF.Suspect" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-BOOLEAN-REF>dt-bool</DATATYPE-DEFINITION-BOOLEAN-REF></TYPE></ATTRIBUTE-DEFINITION-BOOLEAN>
        <ATTRIBUTE-DEFINITION-DATE IDENTIFIER="ad-reviewed" LONG-NAME="LastReviewed" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-DATE-REF>dt-date</DATATYPE-DEFINITION-DATE-REF></TYPE></ATTRIBUTE-DEFINITION-DATE>
      </SPEC-ATTRIBUTES>
    </SPEC-OBJECT-TYPE>
    <SPEC-OBJECT-TYPE IDENTIFIER="sot-heading" LONG-NAME="Heading" LAST-CHANGE="2026-10-20T10:00:00Z">
      <SPEC-ATTRIBUTES>
        <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ad-h-name" LONG-NAME="ReqIF.Name" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-STRING-REF>dt-str</DATATYPE-DEFINITION-STRING-REF></TYPE></ATTRIBUTE-DEFINITION-STRING>
      </SPEC-ATTRIBUTES>
    </SPEC-OBJECT-TYPE>
    <SPEC-RELATION-TYPE IDENTIFIER="srt-link" LONG-NAME="Link" LAST-CHANGE="2026-10-20T10:00:00Z"/>
    <SPECIFICATION-TYPE IDENTIFIER="st-module" LONG-NAME="Module" LAST-CHANGE="2026-10-20T10:00:00Z"/>
  </SPEC-TYPES>
  <SPEC-OBJECTS>
{chr(10).join(objs)}
  </SPEC-OBJECTS>
  <SPEC-RELATIONS>
{chr(10).join(rels)}
  </SPEC-RELATIONS>
  <SPECIFICATIONS>
    <SPECIFICATION IDENTIFIER="spec-1" LONG-NAME="Enterprise System Requirements" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPECIFICATION-TYPE-REF>st-module</SPECIFICATION-TYPE-REF></TYPE>
      <CHILDREN>
{hier}
      </CHILDREN>
    </SPECIFICATION>
  </SPECIFICATIONS>
  </REQ-IF-CONTENT></CORE-CONTENT>
</REQ-IF>
"""


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "samples/export_enterprise.reqif"
    open(out, "w", encoding="utf-8").write(build())
    print(f"Wrote {out}")
