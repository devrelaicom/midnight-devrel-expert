"""Pure semver + relnote-filename helpers. Stdlib only, no I/O."""
import re
from datetime import datetime, timezone

try:  # tomllib is stdlib on Python >=3.11; regex fallback covers older runtimes.
    import tomllib as _tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised only on <3.11
    _tomllib = None

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
    # NOTE: the dash scheme assumes release-core-only versions (e.g. 4-1-1). A
    # prerelease filename (4-0-0-beta-6) would round-trip to "4.0.0.beta.6" —
    # relnote filenames are stable releases only today, so this stays latent.
    return rest if "." in rest else rest.replace("-", ".")

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def stamp_utc() -> str:
    """Filesystem-safe UTC timestamp for dashboard filenames: YYYYMMDD-HHMMSS."""
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

# ---- Cargo.toml version extraction (crates:* fallback) --------------------
# A crate's version can be a literal (`version = "3.1.0"`) or inherited from the
# workspace (`version.workspace = true`). WORKSPACE_INHERITED marks the latter so
# the caller knows to look the version up in the workspace root's Cargo.toml.
WORKSPACE_INHERITED = "\x00workspace-inherited"  # sentinel, never a real version

def _section_scan(text, section, key_re):
    """Yield the first regex match for `key_re` inside the `[section]` table,
    handling both bare `[table]` headers and comment-stripped lines."""
    cur = None
    for line in text.splitlines():
        s = line.split("#", 1)[0].strip()  # Cargo values never contain '#'
        if s.startswith("[") and s.endswith("]"):
            cur = s[1:-1].strip()
            continue
        if cur == section:
            m = key_re.match(s)
            if m:
                return m
    return None

_VER_LITERAL = re.compile(r'version\s*=\s*"([^"]+)"')
_VER_WS_DOTTED = re.compile(r'version\.workspace\s*=\s*true')
_VER_WS_INLINE = re.compile(r'version\s*=\s*\{[^}]*workspace\s*=\s*true')
_PKG_VER_DOTTED = re.compile(r'package\.version\s*=\s*"([^"]+)"')

def package_version(toml_text: str):
    """Version declared under `[package]`: a literal string, WORKSPACE_INHERITED
    when it defers to the workspace, or None when absent/unparseable."""
    if _tomllib is not None:
        try:
            v = (_tomllib.loads(toml_text).get("package") or {}).get("version")
            if isinstance(v, str):
                return v
            if isinstance(v, dict) and v.get("workspace") is True:
                return WORKSPACE_INHERITED
            return None
        except Exception:
            pass
    m = _section_scan(toml_text, "package", _VER_LITERAL)
    if m:
        return m.group(1)
    if _section_scan(toml_text, "package", _VER_WS_DOTTED) or \
       _section_scan(toml_text, "package", _VER_WS_INLINE):
        return WORKSPACE_INHERITED
    return None

def workspace_package_version(toml_text: str):
    """Version shared across a workspace — either `[workspace.package] version`
    or the dotted `[workspace] package.version` form. None when absent."""
    if _tomllib is not None:
        try:
            ws = _tomllib.loads(toml_text).get("workspace") or {}
            v = (ws.get("package") or {}).get("version")
            return v if isinstance(v, str) else None
        except Exception:
            pass
    m = _section_scan(toml_text, "workspace.package", _VER_LITERAL)
    if m:
        return m.group(1)
    m = _section_scan(toml_text, "workspace", _PKG_VER_DOTTED)
    return m.group(1) if m else None

def crate_version(package_toml: str, workspace_toml: str | None = None):
    """Resolve a crate's version from its Cargo.toml, following
    `version.workspace = true` into the workspace root when `workspace_toml` is
    given. Returns the version string, or None when it cannot be resolved."""
    v = package_version(package_toml)
    if v == WORKSPACE_INHERITED:
        return workspace_package_version(workspace_toml) if workspace_toml else None
    return v
