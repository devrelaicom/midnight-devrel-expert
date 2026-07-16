"""Infer relevant repos for a docs page from its extracted tech/tool + repo-URL items."""
import re, json, argparse
from . import lib

# ordered (regex on lowercased tech, [repo names]) — see docs-drift-methodology skill for rationale
TECH_RULES = [
    (re.compile(r"compact"), ["compact"]),
    (re.compile(r"midnight\.?js|testkit-js"), ["midnight-js"]),
    (re.compile(r"zero-knowledge proof|zk-?snark|halo 2|proving key|verification key"), ["midnight-zk"]),
    (re.compile(r"\bledger\b|zswap|impact vm|transaction model|kernel|nullifier|merkle"), ["midnight-ledger"]),
    (re.compile(r"indexer"), ["midnight-indexer"]),
    (re.compile(r"wallet sdk|hd wallet"), ["midnight-wallet"]),
    (re.compile(r"dapp connector"), ["midnight-dapp-connector-api"]),
    (re.compile(r"midnight node|boot node|full node|rpc node|substrate|polkadot|consensus"), ["midnight-node"]),
]

def map_page(items, repo_names, known_urls=None):
    if known_urls is None:
        known_urls = {n: f"https://github.com/midnightntwrk/{n}" for n in repo_names}
    if "compact" in repo_names:
        known_urls["compact"] = "https://github.com/LFDT-Minokawa/compact"
    linked, inferred = set(), set()
    for x in items:
        if x.startswith("https://github.com/"):
            nm = x.rstrip("/").split("/")[-1]
            if nm in repo_names:
                linked.add(known_urls.get(nm, x))
        else:
            t = x.lower()
            for rx, names in TECH_RULES:
                if rx.search(t):
                    for nm in names:
                        if nm in repo_names:
                            inferred.add(known_urls[nm])
    inferred -= linked
    return {"linked": sorted(linked), "inferred": sorted(inferred)}

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--page-items", required=True, help="JSON {page:[items]}")
    ap.add_argument("--repos", required=True, help="repos.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    repos = json.load(open(a.repos))["repos"]
    names = {r["name"] for r in repos}
    urls = {r["name"]: r["url"] for r in repos}
    page_items = json.load(open(a.page_items))
    pages = {p: map_page(items, names, dict(urls)) for p, items in page_items.items()}
    json.dump({"generated_at": lib.iso_now(), "pages": pages}, open(a.out, "w"), indent=2)
    print(f"mapped {len(pages)} pages -> {a.out}")

if __name__ == "__main__":
    main()
