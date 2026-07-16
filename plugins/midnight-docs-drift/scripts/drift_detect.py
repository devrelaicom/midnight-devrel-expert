"""Drift = doc mtime older than any mapped repo's last publish."""
import json, subprocess, argparse
from . import lib

def resolve_publish(release_pub, head_date):
    if release_pub:
        return release_pub, "release"
    if head_date:
        return head_date, "push"
    return None, "unknown"

def drift_for_page(doc_modified, repo_pubs):
    dm = lib.parse_iso(doc_modified)
    out = []
    for repo,(pub,method) in repo_pubs.items():
        if pub and lib.parse_iso(pub) > dm:
            out.append({"repo":repo,"published":pub,"method":method})
    return sorted(out, key=lambda d: d["published"], reverse=True)

# ---- thin I/O shell ----
def _ensure_full_history(repo_path):
    shallow = subprocess.run(["git","-C",repo_path,"rev-parse","--is-shallow-repository"],
        capture_output=True,text=True).stdout.strip()
    if shallow == "true":
        subprocess.run(["git","-C",repo_path,"fetch","--unshallow"], capture_output=True)

def _file_mtime(repo_path, rel):
    return subprocess.run(["git","-C",repo_path,"log","-1","--format=%cI","--",rel],
        capture_output=True,text=True).stdout.strip() or None

def _repo_publish(url):
    owner,name = url.rstrip("/").split("/")[-2:]
    rel = subprocess.run(["gh","api",f"repos/{owner}/{name}/releases/latest","--jq",".published_at"],
        capture_output=True,text=True)
    release = rel.stdout.strip() if rel.returncode==0 and rel.stdout.strip() not in ("","null") else None
    branch = subprocess.run(["gh","api",f"repos/{owner}/{name}","--jq",".default_branch"],
        capture_output=True,text=True).stdout.strip() or "main"
    head = subprocess.run(["gh","api",f"repos/{owner}/{name}/commits/{branch}","--jq",".commit.committer.date"],
        capture_output=True,text=True).stdout.strip() or None
    return resolve_publish(release, head)

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-repo", required=True)
    ap.add_argument("--map", required=True, help="docs-repo-map.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    _ensure_full_history(a.docs_repo)
    dmap = json.load(open(a.map))["pages"]
    pub_cache = {}
    stale = {}
    for page, m in dmap.items():
        urls = m.get("linked",[]) + m.get("inferred",[])
        pubs = {}
        for u in urls:
            if u not in pub_cache: pub_cache[u] = _repo_publish(u)
            pubs[u] = pub_cache[u]
        mtime = _file_mtime(a.docs_repo, page)
        if not mtime: continue
        behind = drift_for_page(mtime, pubs)
        if behind:
            stale[page] = {"doc_modified":mtime, "behind":behind}
    json.dump({"generated_at":lib.iso_now(),"stale_pages":stale}, open(a.out,"w"), indent=2)
    print(f"{len(stale)} drifted pages -> {a.out}")

if __name__ == "__main__":
    main()
