import scripts.repo_scan as rs

SINCE = "2026-01-16T00:00:00Z"

def node(name, pushed, commit, archived=False, empty=False, entries=("src","README.md"), priv=False):
    return {"name":name,"url":f"https://github.com/midnightntwrk/{name}","isArchived":archived,
            "isEmpty":empty,"isPrivate":priv,"description":"d","pushedAt":pushed,
            "lastCommit":commit,"topLevelEntries":list(entries)}

def test_is_active_filters():
    assert rs.is_active(node("a","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z"), SINCE) is True
    assert rs.is_active(node("b","2025-01-01T0:0:0Z","2025-01-01T00:00:00Z"), SINCE) is False  # too old
    assert rs.is_active(node("c","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z",archived=True), SINCE) is False
    assert rs.is_active(node("d","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z",empty=True), SINCE) is False

def test_scaffold_only_excluded():
    scaffold = {".envrc",".github","CHANGELOG.md","CODEOWNERS","CODE_OF_CONDUCT.md",
                "CONTRIBUTING.md","LICENSE","README.md","SECURITY.md"}
    n = node("s","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z",entries=scaffold)
    assert rs.is_active(n, SINCE) is False

def test_build_list_sorts_desc_and_appends_extra():
    nodes=[node("old","2026-02-01T0:0:0Z","2026-02-01T00:00:00Z"),
           node("new","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z")]
    extra=[{"name":"compact","url":"https://github.com/LFDT-Minokawa/compact",
            "last_commit":"2026-06-25T00:00:00Z","description":"Compact","private":False}]
    out = rs.build_repo_list(nodes, SINCE, extra)
    assert [r["name"] for r in out] == ["new","compact","old"]
