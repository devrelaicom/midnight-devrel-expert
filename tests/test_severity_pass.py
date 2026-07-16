import scripts.severity_pass as sp

def test_high_on_code_exact():
    s,_ = sp.severity_for("persistentHash<T>() returns Bytes<32>", ["compact"], False)
    assert s == "high"

def test_low_on_conceptual_unclassified():
    s,_ = sp.severity_for("Zswap is a protocol that enables private transactions", [], True)
    assert s == "low"

def test_medium_on_named_construct_behaviour():
    s,_ = sp.severity_for("The `increment` circuit updates the counter", ["compact"], False)
    assert s == "medium"
