import scripts.lib as lib

def test_strip_prefix():
    assert lib.strip_prefix("v4.1.1", "v") == "4.1.1"
    assert lib.strip_prefix("ledger-8.1.0", "ledger-") == "8.1.0"
    assert lib.strip_prefix("compactc-v0.31.1", "compactc-v") == "0.31.1"
    assert lib.strip_prefix("4.1.1", "v") == "4.1.1"  # prefix absent → unchanged

def test_is_prerelease():
    assert lib.is_prerelease("5.0.0-beta.6") is True
    assert lib.is_prerelease("5.0.0-alpha.1") is True
    assert lib.is_prerelease("0.33.0-rc.2") is True
    assert lib.is_prerelease("4.0.2-0-pre.2a895cf0") is True
    assert lib.is_prerelease("4.1.1") is False
    assert lib.is_prerelease("8.1.0") is False

def test_release_tuple():
    assert lib.release_tuple("4.1.1") == (4, 1, 1)
    assert lib.release_tuple("5.0.0-beta.6") == (5, 0, 0)
    assert lib.release_tuple("v0.31.1") == (0, 31, 1)

def test_cmp_release():
    assert lib.cmp_release("4.1.1", "4.1.0") == 1
    assert lib.cmp_release("4.0.4", "4.1.1") == -1
    assert lib.cmp_release("8.1.0", "8.1") == 0   # padding
    assert lib.cmp_release("5.0.0-beta.6", "5.0.0") == 0  # prerelease ignored for release compare

def test_version_to_filename():
    assert lib.version_to_filename("midnight-js", "4.1.1", "dash") == "midnight-js-4-1-1"
    assert lib.version_to_filename("toolchain", "0.31.0", "dotted") == "toolchain-0.31.0"

def test_filename_to_version():
    assert lib.filename_to_version("midnight-js-4-1-1.mdx", "midnight-js") == "4.1.1"
    assert lib.filename_to_version("toolchain-0.31.0.mdx", "toolchain") == "0.31.0"
    assert lib.filename_to_version("ledger-8-1-0.mdx", "midnight-js") is None

def test_stamp_utc_is_filesystem_safe():
    s = lib.stamp_utc()
    import re
    assert re.fullmatch(r"\d{8}-\d{6}", s)  # YYYYMMDD-HHMMSS, no ':' or spaces

# ---- Cargo.toml version extraction (shapes taken from the real crates) ----
# onchain-runtime/Cargo.toml: a literal version.
ONCHAIN_TOML = '[package]\nname = "midnight-onchain-runtime"\nversion = "3.1.0"\n\n[features]\n'
# proof-server/Cargo.toml: inherits from the workspace.
PROOF_TOML = '[package]\nname = "midnight-proof-server"\nversion.workspace = true\n\n[dependencies]\n'
# midnight-ledger workspace root: dotted `[workspace] package.version` form.
WS_ROOT_TOML = '[workspace]\nresolver = "2"\npackage.version = "8.2.0-rc.1"\n\n[workspace.dependencies]\n'
WS_ROOT_SECTION_TOML = '[workspace.package]\nversion = "8.2.0-rc.1"\nedition = "2021"\n'

def test_package_version_literal():
    assert lib.package_version(ONCHAIN_TOML) == "3.1.0"

def test_package_version_workspace_inherited():
    assert lib.package_version(PROOF_TOML) == lib.WORKSPACE_INHERITED

def test_package_version_inline_workspace_table():
    assert lib.package_version('[package]\nversion = { workspace = true }\n') == lib.WORKSPACE_INHERITED

def test_workspace_package_version_both_forms():
    assert lib.workspace_package_version(WS_ROOT_TOML) == "8.2.0-rc.1"        # dotted
    assert lib.workspace_package_version(WS_ROOT_SECTION_TOML) == "8.2.0-rc.1"  # sectioned

def test_crate_version_literal_needs_no_workspace():
    assert lib.crate_version(ONCHAIN_TOML) == "3.1.0"

def test_crate_version_follows_workspace_inheritance():
    assert lib.crate_version(PROOF_TOML, WS_ROOT_TOML) == "8.2.0-rc.1"

def test_crate_version_unresolvable_without_workspace():
    # Inherited version but no workspace toml supplied → cannot resolve.
    assert lib.crate_version(PROOF_TOML) is None
    # No version at all → None.
    assert lib.crate_version('[package]\nname = "x"\n') is None
