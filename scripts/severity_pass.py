"""Heuristic severity = blast radius if the claim is stale/wrong (not P(wrong))."""
import re, json, argparse, glob

DOMAINS = {"compact","sdk","zkir","witness"}

# A code marker: presence signals code-exactness (backtick span, package, call,
# snake_case, camelCase, or an opening generic like `<T`).
CODE_CONTEXT = re.compile(r"`[^`]+`|@midnight-ntwrk|[A-Za-z_]\w*\(|\b\w+_\w+\b|\b[a-z][a-zA-Z0-9]*[A-Z]\w*\b|<\s*[A-Z]")

# HIGH_STRICT: inherently code-exact — fire unconditionally.
HIGH_STRICT = [
    ("type-expr",  re.compile(r"\b(Bytes|Uint|Vector|Opaque|Maybe|Either|Field|Boolean)\s*<|<\s*[A-Z]\w*\s*>")),
    ("fn-call",    re.compile(r"`[^`]*\b[A-Za-z_]\w*\s*\([^`]*`")),
    ("import-pkg", re.compile(r"@midnight-ntwrk|\bimport\b|\bpackage\b")),
    ("error-code", re.compile(r"\berror code\b|\bstatus code\b|\bexit code\b|\bfails? to compile\b|\bcompile[- ]time\b")),
    ("cli",        re.compile(r"--[a-z][\w-]+|\bsubcommand\b")),
    ("zkir",       re.compile(r"\bopcode\b|\bwraps? modulo\b|constrain_bits|declare_pub_input|private_input")),
    ("primitive",  re.compile(r"persistent(Hash|Commit)|transient(Hash|Commit)|\bdisclose\s*\(")),
    ("pragma",     re.compile(r"\bpragma\b")),
]
# HIGH_CONTEXTUAL: bare words that are only code-exact when a code marker co-occurs.
HIGH_CONTEXTUAL = [
    ("signature", re.compile(r"\breturns?\b|\breturn type\b|\bsignature\b")),
    ("keyword",   re.compile(r"\bkeyword\b|\bsyntax\b|\boperator\b")),
    ("security",  re.compile(r"\bwitness\b|\bnullifier\b|\bsealed\b|\bdisclose\b|\bpublicly visible\b")),
]
LOW = re.compile(r"\bis an?\b|\brefers to\b|\bconsists of\b|\barchitecture\b|\bdesigned to\b|\benables?\b|\bprovides?\b|\bconcept\b|\boverview\b|\bconsensus\b")
CODE_TOKEN = re.compile(r"`[^`]+`|\b[a-z][a-zA-Z0-9]*[A-Z]\w*\b|\b\w+_\w+\b|\(\)")

def severity_for(claim_text, domains, is_unclassified):
    for name, pat in HIGH_STRICT:
        if pat.search(claim_text):
            return "high", name
    has_ctx = bool(CODE_CONTEXT.search(claim_text))
    for name, pat in HIGH_CONTEXTUAL:
        if pat.search(claim_text) and has_ctx:
            return "high", name
    # A claim outside the four verifiable domains caps at low unless a HIGH code-exact fact fired above.
    if is_unclassified:
        return "low", "unclassified"
    in_code_domain = bool(set(domains) & DOMAINS)
    if CODE_TOKEN.search(claim_text):
        return "medium", "named-construct"
    if LOW.search(claim_text):
        return "low", "conceptual"
    return ("medium", "code-domain-default") if in_code_domain else ("low", "default-soft")

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
