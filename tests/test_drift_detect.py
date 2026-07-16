import scripts.drift_detect as dd

def test_resolve_prefers_release():
    assert dd.resolve_publish("2026-06-25T00:00:00Z","2026-07-01T00:00:00Z") == ("2026-06-25T00:00:00Z","release")
    assert dd.resolve_publish(None,"2026-07-01T00:00:00Z") == ("2026-07-01T00:00:00Z","push")
    assert dd.resolve_publish(None,None) == (None,"unknown")

def test_drift_for_page_lists_newer_only_desc():
    pubs = {"repoA":("2026-07-10T00:00:00Z","release"),
            "repoB":("2026-05-01T00:00:00Z","push"),
            "repoC":("2026-07-14T00:00:00Z","release")}
    out = dd.drift_for_page("2026-06-01T00:00:00Z", pubs)
    assert [d["repo"] for d in out] == ["repoC","repoA"]      # repoB older -> excluded; sorted desc
    assert out[0]["method"] == "release"

def test_drift_for_page_empty_when_doc_newest():
    pubs = {"r":("2026-01-01T00:00:00Z","push")}
    assert dd.drift_for_page("2026-06-01T00:00:00Z", pubs) == []
