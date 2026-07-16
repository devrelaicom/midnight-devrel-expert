"""Latest stable + prerelease per item. Pure core + gh/npm shell."""
import json, subprocess, sys
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

# Sources we cannot resolve to a clean semver stream today. `crates:<crate>` is
# recorded so a future crates resolver can pick it up; `ignored` is deprecated
# and intentionally not tracked. Anything unrecognised is treated the same way
# rather than silently falling through to a GitHub-release lookup.
UNTRACKED = {"stable": None, "prerelease": None, "all_stable": [], "tracked": False}

def is_tracked_source(version_source):
    return version_source.startswith("npm:") or version_source == "gh-release"

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

def resolve(item_cfg):
    src = item_cfg["version_source"]
    if src.startswith("npm:"):
        entries = _npm_entries(src[len("npm:"):])
    elif src == "gh-release":
        entries = _gh_entries(item_cfg["repo"], item_cfg.get("tag_prefix", ""))
    else:
        # crates:* / ignored / unknown — not resolvable to a clean version today.
        return {**UNTRACKED, "version_source": src}
    result = select_versions(entries)
    result["tracked"] = True
    return result

def main(argv=None):
    argv = argv or sys.argv[1:]
    print(json.dumps(resolve(json.loads(argv[0]))))

if __name__ == "__main__":
    main()
