"""Shared helpers for the pr_report pipeline (pure, unit-tested)."""
import re
from datetime import datetime, timezone, timedelta

_GITHUB = re.compile(r"^(?:https?://)?(?:www\.)?github\.com/", re.I)
_SSH = re.compile(r"^git@github\.com:", re.I)
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))

def parse_repo(s: str) -> str:
    t = (s or "").strip()
    t = _GITHUB.sub("", t)
    t = _SSH.sub("", t)
    t = t.split("?", 1)[0].split("#", 1)[0]
    parts = [p for p in t.split("/") if p]
    if len(parts) < 2:
        raise ValueError("cannot parse repo from %r" % (s,))
    owner, name = parts[0], parts[1]
    if name.endswith(".git"):
        name = name[:-4]
    repo = "%s/%s" % (owner, name)
    if not _REPO.match(repo):
        raise ValueError("invalid repo %r from %r" % (repo, s))
    return repo

def resolve_since(timeframe: str, now=None) -> str:
    now = now or datetime.now(timezone.utc)
    t = (timeframe or "").strip().lower()
    m = re.fullmatch(r"(\d+)(d|w|mo)", t)
    if m:
        n = int(m.group(1))
        days = {"d": 1, "w": 7, "mo": 30}[m.group(2)] * n
        return (now - timedelta(days=days)).date().isoformat()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        datetime.strptime(t, "%Y-%m-%d")  # validate
        return t
    raise ValueError("cannot parse timeframe %r (use Nd/Nw/Nmo or YYYY-MM-DD)" % (timeframe,))

def days_between(earlier_iso: str, now) -> int:
    return max(0, int((now - parse_iso(earlier_iso)).total_seconds() // 86400))
