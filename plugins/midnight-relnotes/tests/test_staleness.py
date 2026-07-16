import scripts.staleness as st

def test_verdict_up_to_date():
    v = st.verdict("4.1.1", "4.1.1", ["4.0.4", "4.1.1"])
    assert v["behind"] == 0 and v["stale"] is False and v["gap_versions"] == []

def test_verdict_one_behind():
    v = st.verdict("4.0.4", "4.1.1", ["4.0.4", "4.1.1"])
    assert v["behind"] == 1 and v["stale"] is True and v["more_than_one_behind"] is False
    assert v["gap_versions"] == ["4.1.1"]

def test_verdict_more_than_one_behind():
    v = st.verdict("4.0.1", "4.1.1", ["4.0.1", "4.0.2", "4.0.4", "4.1.1"])
    assert v["behind"] == 3 and v["more_than_one_behind"] is True
    assert v["gap_versions"] == ["4.0.2", "4.0.4", "4.1.1"]

def test_verdict_no_relnote_yet():
    v = st.verdict(None, "4.1.1", ["4.0.4", "4.1.1"])
    assert v["behind"] == 2 and v["stale"] is True
    assert v["gap_versions"] == ["4.0.4", "4.1.1"]
