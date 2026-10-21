"""Regression tests for bugs found by stress-testing the pipeline."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = (ROOT / "samples" / "export.reqif").read_text(encoding="utf-8")
SCHEMA = ROOT / "schemas" / "srd_requirement.json"
GOOD = {
    "active": True, "derived": False, "normative": True, "ref": "", "reviewed": None, "links": [],
    "level": "1.0", "header": "Header ok", "asil": "B", "status": "draft",
    "text": "The system shall do a thing under test.\n", "verification_method": "test",
    "rationale": "Because safety needs it.",
}


def run(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, **kw)


@pytest.fixture
def repo(tmp_path):
    run("git init -q", tmp_path, shell=True)
    run("doorstop create SRD ./reqs/SRD", tmp_path, shell=True)
    return tmp_path


def put(repo, uid, **over):
    item = {**GOOD, **over}
    (repo / "reqs" / "SRD" / f"{uid}.yml").write_text(yaml.safe_dump(item, allow_unicode=True), encoding="utf-8")


def iso(repo, directory="reqs/SRD"):
    return run([sys.executable, "-I", str(ROOT / "scripts/validate_iso26262.py"), directory, str(SCHEMA)], repo)


def convert(repo, xml):
    src = repo / "in.reqif"
    src.write_text(xml, encoding="utf-8")
    return run([sys.executable, str(ROOT / "tools/reqif_to_doorstop.py"), str(src), "SRD"], repo)


def items(repo):
    return {p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted((repo / "reqs/SRD").glob("SRD*.yml"))}


# ---- ISO validator
@pytest.mark.parametrize("over", [
    {"text": "The system shallnot do anything at all"},
    {"rationale": " " * 12},
    {"asil": "b"},
    {"status": "approved"},
    {"status": "approved", "reviewed": "forged-stamp"},
])
def test_iso_rejects(repo, over):
    put(repo, "SRD001", **over)
    assert iso(repo).returncode == 1


def test_iso_accepts_four_digit_uid(repo):
    put(repo, "SRD1000")
    assert iso(repo).returncode == 0


def test_iso_accepts_genuine_review(repo):
    put(repo, "SRD001", status="reviewed")
    assert iso(repo).returncode == 1  # no stamp yet
    run("doorstop review SRD001", repo, shell=True)
    assert iso(repo).returncode == 0
    item = yaml.safe_load((repo / "reqs/SRD/SRD001.yml").read_text())
    item["text"] += "tampered after review"
    (repo / "reqs/SRD/SRD001.yml").write_text(yaml.safe_dump(item))
    assert iso(repo).returncode == 1  # stale stamp


def test_iso_accepts_a_correctly_computed_stamp_without_doorstop_review(repo):
    """Known limitation (README "Known limits"): the review stamp is
    sha256(uid, text, ref, links, ...) -- a content hash, not a signature tied to
    a human. Anyone who can `import doorstop` can compute the exact value
    `doorstop review` would write, without ever running it or being a human.
    validate_iso26262.py has no way to tell the two apart; only human PR review
    enforced by branch protection (outside this repo) catches this.
    This test pins today's actual (permissive) behavior so a future change to the
    stamp check is a visible diff here, not a silent regression either direction."""
    import doorstop

    put(repo, "SRD001")
    tree = doorstop.build(root=str(repo))
    tree.load()
    forged = tree.find_document("SRD").find_item("SRD001").stamp(links=True).value
    put(repo, "SRD001", status="approved", reviewed=forged)  # never ran `doorstop review`
    assert iso(repo).returncode == 0  # accepted anyway -- see docstring


def test_iso_empty_or_missing_directory_fails(repo):
    assert iso(repo).returncode == 1
    assert iso(repo, "nope").returncode == 1


@pytest.mark.parametrize("content", ["", "- a\n- b\n", "a: [unclosed\n", "hello\n"])
def test_iso_bad_files_fail_without_traceback(repo, content):
    (repo / "reqs/SRD/SRD001.yml").write_text(content)
    r = iso(repo)
    assert r.returncode == 1 and "Traceback" not in r.stderr


# ---- structural validator
def test_validate_flags_cycles_and_self_links(repo):
    put(repo, "SRD001", links=[{"SRD001": None}, {"SRD002": None}])
    put(repo, "SRD002", links=[{"SRD001": None}])
    r = run([sys.executable, str(ROOT / "tools/validate.py")], repo)
    assert r.returncode == 1 and "links to itself" in r.stdout and "cycle" in r.stdout


def test_validate_never_modifies_files(repo):
    put(repo, "SRD001")
    before = (repo / "reqs/SRD/SRD001.yml").read_bytes()
    run([sys.executable, str(ROOT / "tools/validate.py")], repo)
    assert (repo / "reqs/SRD/SRD001.yml").read_bytes() == before


# ---- ReqIF converter
def test_convert_is_idempotent_and_keeps_doors_id(repo):
    assert convert(repo, SAMPLE).returncode == 0
    first = items(repo)
    assert len(first) == 5 and all(i["doors_id"].startswith("so-") for i in first.values())
    assert convert(repo, SAMPLE).returncode == 0
    assert items(repo).keys() == first.keys()


def test_convert_imports_are_draft_and_unreviewed(repo):
    convert(repo, SAMPLE)
    assert all(i["status"] == "draft" and not i["reviewed"] for i in items(repo).values())


def test_convert_text_cannot_inject_yaml_fields(repo):
    evil = "The system shall obey.\nstatus: approved\nreviewed: abc\nasil: D"
    xml = SAMPLE.replace("The system shall authenticate users before granting access to any protected resource.", evil)
    convert(repo, xml)
    first = items(repo)["SRD001"]
    assert first["status"] == "draft" and first["asil"] == "B" and not first["reviewed"]


def test_convert_warns_about_dropped_links(repo):
    xml = SAMPLE.replace("</SPEC-RELATIONS>", '<SPEC-RELATION IDENTIFIER="x"><TYPE><SPEC-RELATION-TYPE-REF>srt-link</SPEC-RELATION-TYPE-REF></TYPE><SOURCE><SPEC-OBJECT-REF>so-REQ-1</SPEC-OBJECT-REF></SOURCE><TARGET><SPEC-OBJECT-REF>ghost</SPEC-OBJECT-REF></TARGET></SPEC-RELATION></SPEC-RELATIONS>')
    r = convert(repo, xml)
    assert r.returncode == 0 and "ghost" in r.stderr


def test_convert_warns_about_dropped_attributes(repo):
    """An attribute not listed in EXTRA_ATTRS must be reported on stderr, not
    silently dropped -- matches the module docstring's "reported on stderr
    instead of being dropped silently" promise, which previously only held
    for links, not for arbitrary unmapped attributes (found by stress-testing
    with a synthetic export using attribute types outside the base sample:
    enum, boolean, date)."""
    xml = SAMPLE.replace(
        "</SPEC-ATTRIBUTES>",
        '<ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ad-priority" LONG-NAME="Priority"><TYPE><DATATYPE-DEFINITION-STRING-REF>dt-str</DATATYPE-DEFINITION-STRING-REF></TYPE></ATTRIBUTE-DEFINITION-STRING></SPEC-ATTRIBUTES>',
        1,
    ).replace(
        "</VALUES>",
        '<ATTRIBUTE-VALUE-STRING THE-VALUE="High"><DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>ad-priority</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION></ATTRIBUTE-VALUE-STRING></VALUES>',
        1,
    )
    r = convert(repo, xml)
    assert r.returncode == 0
    assert "Priority" in r.stderr and "not carried over" in r.stderr
    assert "priority" not in items(repo)["SRD001"]


def test_convert_non_numeric_foreign_id_does_not_crash(repo):
    xml = SAMPLE.replace('<ATTRIBUTE-VALUE-INTEGER THE-VALUE="1"', '<ATTRIBUTE-VALUE-INTEGER THE-VALUE="abc"', 1)
    assert convert(repo, xml).returncode == 0


@pytest.mark.parametrize("content", ["", "hello", "<foo/>"])
def test_convert_bad_input_is_a_clean_error(repo, content):
    r = convert(repo, content)
    assert r.returncode == 1 and "Traceback" not in r.stderr


# ---- Dolt sync (skipped where dolt is not installed)
@pytest.mark.skipif(shutil.which("dolt") is None, reason="dolt not installed")
def test_dolt_sync_rolls_back_on_failure(repo):
    put(repo, "SRD001")
    put(repo, "SRD002")
    (repo / "dolt_reqs").mkdir()
    run("dolt init && dolt sql < " + str(ROOT / "tools/dolt_schema.sql"), repo / "dolt_reqs", shell=True)
    sync = [sys.executable, str(ROOT / "tools/sync_to_dolt.py"), "reqs", "dolt_reqs"]
    assert run(sync, repo).returncode == 0
    put(repo, "SRD001", status="weird")
    assert run(sync, repo).returncode != 0
    count = run("dolt sql -r csv -q 'SELECT COUNT(*) FROM requirements'", repo / "dolt_reqs", shell=True).stdout.split()[-1]
    assert count == "2"


# ---- SWR / TST validation and CLAUDE.md link rules
def put_doc(repo, prefix, uid, **over):
    base = {**GOOD, "text": "The system shall verify things properly.\n"}
    for key in ("asil", "verification_method", "rationale"):
        base.pop(key)
    (repo / "reqs" / prefix).mkdir(parents=True, exist_ok=True)
    (repo / "reqs" / prefix / f"{uid}.yml").write_text(yaml.safe_dump({**base, **over}), encoding="utf-8")


def iso_doc(repo, prefix):
    schema = ROOT / "schemas" / f"{prefix.lower()}_requirement.json"
    return run([sys.executable, "-I", str(ROOT / "scripts/validate_iso26262.py"), f"reqs/{prefix}", str(schema)], repo)


def test_swr_must_link_to_an_srd(repo):
    put_doc(repo, "SWR", "SWR001", links=[])
    assert iso_doc(repo, "SWR").returncode == 1
    put_doc(repo, "SWR", "SWR001", links=[{"TST001": None}])  # wrong kind of parent
    assert iso_doc(repo, "SWR").returncode == 1
    put_doc(repo, "SWR", "SWR001", links=[{"SRD001": None}])
    assert iso_doc(repo, "SWR").returncode == 0


def test_tst_must_link_to_a_swr(repo):
    put_doc(repo, "TST", "TST001", text="Verify the thing works.\n", links=[{"SRD001": None}])
    assert iso_doc(repo, "TST").returncode == 1
    put_doc(repo, "TST", "TST001", text="Verify the thing works.\n", links=[{"SWR001": None}])
    assert iso_doc(repo, "TST").returncode == 0


def test_swr_text_must_be_shall_form(repo):
    put_doc(repo, "SWR", "SWR001", links=[{"SRD001": None}], text="Software handles things somehow.\n")
    assert iso_doc(repo, "SWR").returncode == 1


def test_iso_default_mode_checks_the_whole_repo():
    r = run([sys.executable, "-I", str(ROOT / "scripts/validate_iso26262.py")], ROOT)
    assert r.returncode == 0, r.stdout
    assert "== reqs/SRD" in r.stdout and "== reqs/SWR" in r.stdout and "== reqs/TST" in r.stdout


def test_imported_items_get_status_draft_for_any_document(repo):
    convert(repo, SAMPLE)
    assert all(i["status"] == "draft" for i in items(repo).values())


# ---- rich text conversion
sys.path.insert(0, str(ROOT / "tools"))
from reqif_to_doorstop import xhtml_to_text  # noqa: E402


def test_xhtml_lists_become_bullets():
    assert xhtml_to_text("<div><p>The system shall list:</p><ul><li>one</li><li>two &amp; three</li></ul></div>") == "The system shall list:\n\n- one\n- two & three"


def test_xhtml_tables_become_pipe_tables():
    text = xhtml_to_text("<div>Intro<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>After</div>")
    assert "| A | B |\n|---|---|\n| 1 | 2 |" in text and text.startswith("Intro") and text.endswith("After")


def test_xhtml_images_leave_a_visible_marker():
    assert xhtml_to_text("<div>See <object data='fig1.png'/> here</div>") == "See [image: fig1.png] here"


@pytest.mark.parametrize("raw,expected", [("", ""), ("   ", ""), ("<div>a&nbsp;b</div>", "a b"), ("<div>l1<br/>l2</div>", "l1\nl2")])
def test_xhtml_edge_cases(raw, expected):
    assert xhtml_to_text(raw) == expected
