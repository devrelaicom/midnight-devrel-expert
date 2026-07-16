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

# ---- thin I/O shell (not unit-tested) ----
def _npm_entries(pkg):
    versions = json.loads(subprocess.run(["npm", "view", pkg, "versions", "--json"],
        capture_output=True, text=True, check=True).stdout or "[]")
    if isinstance(versions, str):
        versions = [versions]
    return [{"version": v, "prerelease": lib.is_prerelease(v), "published_at": ""} for v in versions]

def _gh_entries(repo, prefix):
    raw = subprocess.run(["gh", "release", "list", "--repo", repo, "-L", "100",
        "--json", "tagName,isPrerelease,publishedAt"], capture_output=True, text=True, check=True).stdout
    out = []
    for r in json.loads(raw or "[]"):
        out.append({"version": lib.strip_prefix(r["tagName"], prefix),
                    "prerelease": bool(r["isPrerelease"]), "published_at": r.get("publishedAt", "")})
    return out

def resolve(item_cfg):
    src = item_cfg["version_source"]
    if src.startswith("npm:"):
        entries = _npm_entries(src[len("npm:"):])
    else:
        entries = _gh_entries(item_cfg["repo"], item_cfg.get("tag_prefix", ""))
    return select_versions(entries)

def main(argv=None):
    argv = argv or sys.argv[1:]
    print(json.dumps(resolve(json.loads(argv[0]))))

if __name__ == "__main__":
    main()
