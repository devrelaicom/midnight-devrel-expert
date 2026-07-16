"""Merge per-batch claim files and produce the domain x severity summary."""
import json, glob, argparse
from collections import Counter
from . import lib

DOMAINS = ["compact","sdk","zkir","witness"]

def summarize(claims):
    tag=Counter(); sev=Counter(); by_page=Counter(); unc=0; multi=0
    for c in claims:
        doms=[d for d in (c.get("domains") or []) if d in DOMAINS]
        if not doms or c.get("unclassified") is True: unc+=1
        else:
            for d in doms: tag[d]+=1
            if len(doms)>=2: multi+=1
        sev[c.get("severity","?")] += 1
        by_page[(c.get("source") or {}).get("file","?")] += 1
    return {"total":len(claims),
            "domain_tag_counts":{d:tag[d] for d in DOMAINS},
            "unclassified":unc,"multi_domain":multi,
            "severity":{k:sev[k] for k in ("high","medium","low")},
            "by_page":dict(by_page)}

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims-glob", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    claims=[]
    for f in glob.glob(a.claims_glob): claims += json.load(open(f))
    json.dump({"generated_at":lib.iso_now(), **summarize(claims)}, open(a.out,"w"), indent=2)
    print(f"aggregated {len(claims)} claims -> {a.out}")

if __name__ == "__main__":
    main()
