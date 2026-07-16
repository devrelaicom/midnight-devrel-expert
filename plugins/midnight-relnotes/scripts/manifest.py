# scripts/manifest.py
"""Build/refresh items.json; flag relnote dirs not yet mapped."""
import json, sys, os, argparse
from . import lib

# Seed mapping. Extend as new items are added. file_prefix defaults to dir basename.
SEED = {
    "midnight-js": {"repo": "midnightntwrk/midnight-js", "version_source": "npm:@midnight-ntwrk/midnight-js",
                    "tag_prefix": "v", "filename_scheme": "dash", "dynamiclist": "src/components/DynamicListMidnightJS.js"},
    "ledger": {"repo": "midnightntwrk/midnight-ledger", "version_source": "gh-release",
               "tag_prefix": "ledger-", "filename_scheme": "dash", "dynamiclist": "src/components/DynamicListLedger.js"},
    "midnight-indexer": {"repo": "midnightntwrk/midnight-indexer", "version_source": "gh-release",
                         "tag_prefix": "midnight-indexer-", "filename_scheme": "dash", "dynamiclist": "src/components/DynamicListMidnightIndexer.js"},
    "midnight-wallet-api": {"repo": "midnightntwrk/midnight-wallet", "version_source": "gh-release",
                            "tag_prefix": "", "filename_scheme": "dash", "dynamiclist": "src/components/DynamicListMidnightWalletAPI.js"},
    "compact": {"repo": "LFDT-Minokawa/compact", "version_source": "gh-release",
                "tag_prefix": "compactc-v", "filename_scheme": "dotted", "dynamiclist": "src/components/DynamicListCompact.js",
                "file_prefix": "toolchain"},
}

def unmapped_dirs(manifest_dirs, actual_dirs):
    mapped = set(manifest_dirs)
    return sorted(d for d in actual_dirs if d not in mapped)

def build(actual_dirs):
    items = []
    for d in sorted(actual_dirs):
        base = os.path.basename(d.rstrip("/"))
        cfg = SEED.get(base)
        if not cfg:
            continue
        entry = {"dir": d, "file_prefix": cfg.get("file_prefix", base), "status_vocab": ["LATEST", "SUPPORTED", "DEPRECATED"]}
        entry.update({k: v for k, v in cfg.items() if k != "file_prefix"})
        items.append(entry)
    return {"generated_at": lib.iso_now(), "items": items}

# ---- thin shell ----
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["refresh"])
    ap.add_argument("--docs-repo", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    root = os.path.join(a.docs_repo, "docs", "relnotes")
    actual = [f"docs/relnotes/{name}" for name in sorted(os.listdir(root))
              if os.path.isdir(os.path.join(root, name))]
    manifest = build(actual)
    json.dump(manifest, open(a.out, "w"), indent=2)
    mapped = [it["dir"] for it in manifest["items"]]
    missing = unmapped_dirs(mapped, actual)
    if missing:
        sys.stderr.write("UNMAPPED (add to SEED): " + ", ".join(missing) + "\n")
    print(f"{len(manifest['items'])} items -> {a.out}")

if __name__ == "__main__":
    main()
