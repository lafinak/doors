"""Generate a synthetic DOORS-style ReqIF export (no real DOORS needed)."""
import sys
from xml.sax.saxutils import escape

REQS = [
    ("REQ-1", 1, "User Authentication", "The system shall authenticate users before granting access to any protected resource.", "B"),
    ("REQ-2", 2, "Account Lockout", "The system shall lock an account after five consecutive failed authentication attempts.", "B"),
    ("REQ-3", 3, "Authentication Logging", "The system shall log every authentication attempt with timestamp and outcome.", "A"),
    ("REQ-4", 4, "Session Timeout", "The system shall terminate an idle session after fifteen minutes.", "QM"),
    ("REQ-5", 5, "Password Complexity", "The system shall reject passwords shorter than twelve characters.", "A"),
]
# (source, target): source "refines"/traces to target
RELATIONS = [("REQ-2", "REQ-1"), ("REQ-3", "REQ-1")]


def build() -> str:
    objs = []
    for uid, n, name, text, asil in REQS:
        objs.append(f"""    <SPEC-OBJECT IDENTIFIER="so-{uid}" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPEC-OBJECT-TYPE-REF>sot-req</SPEC-OBJECT-TYPE-REF></TYPE>
      <VALUES>
        <ATTRIBUTE-VALUE-INTEGER THE-VALUE="{n}"><DEFINITION><ATTRIBUTE-DEFINITION-INTEGER-REF>ad-foreignid</ATTRIBUTE-DEFINITION-INTEGER-REF></DEFINITION></ATTRIBUTE-VALUE-INTEGER>
        <ATTRIBUTE-VALUE-STRING THE-VALUE="{escape(name)}"><DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>ad-name</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION></ATTRIBUTE-VALUE-STRING>
        <ATTRIBUTE-VALUE-STRING THE-VALUE="{asil}"><DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>ad-asil</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION></ATTRIBUTE-VALUE-STRING>
        <ATTRIBUTE-VALUE-XHTML><DEFINITION><ATTRIBUTE-DEFINITION-XHTML-REF>ad-text</ATTRIBUTE-DEFINITION-XHTML-REF></DEFINITION><THE-VALUE><xhtml:div>{escape(text)}</xhtml:div></THE-VALUE></ATTRIBUTE-VALUE-XHTML>
      </VALUES>
    </SPEC-OBJECT>""")
    rels = []
    for i, (s, t) in enumerate(RELATIONS, 1):
        rels.append(f"""    <SPEC-RELATION IDENTIFIER="sr-{i}" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPEC-RELATION-TYPE-REF>srt-link</SPEC-RELATION-TYPE-REF></TYPE>
      <SOURCE><SPEC-OBJECT-REF>so-{s}</SPEC-OBJECT-REF></SOURCE>
      <TARGET><SPEC-OBJECT-REF>so-{t}</SPEC-OBJECT-REF></TARGET>
    </SPEC-RELATION>""")
    hier = []
    for uid, *_ in REQS:
        hier.append(f"""        <SPEC-HIERARCHY IDENTIFIER="sh-{uid}" LAST-CHANGE="2026-10-20T10:00:00Z"><OBJECT><SPEC-OBJECT-REF>so-{uid}</SPEC-OBJECT-REF></OBJECT></SPEC-HIERARCHY>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <THE-HEADER><REQ-IF-HEADER IDENTIFIER="header-1">
    <CREATION-TIME>2026-10-20T10:00:00Z</CREATION-TIME>
    <REQ-IF-TOOL-ID>synthetic-doors-export</REQ-IF-TOOL-ID>
    <REQ-IF-VERSION>1.0</REQ-IF-VERSION>
    <SOURCE-TOOL-ID>synthetic-doors-export</SOURCE-TOOL-ID>
    <TITLE>Synthetic DOORS Export</TITLE>
  </REQ-IF-HEADER></THE-HEADER>
  <CORE-CONTENT><REQ-IF-CONTENT>
  <DATATYPES>
    <DATATYPE-DEFINITION-INTEGER IDENTIFIER="dt-int" LAST-CHANGE="2026-10-20T10:00:00Z" MAX="2147483647" MIN="0"/>
    <DATATYPE-DEFINITION-STRING IDENTIFIER="dt-str" LAST-CHANGE="2026-10-20T10:00:00Z" MAX-LENGTH="255"/>
    <DATATYPE-DEFINITION-XHTML IDENTIFIER="dt-xhtml" LAST-CHANGE="2026-10-20T10:00:00Z"/>
  </DATATYPES>
  <SPEC-TYPES>
    <SPEC-OBJECT-TYPE IDENTIFIER="sot-req" LONG-NAME="Requirement" LAST-CHANGE="2026-10-20T10:00:00Z">
      <SPEC-ATTRIBUTES>
        <ATTRIBUTE-DEFINITION-INTEGER IDENTIFIER="ad-foreignid" LONG-NAME="ReqIF.ForeignID" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-INTEGER-REF>dt-int</DATATYPE-DEFINITION-INTEGER-REF></TYPE></ATTRIBUTE-DEFINITION-INTEGER>
        <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ad-name" LONG-NAME="ReqIF.Name" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-STRING-REF>dt-str</DATATYPE-DEFINITION-STRING-REF></TYPE></ATTRIBUTE-DEFINITION-STRING>
        <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ad-asil" LONG-NAME="ASIL" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-STRING-REF>dt-str</DATATYPE-DEFINITION-STRING-REF></TYPE></ATTRIBUTE-DEFINITION-STRING>
        <ATTRIBUTE-DEFINITION-XHTML IDENTIFIER="ad-text" LONG-NAME="ReqIF.Text" LAST-CHANGE="2026-10-20T10:00:00Z"><TYPE><DATATYPE-DEFINITION-XHTML-REF>dt-xhtml</DATATYPE-DEFINITION-XHTML-REF></TYPE></ATTRIBUTE-DEFINITION-XHTML>
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
    <SPECIFICATION IDENTIFIER="spec-1" LONG-NAME="System Requirements" LAST-CHANGE="2026-10-20T10:00:00Z">
      <TYPE><SPECIFICATION-TYPE-REF>st-module</SPECIFICATION-TYPE-REF></TYPE>
      <CHILDREN>
{chr(10).join(hier)}
      </CHILDREN>
    </SPECIFICATION>
  </SPECIFICATIONS>
  </REQ-IF-CONTENT></CORE-CONTENT>
</REQ-IF>
"""


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "samples/export.reqif"
    open(out, "w", encoding="utf-8").write(build())
    print(f"Wrote {out}")
