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
