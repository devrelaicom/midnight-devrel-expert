# scripts/manifest.py
"""Build/refresh items.json; flag relnote dirs not yet mapped."""
import json, sys, os, argparse
from . import lib

# Seed mapping lives in scripts/seed.json (data, not code): one entry per
# docs/relnotes/<dir>, keyed by dir basename. file_prefix defaults to basename.
# Keys starting with "_" (e.g. "_comment") are documentation, not mappings.
SEED_PATH = os.path.join(os.path.dirname(__file__), "seed.json")

def load_seed(path=SEED_PATH):
    with open(path) as fh:
        return {k: v for k, v in json.load(fh).items() if not k.startswith("_")}

SEED = load_seed()

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
    if not os.path.isdir(root):
        raise SystemExit(f"no docs/relnotes under {a.docs_repo!r} — run from inside a midnight-docs checkout")
    actual = [f"docs/relnotes/{name}" for name in sorted(os.listdir(root))
              if os.path.isdir(os.path.join(root, name))]
    manifest = build(actual)
    json.dump(manifest, open(a.out, "w"), indent=2)
    mapped = [it["dir"] for it in manifest["items"]]
    missing = unmapped_dirs(mapped, actual)
    if missing:
        sys.stderr.write("UNMAPPED (add to scripts/seed.json): " + ", ".join(missing) + "\n")
    print(f"{len(manifest['items'])} items -> {a.out}")

if __name__ == "__main__":
    main()
