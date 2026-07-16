import scripts.latest_release as lrel

def E(v, pre=False, at="2026-01-01T00:00:00Z"):
    return {"version": v, "prerelease": pre, "published_at": at}

def test_select_stable_ignores_prereleases():
    entries = [E("4.1.1"), E("5.0.0-beta.6", pre=True, at="2026-07-10T00:00:00Z"), E("4.0.4")]
    got = lrel.select_versions(entries)
    assert got["stable"] == "4.1.1"
    assert got["all_stable"] == ["4.0.4", "4.1.1"]

def test_select_prerelease_newest_ahead_of_stable():
    entries = [E("4.1.1"), E("5.0.0-alpha.1", pre=True, at="2026-06-29T00:00:00Z"),
               E("5.0.0-beta.6", pre=True, at="2026-07-10T00:00:00Z")]
    got = lrel.select_versions(entries)
    assert got["prerelease"] == "5.0.0-beta.6"

def test_select_no_stable():
    entries = [E("0.33.0-rc.2", pre=True)]
    got = lrel.select_versions(entries)
    assert got["stable"] is None
    assert got["all_stable"] == []
    assert got["prerelease"] == "0.33.0-rc.2"
