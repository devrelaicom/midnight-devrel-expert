import os, pytest, scripts.register_release as reg

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "DynamicListSample.js")

def _rel():
    return {"version": "4.1.1", "status": "LATEST", "date": "2 June 2026",
            "summary": "Breaking error handling changes",
            "details": ["Renamed `IndexerFormattedError.cause` to `.errors`",
                        "Added qanet support in `testkit-js`"],
            "artifacts": [{"name": "NPM Package", "url": "https://www.npmjs.com/search?q=midnight-ntwrk"}],
            "link": "/relnotes/midnight-js/midnight-js-4-1-1"}

def test_js_string_escapes_apostrophes():
    assert reg.js_string("it's") == "'it\\'s'"

def test_render_release_contains_fields():
    out = reg.render_release(_rel())
    assert "version: '4.1.1'" in out
    assert "status: 'LATEST'" in out
    assert "link: '/relnotes/midnight-js/midnight-js-4-1-1'" in out

def test_register_prepends_and_demotes():
    src = open(FIX).read()
    out = reg.register(src, _rel())
    # new version appears before the old one
    assert out.index("'4.1.1'") < out.index("'4.0.4'")
    # exactly one LATEST remains (the new one); the old became SUPPORTED
    assert out.count("status: 'LATEST'") == 1
    assert "status: 'SUPPORTED'" in out
    assert out.index("status: 'LATEST'") < out.index("status: 'SUPPORTED'")

def test_register_into_empty_list_no_prior_latest():
    src = "const releases = [\n];\n"
    out = reg.register(src, _rel())
    assert out.count("status: 'LATEST'") == 1
    assert "status: 'SUPPORTED'" not in out

def test_js_string_escapes_newline():
    assert reg.js_string("a\nb") == "'a\\nb'"

def test_js_string_escapes_cr_and_line_separators():
    # CRLF-authored notes and pasted U+2028/U+2029 are JS LineTerminators too.
    assert reg.js_string("a\r\nb") == "'a\\r\\nb'"
    assert reg.js_string("a" + chr(0x2028) + "b") == "'a\\u2028b'"
    assert reg.js_string("a" + chr(0x2029) + "b") == "'a\\u2029b'"

def test_register_missing_anchor_raises_clear_error():
    with pytest.raises(ValueError, match="anchor"):
        reg.register("const somethingElse = [];", _rel())

def test_register_non_latest_does_not_demote():
    src = open(FIX).read()
    backport = {**_rel(), "status": "SUPPORTED"}
    out = reg.register(src, backport)
    # the pre-existing LATEST must be left intact when the new note isn't LATEST
    assert out.count("status: 'LATEST'") == 1
    assert out.index("'4.1.1'") < out.index("'4.0.4'")
