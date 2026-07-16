import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))

def is_cache_fresh(generated_at: str, ttl_days: int, now=None) -> bool:
    now = now or datetime.now(timezone.utc)
    return (now - parse_iso(generated_at)) <= timedelta(days=ttl_days)

def state_dir(plugin_data: str, *parts: str) -> Path:
    p = Path(plugin_data).joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p

def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)
