"""Latest stable + prerelease per item. Pure core + gh/npm/cargo shell."""
import json, subprocess, sys, shutil, base64, re
from functools import cmp_to_key
from . import lib

def select_versions(entries):
    stable = [e for e in entries if not e["prerelease"]]
    pre = [e for e in entries if e["prerelease"]]
    stable_sorted = sorted(stable, key=cmp_to_key(lambda a, b: lib.cmp_release(a["version"], b["version"])))
    all_stable = [e["version"] for e in stable_sorted]
    latest_stable = all_stable[-1] if all_stable else None
    latest_pre = max(pre, key=lambda e: e["published_at"])["version"] if pre else None
    return {"stable": latest_stable, "prerelease": latest_pre, "all_stable": all_stable}

# Fallback for sources that produce no resolvable version. `ignored` is
# deprecated and intentionally not tracked; a `crates:*` item lands here only
# when neither cargo nor its Cargo.toml yields a version. Anything unrecognised
# is treated the same way rather than silently falling through to a GitHub-release
# lookup.
UNTRACKED = {"stable": None, "prerelease": None, "all_stable": [], "tracked": False}

def is_tracked_source(version_source):
    return (version_source.startswith("npm:") or version_source == "gh-release"
            or version_source.startswith("crates:"))

def gh_rows_to_entries(rows, prefix):
    """Convert `gh release list` rows to entries, keeping only tags in this
    prefix's stream. Monorepos (e.g. midnightntwrk/compact ships both
    `compact-v*` and `compactc-v*`) tag several unrelated components, so a bare
    strip would drag other streams — and dev/branch tags — into the result."""
    out = []
    for r in rows:
        tag = r["tagName"]
        if prefix and not tag.startswith(prefix):
            continue
        out.append({"version": lib.strip_prefix(tag, prefix),
                    "prerelease": bool(r["isPrerelease"]), "published_at": r.get("publishedAt", "")})
    return out

# ---- thin I/O shell (not unit-tested) ----
def _run(cmd):
    """Run a resolver command; on failure raise a clean one-liner instead of a
    CalledProcessError traceback, so one unresolvable item degrades to an ERROR
    row rather than aborting the whole scout batch."""
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(f"resolve failed ({cmd[0]} exit {p.returncode}): "
                         f"{(p.stderr or p.stdout).strip().splitlines()[-1:] or ['no output']}")
    return p.stdout

def _npm_entries(pkg):
    versions = json.loads(_run(["npm", "view", pkg, "versions", "--json"]) or "[]")
    if isinstance(versions, str):
        versions = [versions]
    # npm returns versions in ascending publish order; encode that order into
    # published_at (zero-padded index) so select_versions picks the newest prerelease.
    return [{"version": v, "prerelease": lib.is_prerelease(v), "published_at": str(i).zfill(9)}
            for i, v in enumerate(versions)]

def _gh_entries(repo, prefix):
    # -L pulls the most-recent N releases. A monorepo with a busy stream and a
    # quiet one (compact-v* vs compactc-v*) could push the quiet stream's newest
    # stable past this window; keep N well above any single repo's release count.
    raw = _run(["gh", "release", "list", "--repo", repo, "-L", "300",
        "--json", "tagName,isPrerelease,publishedAt"])
    return gh_rows_to_entries(json.loads(raw or "[]"), prefix)

def _run_soft(cmd):
    """Run a resolver command, returning stdout on success or None on any
    failure. The crates path chains fallbacks (cargo -> Cargo.toml -> untracked),
    so a miss must degrade quietly rather than abort like `_run`."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
    except (OSError, ValueError):
        return None
    return p.stdout if p.returncode == 0 else None

_CARGO_LINE = re.compile(r'^([A-Za-z0-9_.+-]+)\s*=\s*"([^"]+)"')

def _cargo_crate_version(crate):
    """Primary crates resolver: `cargo search`, gated on cargo being installed.
    Internal midnight crates are usually unpublished, so this frequently returns
    None and the Cargo.toml fallback takes over."""
    if shutil.which("cargo") is None:
        return None
    out = _run_soft(["cargo", "search", crate, "--limit", "20"])
    if not out:
        return None
    for line in out.splitlines():
        m = _CARGO_LINE.match(line.strip())
        if m and m.group(1) == crate:  # exact name, not a substring neighbour
            return m.group(2)
    return None

def _gh_file(repo, path, ref):
    """Fetch a repo file's text at a ref via the GitHub contents API (base64).
    Returns None on any failure so the caller can degrade to untracked."""
    out = _run_soft(["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "--jq", ".content"])
    if not out:
        return None
    try:  # b64decode(validate=False) drops the newlines GitHub wraps content in.
        return base64.b64decode(out.strip()).decode("utf-8", "replace")
    except Exception:
        return None

def _crate_version(cfg, crate):
    """Resolve a crate's current version: cargo/crates.io first, then the crate's
    Cargo.toml at source_path@source_ref (following version.workspace = true into
    the workspace root). Returns None when nothing resolves — never fabricates."""
    ver = _cargo_crate_version(crate)
    if ver:
        return ver
    repo, path, ref = cfg.get("repo"), cfg.get("source_path"), cfg.get("source_ref")
    if not (repo and path and ref):
        return None
    pkg_toml = _gh_file(repo, f"{path}/Cargo.toml", ref)
    if not pkg_toml:
        return None
    pv = lib.package_version(pkg_toml)
    if pv == lib.WORKSPACE_INHERITED:
        ws_toml = _gh_file(repo, "Cargo.toml", ref)
        pv = lib.workspace_package_version(ws_toml) if ws_toml else None
    return pv if isinstance(pv, str) and pv != lib.WORKSPACE_INHERITED else None

def resolve(item_cfg):
    src = item_cfg["version_source"]
    if src.startswith("npm:"):
        entries = _npm_entries(src[len("npm:"):])
    elif src == "gh-release":
        entries = _gh_entries(item_cfg["repo"], item_cfg.get("tag_prefix", ""))
    elif src.startswith("crates:"):
        ver = _crate_version(item_cfg, src[len("crates:"):])
        if not ver:  # cargo miss + no Cargo.toml version -> stay untracked
            return {**UNTRACKED, "version_source": src}
        entries = [{"version": ver, "prerelease": lib.is_prerelease(ver), "published_at": "0"}]
    else:
        # ignored / unknown — not resolvable to a clean version.
        return {**UNTRACKED, "version_source": src}
    result = select_versions(entries)
    result["tracked"] = True
    return result

def main(argv=None):
    argv = argv or sys.argv[1:]
    print(json.dumps(resolve(json.loads(argv[0]))))

if __name__ == "__main__":
    main()
