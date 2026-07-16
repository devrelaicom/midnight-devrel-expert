import scripts.build_map as bm

NAMES = {"midnight-node","midnight-ledger","compact","midnight-indexer"}

def test_linked_kept_only_if_repo_known():
    items = ["Midnight Node","https://github.com/midnightntwrk/midnight-node",
             "https://github.com/midnightntwrk/proof-server"]  # proof-server not in NAMES
    m = bm.map_page(items, NAMES)
    assert "https://github.com/midnightntwrk/midnight-node" in m["linked"]
    assert all("proof-server" not in u for u in m["linked"])

def test_inferred_from_tech_and_deduped_against_linked():
    items = ["Ledger","Zswap","https://github.com/midnightntwrk/midnight-ledger"]
    m = bm.map_page(items, NAMES)
    # ledger is linked, so it must NOT also appear in inferred
    assert "https://github.com/midnightntwrk/midnight-ledger" in m["linked"]
    assert "https://github.com/midnightntwrk/midnight-ledger" not in m["inferred"]

def test_compact_tech_infers_compact_repo():
    m = bm.map_page(["Compact compiler (compactc)"], NAMES)
    assert any(u.endswith("/compact") for u in m["inferred"])
