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

def R(tag, pre=False):
    return {"tagName": tag, "isPrerelease": pre, "publishedAt": "2026-01-01T00:00:00Z"}

def test_gh_rows_filters_foreign_streams():
    # midnightntwrk/compact ships two release streams + a dev tag in one repo.
    rows = [R("compact-v0.5.1"), R("compactc-v0.31.1"), R("compactc-dev-abc"), R("compact-v0.4.0")]
    got = lrel.gh_rows_to_entries(rows, "compact-v")
    assert [e["version"] for e in got] == ["0.5.1", "0.4.0"]

def test_gh_rows_empty_prefix_keeps_all():
    rows = [R("1.0.0"), R("2.0.0", pre=True)]
    got = lrel.gh_rows_to_entries(rows, "")
    assert [e["version"] for e in got] == ["1.0.0", "2.0.0"]
    assert got[1]["prerelease"] is True

def test_is_tracked_source():
    assert lrel.is_tracked_source("npm:@midnight-ntwrk/midnight-js")
    assert lrel.is_tracked_source("gh-release")
    assert lrel.is_tracked_source("crates:midnight-onchain-runtime")  # now resolved
    assert not lrel.is_tracked_source("ignored")

def test_resolve_untracked_sources_make_no_calls():
    # ignored / unknown short-circuit before any npm/gh/cargo subprocess.
    for src in ("ignored", "something-unknown"):
        got = lrel.resolve({"version_source": src})
        assert got["tracked"] is False
        assert got["stable"] is None and got["all_stable"] == []
        assert got["version_source"] == src

def test_resolve_crate_stable(monkeypatch):
    # A crate that resolves to a stable version behaves like any tracked source.
    monkeypatch.setattr(lrel, "_crate_version", lambda cfg, crate: "3.1.0")
    got = lrel.resolve({"version_source": "crates:midnight-onchain-runtime"})
    assert got["tracked"] is True
    assert got["stable"] == "3.1.0" and got["all_stable"] == ["3.1.0"]
    assert got["prerelease"] is None

def test_resolve_crate_prerelease_only(monkeypatch):
    # A crate whose only version is a prerelease (e.g. workspace 8.2.0-rc.1):
    # surfaced as prerelease, with no stable and nothing to be "behind".
    monkeypatch.setattr(lrel, "_crate_version", lambda cfg, crate: "8.2.0-rc.1")
    got = lrel.resolve({"version_source": "crates:midnight-proof-server"})
    assert got["tracked"] is True
    assert got["stable"] is None and got["all_stable"] == []
    assert got["prerelease"] == "8.2.0-rc.1"

def test_resolve_crate_unresolvable_untracked(monkeypatch):
    # Neither cargo nor Cargo.toml yields a version → degrade to untracked,
    # never error, never fabricate.
    monkeypatch.setattr(lrel, "_crate_version", lambda cfg, crate: None)
    got = lrel.resolve({"version_source": "crates:whatever"})
    assert got["tracked"] is False
    assert got["stable"] is None and got["all_stable"] == []
    assert got["version_source"] == "crates:whatever"
