import os, scripts.register_release as reg

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
