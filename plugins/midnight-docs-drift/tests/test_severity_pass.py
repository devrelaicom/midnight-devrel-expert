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

def test_contextual_high_requires_code_context():
    s, _ = sp.severity_for("You must disclose your feelings in this advice column", [], True)
    assert s == "low"
    s2, _ = sp.severity_for("The `witness` value must be disclosed before the circuit returns", ["compact"], False)
    assert s2 == "high"

def test_unclassified_caps_at_low_even_with_code_token():
    s, sig = sp.severity_for("The auth_flag determines whether the greeting renders", [], True)
    assert (s, sig) == ("low", "unclassified")

def test_code_domain_default_branch():
    s, sig = sp.severity_for("Compact circuits enforce privacy through zero-knowledge proofs", ["compact"], False)
    assert (s, sig) == ("medium", "code-domain-default")

def test_default_soft_branch():
    s, sig = sp.severity_for("A plain sentence with no markers at all", ["some-other-domain"], False)
    assert (s, sig) == ("low", "default-soft")
