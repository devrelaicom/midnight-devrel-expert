import scripts.aggregate as agg

def C(claim, domains, sev, page="docs/x.mdx"):
    return {"claim":claim,"domains":domains,"unclassified":not domains,
            "severity":sev,"source":{"file":page}}

def test_summarize_counts():
    claims=[C("a",["compact"],"high"), C("b",["compact","sdk"],"medium"),
            C("c",[],"low",page="docs/y.mdx")]
    s = agg.summarize(claims)
    assert s["total"] == 3
    assert s["domain_tag_counts"]["compact"] == 2
    assert s["domain_tag_counts"]["sdk"] == 1
    assert s["unclassified"] == 1
    assert s["multi_domain"] == 1
    assert s["severity"] == {"high":1,"medium":1,"low":1}
    assert s["by_page"]["docs/x.mdx"] == 2
