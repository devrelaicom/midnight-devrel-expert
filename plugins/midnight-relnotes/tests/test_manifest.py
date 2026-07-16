import scripts.manifest as man

def test_unmapped_dirs_reports_new():
    mapped = ["docs/relnotes/midnight-js", "docs/relnotes/ledger"]
    actual = ["docs/relnotes/midnight-js", "docs/relnotes/ledger", "docs/relnotes/proof-server"]
    assert man.unmapped_dirs(mapped, actual) == ["docs/relnotes/proof-server"]

def test_unmapped_dirs_empty_when_all_mapped():
    dirs = ["docs/relnotes/midnight-js"]
    assert man.unmapped_dirs(dirs, dirs) == []
