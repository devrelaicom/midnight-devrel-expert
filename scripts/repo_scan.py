"""Deterministic core + thin gh shell for the active-repo list."""
import json, subprocess, argparse, sys
from . import lib

SCAFFOLD = {".envrc",".github","CHANGELOG.md","CODEOWNERS","CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md","LICENSE","README.md","SECURITY.md","renovate.json"}

def is_scaffold_only(entries) -> bool:
    e = set(entries)
    return bool(e) and e <= SCAFFOLD or e == {"README.md"} or len(e) <= 1

def is_active(node: dict, since_iso: str) -> bool:
    if node.get("isArchived") or node.get("isEmpty"):
        return False
    last = node.get("lastCommit")
    if not last or lib.parse_iso(last) < lib.parse_iso(since_iso):
        return False
    if is_scaffold_only(node.get("topLevelEntries") or []):
        return False
    return True

def build_repo_list(nodes, since_iso, extra):
    recs = [{"name":n["name"],"url":n["url"],"last_commit":n["lastCommit"],
             "description":n.get("description") or "","private":bool(n.get("isPrivate"))}
            for n in nodes if is_active(n, since_iso)]
    recs += list(extra)
    return sorted(recs, key=lambda r: r["last_commit"], reverse=True)

# ---- thin I/O shell (not unit-tested; exercised by the command dry-run) ----
GQL = """query($org:String!,$endCursor:String){organization(login:$org){repositories(first:50,after:$endCursor,orderBy:{field:PUSHED_AT,direction:DESC}){pageInfo{hasNextPage endCursor} nodes{name url isArchived isEmpty isPrivate description pushedAt defaultBranchRef{target{... on Commit{committedDate tree{entries{name}}}}}}}}}"""

def _fetch_org(org):
    # entries[]? guards repos with a null defaultBranchRef (empty/branchless repos exist in
    # the org) so jq doesn't error "Cannot iterate over null" and abort the whole --paginate run.
    raw = subprocess.run(["gh","api","graphql","--paginate","-f",f"org={org}",
        "-f",f"query={GQL}","--jq",
        ".data.organization.repositories.nodes[]|{name,url,isArchived,isEmpty,isPrivate,description,pushedAt,lastCommit:.defaultBranchRef.target.committedDate,topLevelEntries:[.defaultBranchRef.target.tree.entries[]?.name]}"],
        capture_output=True, text=True, check=True).stdout.strip().splitlines()
    return [json.loads(l) for l in raw if l]

def _fetch_extra(spec):  # spec "OWNER/NAME"
    o,n = spec.split("/")
    d = json.loads(subprocess.run(["gh","api",f"repos/{o}/{n}","--jq",
        "{name:.name,url:.html_url,description:.description,private:.private,default:.default_branch}"],
        capture_output=True,text=True,check=True).stdout)
    lc = subprocess.run(["gh","api",f"repos/{o}/{n}/commits/{d['default']}","--jq",".commit.committer.date"],
        capture_output=True,text=True,check=True).stdout.strip()
    return {"name":d["name"],"url":d["url"],"last_commit":lc,"description":d.get("description") or "","private":d["private"]}

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", default="midnightntwrk")
    ap.add_argument("--since", required=True, help="ISO cutoff")
    ap.add_argument("--extra-repo", action="append", default=["LFDT-Minokawa/compact"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    extra = [_fetch_extra(s) for s in a.extra_repo]
    repos = build_repo_list(_fetch_org(a.org), a.since, extra)
    json.dump({"generated_at":lib.iso_now(),"since":a.since,"org":a.org,"repos":repos},
              open(a.out,"w"), indent=2)
    print(f"{len(repos)} active repos -> {a.out}")

if __name__ == "__main__":
    main()
