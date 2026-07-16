import scripts.latest_relnote as lr

def test_highest_relnote_picks_max():
    files = ["midnight-js-4-0-4.mdx", "midnight-js-4-1-1.mdx", "midnight-js-3-2-0.mdx", "README.md"]
    got = lr.highest_relnote(files, "midnight-js")
    assert got == {"version": "4.1.1", "filename": "midnight-js-4-1-1.mdx"}

def test_highest_relnote_filters_by_prefix():
    files = ["compact-0-20-28-0.mdx", "toolchain-0.31.0.mdx", "toolchain-0.30.0.mdx"]
    assert lr.highest_relnote(files, "toolchain") == {"version": "0.31.0", "filename": "toolchain-0.31.0.mdx"}

def test_highest_relnote_none_when_empty():
    assert lr.highest_relnote(["README.md"], "midnight-js") is None
