from datetime import datetime, timezone
import scripts.lib as lib

def test_parse_iso_handles_z_and_offset():
    assert lib.parse_iso("2026-07-16T10:00:00Z") == datetime(2026,7,16,10,0,tzinfo=timezone.utc)
    assert lib.parse_iso("2026-07-16T10:00:00+00:00").tzinfo is not None

def test_is_cache_fresh_boundary():
    now = datetime(2026,7,16,0,0,tzinfo=timezone.utc)
    assert lib.is_cache_fresh("2026-07-02T00:00:00Z", 14, now) is True    # exactly 14 days
    assert lib.is_cache_fresh("2026-07-01T23:59:59Z", 14, now) is False   # just over 14 days

def test_slugify():
    assert lib.slugify("Fix: persistentHash returns Bytes<32>!") == "fix-persistenthash-returns-bytes-32"

def test_state_dir_creates(tmp_path):
    p = lib.state_dir(str(tmp_path), "midnightntwrk")
    assert p.is_dir() and p.name == "midnightntwrk"
