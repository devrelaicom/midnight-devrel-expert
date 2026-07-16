"""Heuristic severity = blast radius if the claim is stale/wrong (not P(wrong))."""
import re, json, argparse, glob
from . import lib

DOMAINS = {"compact","sdk","zkir","witness"}
HIGH = [
    ("type-expr",   re.compile(r"\b(Bytes|Uint|Vector|Opaque|Maybe|Either|Field|Boolean)\s*<|<\s*[A-Z]\w*\s*>")),
    ("fn-sig",      re.compile(r"`[^`]*\b[A-Za-z_]\w*\s*\([^`]*`|->|\breturn type\b|\bsignature\b|\breturns?\b")),
    ("import-pkg",  re.compile(r"@midnight-ntwrk|\bimport\b|\bpackage\b")),
    ("keyword",     re.compile(r"\bkeyword\b|\bsyntax\b|\boperator\b|\bpragma\b|\bmust be\b|\bis required\b")),
    ("error-code",  re.compile(r"\berror code\b|\bstatus code\b|\bexit code\b|\bfails? to compile\b|\bcompile[- ]time\b")),
    ("security",    re.compile(r"\bdisclose\b|\bwitness\b|\bnullifier\b|\bsealed\b|\bpublicly visible\b|persistent(Hash|Commit)|transient(Hash|Commit)")),
    ("cli",         re.compile(r"--[a-z][\w-]+|\bsubcommand\b")),
    ("zkir",        re.compile(r"\bopcode\b|\bwraps? modulo\b|constrain_bits|declare_pub_input|private_input")),
]
LOW = re.compile(r"\bis an?\b|\brefers to\b|\bconsists of\b|\barchitecture\b|\bdesigned to\b|\benables?\b|\bprovides?\b|\bconcept\b|\boverview\b|\bconsensus\b")
CODE_TOKEN = re.compile(r"`[^`]+`|\b[a-z][a-zA-Z0-9]*[A-Z]\w*\b|\b\w+_\w+\b|\(\)")

def severity_for(claim_text, domains, is_unclassified):
    for name, pat in HIGH:
        if pat.search(claim_text):
            return "high", name
    in_code_domain = bool(set(domains) & DOMAINS)
    has_code = bool(CODE_TOKEN.search(claim_text))
    has_concept = bool(LOW.search(claim_text))
    if has_code and (in_code_domain or not has_concept):
        return "medium", "named-construct"
    if has_concept or is_unclassified:
        return "low", "conceptual"
    return ("medium","code-domain-default") if in_code_domain else ("low","default-soft")

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims-glob", required=True, help="glob of claim batch JSON files")
    a = ap.parse_args(argv)
    for f in glob.glob(a.claims_glob):
        data = json.load(open(f))
        for c in data:
            doms = [d for d in (c.get("domains") or []) if d in DOMAINS]
            unc = c.get("unclassified") is True or not doms
            c["severity"], c["severity_signal"] = severity_for(c["claim"], doms, unc)
        json.dump(data, open(f,"w"), indent=2, ensure_ascii=False)
    print("severity applied")

if __name__ == "__main__":
    main()
