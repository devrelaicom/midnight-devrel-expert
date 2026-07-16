from datetime import datetime, timezone
import pytest
import scripts.lib as lib

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)

def test_parse_repo_bare():
    assert lib.parse_repo("midnightntwrk/midnight-docs") == "midnightntwrk/midnight-docs"

def test_parse_repo_url_forms():
    assert lib.parse_repo("https://github.com/foo/bar") == "foo/bar"
    assert lib.parse_repo("https://github.com/foo/bar/tree/main/x") == "foo/bar"
    assert lib.parse_repo("git@github.com:foo/bar.git") == "foo/bar"
    assert lib.parse_repo("github.com/foo/bar.git") == "foo/bar"

def test_parse_repo_rejects_garbage():
    for bad in ["", "just-a-name", "https://github.com/onlyowner"]:
        with pytest.raises(ValueError):
            lib.parse_repo(bad)

def test_resolve_since_relative():
    assert lib.resolve_since("2w", NOW) == "2026-07-02"
    assert lib.resolve_since("10d", NOW) == "2026-07-06"
    assert lib.resolve_since("3mo", NOW) == "2026-04-17"

def test_resolve_since_absolute_and_bad():
    assert lib.resolve_since("2026-01-05", NOW) == "2026-01-05"
    with pytest.raises(ValueError):
        lib.resolve_since("soon", NOW)

def test_days_between():
    assert lib.days_between("2026-07-06T00:00:00Z", NOW) == 10
