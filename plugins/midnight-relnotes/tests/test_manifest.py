import scripts.manifest as man

def test_load_seed_drops_underscore_keys():
    seed = man.load_seed()
    assert not any(k.startswith("_") for k in seed)

def test_seed_maps_all_known_dirs():
    # The 8 dirs that were previously UNMAPPED must now be present.
    for name in ("compact-js", "compact-tools", "dapp-connector-api",
                 "dapp-examples-deprecated", "node", "onchain-runtime",
                 "proof-server", "wallet"):
        assert name in man.SEED, f"{name} missing from seed.json"

def test_every_seed_entry_has_required_fields():
    for name, cfg in man.SEED.items():
        assert "version_source" in cfg and "dynamiclist" in cfg, name
        assert "filename_scheme" in cfg, name

def test_wallet_api_uses_npm_semver_source():
    # The fix: the monorepo gh-release/empty-prefix mapping produced package-
    # scoped junk; the wallet API version comes from the npm package instead.
    assert man.SEED["midnight-wallet-api"]["version_source"] == "npm:@midnight-ntwrk/wallet-api"
    assert man.SEED["midnight-wallet-api"].get("tag_prefix", "") == ""

def test_build_applies_file_prefix_override():
    got = man.build(["docs/relnotes/dapp-examples-deprecated"])
    entry = got["items"][0]
    assert entry["file_prefix"] == "dapp-examples"          # not the dir basename
    assert entry["version_source"] == "ignored"

def test_build_defaults_file_prefix_to_basename():
    got = man.build(["docs/relnotes/compact-js"])
    assert got["items"][0]["file_prefix"] == "compact-js"

def test_build_skips_unknown_dirs():
    got = man.build(["docs/relnotes/not-a-real-item"])
    assert got["items"] == []

def test_unmapped_dirs_reports_new():
    mapped = ["docs/relnotes/midnight-js", "docs/relnotes/ledger"]
    actual = ["docs/relnotes/midnight-js", "docs/relnotes/ledger", "docs/relnotes/proof-server"]
    assert man.unmapped_dirs(mapped, actual) == ["docs/relnotes/proof-server"]

def test_unmapped_dirs_empty_when_all_mapped():
    dirs = ["docs/relnotes/midnight-js"]
    assert man.unmapped_dirs(dirs, dirs) == []
