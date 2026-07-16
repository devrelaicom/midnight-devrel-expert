"""Pure semver + relnote-filename helpers. Stdlib only, no I/O."""
import re
from datetime import datetime, timezone

_PRERELEASE_RE = re.compile(r"\d+(?:\.\d+)*-")  # a release core followed by '-<ident>'

def strip_prefix(tag: str, prefix: str) -> str:
    return tag[len(prefix):] if prefix and tag.startswith(prefix) else tag

def is_prerelease(raw: str) -> bool:
    return bool(_PRERELEASE_RE.search(raw.strip()))

def release_tuple(raw: str) -> tuple:
    core = raw.strip().lstrip("vV").split("-", 1)[0]
    parts = []
    for p in core.split("."):
        m = re.match(r"\d+", p)
        parts.append(int(m.group()) if m else 0)
    return tuple(parts)

def cmp_release(a: str, b: str) -> int:
    ta, tb = release_tuple(a), release_tuple(b)
    n = max(len(ta), len(tb))
    ta += (0,) * (n - len(ta))
    tb += (0,) * (n - len(tb))
    return (ta > tb) - (ta < tb)

def version_to_filename(file_prefix: str, version: str, scheme: str) -> str:
    v = version.strip().lstrip("vV")
    if scheme == "dash":
        v = v.replace(".", "-")
    return f"{file_prefix}-{v}"

def filename_to_version(filename: str, file_prefix: str) -> str | None:
    stem = filename[:-4] if filename.endswith(".mdx") else filename
    lead = f"{file_prefix}-"
    if not stem.startswith(lead):
        return None
    rest = stem[len(lead):]
    # dash scheme stores dots as dashes; dotted keeps dots. Detect: if it has dots, it's dotted.
    return rest if "." in rest else rest.replace("-", ".")

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()
