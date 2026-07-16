# /update-drifted-docs Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Claude Code plugin in this repo whose `/update-drifted-docs` command detects drifted `midnight-docs` pages and drives an interactive extract → classify → severity → verify → fix → PR pipeline, reusing the installed `midnight-fact-check` and `midnight-verify` plugins.

**Architecture:** Deterministic work (repo scan, drift math, mapping inference, severity, aggregation) ships as pure-core Python scripts with thin subprocess/file I/O shells, so the cores are unit-testable without network. Judgement work (mapping read-pass, claim extraction, classification, verification, fixing) is delegated to sibling-plugin agents/commands, orchestrated by the command markdown which owns every interactive gate. All state lives under `${CLAUDE_PLUGIN_DATA}`.

**Tech Stack:** Python 3.10+ (stdlib only — `json`, `subprocess`, `datetime`, `pathlib`, `re`, `argparse`, `os`, `sys`), `pytest` (dev-only), `gh` CLI, `git`. Markdown for the command + skill. JSON for state.

## Global Constraints

- No third-party Python runtime dependencies; stdlib only. `pytest` is dev-only.
- No custom npm/registry config anywhere in the plugin.
- All persistent + per-run state lives under `${CLAUDE_PLUGIN_DATA}`, keyed by org and docs-repo remote. Nothing is written into the `midnight-docs` working tree.
- The repo list always includes the cross-org repo `LFDT-Minokawa/compact` in addition to active `midnightntwrk` repos.
- Repo-list cache is stale after 14 days (but the user is always shown `generated_at` and decides).
- Eligible doc files are `*.mdx`/`*.md`, excluding any path segment starting with `_` and, by default, `docs/relnotes/`.
- "Active repo" = not archived, not empty/scaffold-only, default-branch commit within the window (default 6 months).
- Drift = a doc file's last git-modified time predates the last-published time of any repo it maps to. Last-published = latest GitHub release `published_at`, else default-branch HEAD `committedDate`.
- Config precedence: command flags > plugin settings > defaults.
- Extraction, classification, and verification are delegated to siblings; never reimplemented.

---

### Task 1: Plugin scaffold + shared library

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `scripts/lib.py`
- Create: `tests/test_lib.py`
- Create: `pytest.ini`

**Interfaces:**
- Produces: `lib.iso_now() -> str`; `lib.parse_iso(s: str) -> datetime` (aware, UTC); `lib.is_cache_fresh(generated_at: str, ttl_days: int, now: datetime|None=None) -> bool`; `lib.state_dir(plugin_data: str, *parts: str) -> Path` (creates dirs); `lib.slugify(text: str) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_lib.py
from datetime import datetime, timezone
import scripts.lib as lib

def test_parse_iso_handles_z_and_offset():
    assert lib.parse_iso("2026-07-16T10:00:00Z") == datetime(2026,7,16,10,0,tzinfo=timezone.utc)
    assert lib.parse_iso("2026-07-16T10:00:00+00:00").tzinfo is not None

def test_is_cache_fresh_boundary():
    now = datetime(2026,7,16,0,0,tzinfo=timezone.utc)
    assert lib.is_cache_fresh("2026-07-02T00:00:00Z", 14, now) is True    # exactly 14 days
    assert lib.is_cache_fresh("2026-07-01T23:59:59Z", 14, now) is False   # just over 14 days

def test_slugify():
    assert lib.slugify("Fix: persistentHash returns Bytes<32>!") == "fix-persistenthash-returns-bytes-32"

def test_state_dir_creates(tmp_path):
    p = lib.state_dir(str(tmp_path), "midnightntwrk")
    assert p.is_dir() and p.name == "midnightntwrk"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_lib.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.lib'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/lib.py
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))

def is_cache_fresh(generated_at: str, ttl_days: int, now=None) -> bool:
    now = now or datetime.now(timezone.utc)
    return (now - parse_iso(generated_at)) <= timedelta(days=ttl_days)

def state_dir(plugin_data: str, *parts: str) -> Path:
    p = Path(plugin_data).joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p

def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)
```

```json
// .claude-plugin/plugin.json
{
  "name": "midnight-docs-drift",
  "version": "0.1.0",
  "description": "Detect and repair drifted midnightntwrk/midnight-docs pages via /update-drifted-docs.",
  "commands": ["commands/update-drifted-docs.md"],
  "skills": ["skills/docs-drift-methodology"],
  "notes": "Soft-depends on the midnight-fact-check and midnight-verify plugins being installed."
}
```

```ini
# pytest.ini
[pytest]
testpaths = tests
```

Create empty `scripts/__init__.py` and `tests/__init__.py` so `import scripts.lib` resolves.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_lib.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/plugin.json scripts/lib.py scripts/__init__.py tests/__init__.py tests/test_lib.py pytest.ini
git commit -m "feat: plugin scaffold + shared state/date helpers"
```

---

### Task 2: `repo_scan.py` — active org repos + extra cross-org repos

**Files:**
- Create: `scripts/repo_scan.py`
- Test: `tests/test_repo_scan.py`

**Interfaces:**
- Consumes: `lib.iso_now`.
- Produces: `repo_scan.is_active(node: dict, since_iso: str) -> bool`; `repo_scan.build_repo_list(nodes: list[dict], since_iso: str, extra: list[dict]) -> list[dict]` returning records `{"name","url","last_commit","description","private"}` sorted by `last_commit` desc; `repo_scan.SCAFFOLD_ONLY(entries: set[str]) -> bool`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_repo_scan.py
import scripts.repo_scan as rs

SINCE = "2026-01-16T00:00:00Z"

def node(name, pushed, commit, archived=False, empty=False, entries=("src","README.md"), priv=False):
    return {"name":name,"url":f"https://github.com/midnightntwrk/{name}","isArchived":archived,
            "isEmpty":empty,"isPrivate":priv,"description":"d","pushedAt":pushed,
            "lastCommit":commit,"topLevelEntries":list(entries)}

def test_is_active_filters():
    assert rs.is_active(node("a","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z"), SINCE) is True
    assert rs.is_active(node("b","2025-01-01T0:0:0Z","2025-01-01T00:00:00Z"), SINCE) is False  # too old
    assert rs.is_active(node("c","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z",archived=True), SINCE) is False
    assert rs.is_active(node("d","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z",empty=True), SINCE) is False

def test_scaffold_only_excluded():
    scaffold = {".envrc",".github","CHANGELOG.md","CODEOWNERS","CODE_OF_CONDUCT.md",
                "CONTRIBUTING.md","LICENSE","README.md","SECURITY.md"}
    n = node("s","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z",entries=scaffold)
    assert rs.is_active(n, SINCE) is False

def test_build_list_sorts_desc_and_appends_extra():
    nodes=[node("old","2026-02-01T0:0:0Z","2026-02-01T00:00:00Z"),
           node("new","2026-07-01T0:0:0Z","2026-07-01T00:00:00Z")]
    extra=[{"name":"compact","url":"https://github.com/LFDT-Minokawa/compact",
            "last_commit":"2026-06-25T00:00:00Z","description":"Compact","private":False}]
    out = rs.build_repo_list(nodes, SINCE, extra)
    assert [r["name"] for r in out] == ["new","compact","old"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_repo_scan.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.repo_scan'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/repo_scan.py
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
GQL = """query($org:String!,$cursor:String){organization(login:$org){repositories(first:50,after:$cursor,orderBy:{field:PUSHED_AT,direction:DESC}){pageInfo{hasNextPage endCursor} nodes{name url isArchived isEmpty isPrivate description pushedAt defaultBranchRef{target{... on Commit{committedDate tree{entries{name}}}}}}}}}"""

def _fetch_org(org):
    raw = subprocess.run(["gh","api","graphql","--paginate","-f",f"org={org}",
        "-f",f"query={GQL}","--jq",
        ".data.organization.repositories.nodes[]|{name,url,isArchived,isEmpty,isPrivate,description,pushedAt,lastCommit:.defaultBranchRef.target.committedDate,topLevelEntries:[.defaultBranchRef.target.tree.entries[].name]}"],
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_repo_scan.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/repo_scan.py tests/test_repo_scan.py
git commit -m "feat: active-repo scan core + gh shell (incl. extra cross-org repos)"
```

---

### Task 3: `drift_detect.py` — publish date vs per-file git mtime

**Files:**
- Create: `scripts/drift_detect.py`
- Test: `tests/test_drift_detect.py`

**Interfaces:**
- Consumes: `lib.parse_iso`.
- Produces: `drift_detect.resolve_publish(release_pub: str|None, head_date: str|None) -> tuple[str|None,str]` (returns `(iso_or_None, "release"|"push"|"unknown")`); `drift_detect.drift_for_page(doc_modified: str, repo_pubs: dict[str,tuple[str,str]]) -> list[dict]` returning `[{"repo","published","method"}]` for repos published after the doc, newest first.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_drift_detect.py
import scripts.drift_detect as dd

def test_resolve_prefers_release():
    assert dd.resolve_publish("2026-06-25T00:00:00Z","2026-07-01T00:00:00Z") == ("2026-06-25T00:00:00Z","release")
    assert dd.resolve_publish(None,"2026-07-01T00:00:00Z") == ("2026-07-01T00:00:00Z","push")
    assert dd.resolve_publish(None,None) == (None,"unknown")

def test_drift_for_page_lists_newer_only_desc():
    pubs = {"repoA":("2026-07-10T00:00:00Z","release"),
            "repoB":("2026-05-01T00:00:00Z","push"),
            "repoC":("2026-07-14T00:00:00Z","release")}
    out = dd.drift_for_page("2026-06-01T00:00:00Z", pubs)
    assert [d["repo"] for d in out] == ["repoC","repoA"]      # repoB older -> excluded; sorted desc
    assert out[0]["method"] == "release"

def test_drift_for_page_empty_when_doc_newest():
    pubs = {"r":("2026-01-01T00:00:00Z","push")}
    assert dd.drift_for_page("2026-06-01T00:00:00Z", pubs) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_drift_detect.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.drift_detect'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/drift_detect.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_drift_detect.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/drift_detect.py tests/test_drift_detect.py
git commit -m "feat: drift detection core (release-else-push vs git mtime)"
```

---

### Task 4: `build_map.py` — docs→repo inference

**Files:**
- Create: `scripts/build_map.py`
- Test: `tests/test_build_map.py`

**Interfaces:**
- Produces: `build_map.map_page(items: list[str], repo_names: set[str]) -> dict` returning `{"linked":[urls],"inferred":[urls]}` where `linked` = explicit `github.com/...` URLs whose repo is in `repo_names`, `inferred` = component→repo lookups from tech/tool strings (minus anything already linked). Uses `build_map.TECH_RULES` (ordered list of `(regex, [repo_names])`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_build_map.py
import scripts.build_map as bm

NAMES = {"midnight-node","midnight-ledger","compact","midnight-indexer"}

def test_linked_kept_only_if_repo_known():
    items = ["Midnight Node","https://github.com/midnightntwrk/midnight-node",
             "https://github.com/midnightntwrk/proof-server"]  # proof-server not in NAMES
    m = bm.map_page(items, NAMES)
    assert "https://github.com/midnightntwrk/midnight-node" in m["linked"]
    assert all("proof-server" not in u for u in m["linked"])

def test_inferred_from_tech_and_deduped_against_linked():
    items = ["Ledger","Zswap","https://github.com/midnightntwrk/midnight-ledger"]
    m = bm.map_page(items, NAMES)
    # ledger is linked, so it must NOT also appear in inferred
    assert "https://github.com/midnightntwrk/midnight-ledger" in m["linked"]
    assert "https://github.com/midnightntwrk/midnight-ledger" not in m["inferred"]

def test_compact_tech_infers_compact_repo():
    m = bm.map_page(["Compact compiler (compactc)"], NAMES)
    assert any(u.endswith("/compact") for u in m["inferred"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_build_map.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.build_map'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/build_map.py
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

def _url_for(name, known_urls):
    return known_urls.get(name)

def map_page(items, repo_names, known_urls=None):
    known_urls = known_urls or {n: f"https://github.com/midnightntwrk/{n}" for n in repo_names}
    known_urls.setdefault("compact", "https://github.com/LFDT-Minokawa/compact")
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_build_map.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/build_map.py tests/test_build_map.py
git commit -m "feat: docs->repo inference (linked + tech-rule inferred)"
```

---

### Task 5: `severity_pass.py` — heuristic blast-radius severity

> **Amendment (2026-07-16, post-review, user-approved):** the HIGH tier below was tightened after the Task 5 review demonstrated it over-fired on bare English words (`disclose`, `returns`, `witness`, `must be`, `syntax`) in conceptual prose. The shipped implementation: splits HIGH into `HIGH_STRICT` (inherently code-exact, fires unconditionally) and `HIGH_CONTEXTUAL` (bare words that only reach HIGH when a code marker co-occurs, via a `CODE_CONTEXT` regex); drops generic `must be`/`is required` from HIGH; makes `is_unclassified` cap a claim at `low` unless a HIGH code-exact fact fired; and adds tests covering all five outcome branches plus the two new behaviors. The committed code (see the commit for this task) is authoritative; the code block below is the pre-amendment version kept for history.

**Files:**
- Create: `scripts/severity_pass.py`
- Test: `tests/test_severity_pass.py`

**Interfaces:**
- Produces: `severity_pass.severity_for(claim_text: str, domains: list[str], is_unclassified: bool) -> tuple[str,str]` returning `(severity, signal)` where severity ∈ `{"high","medium","low"}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_severity_pass.py
import scripts.severity_pass as sp

def test_high_on_code_exact():
    s,_ = sp.severity_for("persistentHash<T>() returns Bytes<32>", ["compact"], False)
    assert s == "high"

def test_low_on_conceptual_unclassified():
    s,_ = sp.severity_for("Zswap is a protocol that enables private transactions", [], True)
    assert s == "low"

def test_medium_on_named_construct_behaviour():
    s,_ = sp.severity_for("The `increment` circuit updates the counter", ["compact"], False)
    assert s == "medium"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_severity_pass.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.severity_pass'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/severity_pass.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_severity_pass.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/severity_pass.py tests/test_severity_pass.py
git commit -m "feat: heuristic severity pass (blast-radius tiers)"
```

---

### Task 6: `aggregate.py` — merge claim batches + summaries

**Files:**
- Create: `scripts/aggregate.py`
- Test: `tests/test_aggregate.py`

**Interfaces:**
- Produces: `aggregate.summarize(claims: list[dict]) -> dict` with keys `total`, `domain_tag_counts` ({compact,sdk,zkir,witness}), `unclassified`, `multi_domain`, `severity` ({high,medium,low}), `by_page` ({path:count}).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_aggregate.py
import scripts.aggregate as agg

def C(claim, domains, sev, page="docs/x.mdx"):
    return {"claim":claim,"domains":domains,"unclassified":not domains,
            "severity":sev,"source":{"file":page}}

def test_summarize_counts():
    claims=[C("a",["compact"],"high"), C("b",["compact","sdk"],"medium"),
            C("c",[],"low",page="docs/y.mdx")]
    s = agg.summarize(claims)
    assert s["total"] == 3
    assert s["domain_tag_counts"]["compact"] == 2
    assert s["domain_tag_counts"]["sdk"] == 1
    assert s["unclassified"] == 1
    assert s["multi_domain"] == 1
    assert s["severity"] == {"high":1,"medium":1,"low":1}
    assert s["by_page"]["docs/x.mdx"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_aggregate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.aggregate'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/aggregate.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_aggregate.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/aggregate.py tests/test_aggregate.py
git commit -m "feat: claim aggregation + domain x severity summary"
```

---

### Task 7: `docs-drift-methodology` skill

**Files:**
- Create: `skills/docs-drift-methodology/SKILL.md`

**Interfaces:**
- Consumes: nothing at runtime; it is reference content the command and dispatched agents read.
- Produces: documented rubrics (active-repo criteria, repo-reference rules for the mapping read-pass, drift semantics, severity tiers).

- [ ] **Step 1: Write the skill file**

```markdown
---
name: docs-drift-methodology
description: Rubrics for the /update-drifted-docs pipeline — active-repo criteria, docs→repo reference rules, drift semantics, and the heuristic severity tiers. Read by the command and its dispatched mapping/claim agents.
---

# Docs-Drift Methodology

## Active repo (stage 1)
A `midnightntwrk` repo is included when ALL hold: not archived; not empty; default-branch
HEAD commit within the window (default 6 months); top-level tree is more than a README or
the standard scaffold set (`.envrc`, `.github`, `CHANGELOG.md`, `CODEOWNERS`,
`CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md`, `renovate.json`).
Always additionally include `LFDT-Minokawa/compact`.

## Mapping read-pass (stage 2, for dispatched agents)
For each page, record (a) Midnight technologies/tools it covers (human-readable names like
"Compact compiler (compactc)", "Midnight Node", "Indexer") and (b) specific
`midnightntwrk/*` repositories it references, as full GitHub URLs. Ignore `_`-prefixed files.
`build_map.py` turns these into `linked` (explicit URL, repo must exist in the repo list) and
`inferred` (component→repo rules).

## Drift semantics (stage 3)
A page is drifted when its last git-modified time predates the last-published time of any repo
it maps to. Last-published = latest release `published_at`, else default-branch HEAD
`committedDate`. Release-backed drift is higher confidence than push-backed.

## Severity tiers (post-classification)
Severity = blast radius if the claim is stale/wrong (NOT probability of being wrong).
- **high** — code-exact facts a developer copies verbatim: signatures, type expressions,
  imports/packages, keywords/operators/pragma, error/status codes, CLI flags, ZKIR opcodes,
  security primitives. Wrong → build breaks or security impact.
- **medium** — specific behaviour of a named construct, not a verbatim signature.
- **low** — conceptual/architectural prose with no code-exactness.
```

- [ ] **Step 2: Validate the skill frontmatter**

Run: `python -c "import re,sys; t=open('skills/docs-drift-methodology/SKILL.md').read(); assert t.startswith('---') and 'name: docs-drift-methodology' in t and 'description:' in t; print('skill frontmatter OK')"`
Expected: `skill frontmatter OK`

- [ ] **Step 3: Commit**

```bash
git add skills/docs-drift-methodology/SKILL.md
git commit -m "docs: docs-drift-methodology skill (rubrics)"
```

---

### Task 8: `update-drifted-docs` command orchestrator

**Files:**
- Create: `commands/update-drifted-docs.md`

**Interfaces:**
- Consumes: all scripts from Tasks 2–6, the Task 7 skill, and the sibling plugins (`midnight-fact-check` agents `claim-extractor`/`domain-classifier`; `midnight-verify` `/verify`).
- Produces: the user-facing `/update-drifted-docs [path]` command.

- [ ] **Step 1: Write the command file**

````markdown
---
description: Detect drifted midnight-docs pages and drive an interactive extract→classify→severity→verify→fix→PR pipeline. Run from inside a midnight-docs checkout. Optional path arg scopes the run to a subtree.
argument-hint: "[path] [--org X] [--since 6mo] [--extra-repo O/N] [--remap all|new|reuse] [--repos-ttl 14]"
---

You are running the docs-drift pipeline. Load the `docs-drift-methodology` skill first for
all rubrics. Resolve `${CLAUDE_PLUGIN_DATA}` as the state root and `$1` (if present) as the
path scope. Announce each stage; STOP at every gate and wait for the user.

**Preflight.** Confirm cwd is a git repo whose remote is the docs repo (default
`midnightntwrk/midnight-docs`); confirm `gh auth status` is OK; confirm the
`midnight-fact-check` and `midnight-verify` plugins are available (if not, tell the user how
to install them and stop). Resolve eligible files under the scope: `*.mdx`/`*.md`, excluding
`_`-prefixed segments and (by default) `docs/relnotes/`.

**Stage 1 — Repo list.** Look for `${CLAUDE_PLUGIN_DATA}/<org>/repos.json`. If it exists,
report its `generated_at` and whether it is within the TTL (14 days). GATE: ask regenerate or
reuse. On regenerate/absent, run:
`python ${CLAUDE_PLUGIN_ROOT}/scripts/repo_scan.py --org <org> --since <iso-cutoff> --extra-repo LFDT-Minokawa/compact --out ${CLAUDE_PLUGIN_DATA}/<org>/repos.json`

**Stage 2 — Docs→repo map.** Load `${CLAUDE_PLUGIN_DATA}/<docs-repo>/docs-repo-map.json`.
Diff its keys against the scoped eligible files. GATE: if new/removed pages → remap all vs
only new; if none → remap vs reuse. To (re)map: dispatch reader agents over the target pages
to produce `{page:[tech/tool + repo-URL items]}` per the methodology skill, write it to the
run dir, then run:
`python ${CLAUDE_PLUGIN_ROOT}/scripts/build_map.py --page-items <items.json> --repos ${CLAUDE_PLUGIN_DATA}/<org>/repos.json --out ${CLAUDE_PLUGIN_DATA}/<docs-repo>/docs-repo-map.json`

**Stage 3 — Drift detect.** Run:
`python ${CLAUDE_PLUGIN_ROOT}/scripts/drift_detect.py --docs-repo . --map ${CLAUDE_PLUGIN_DATA}/<docs-repo>/docs-repo-map.json --out <run>/drift.json`

**Stage 4 — Drift summary.** Render each drifted page → the repos published more recently
(date + release/push). GATE: ask the user to exclude any files or continue with all; apply
exclusions to the working set.

**Stage 5 — Claims.** For the working set, dispatch `midnight-fact-check`'s `claim-extractor`
agents in parallel batches (each writes a claim batch JSON to `<run>/claims/`), then dispatch
`domain-classifier`. Then run:
`python ${CLAUDE_PLUGIN_ROOT}/scripts/severity_pass.py --claims-glob "<run>/claims/claims-batch-*.json"`
`python ${CLAUDE_PLUGIN_ROOT}/scripts/aggregate.py --claims-glob "<run>/claims/claims-batch-*.json" --out <run>/severity.json`

**Stage 6 — Claims summary.** Present counts as domain × severity from `<run>/severity.json`.
GATE: ask whether to verify ALL, a PRESET subset (high-severity only · one domain · one
page/subtree · high+medium excluding unclassified), or a USER-SPECIFIED custom subset.

**Stage 7 — Verify.** For each selected claim/subset invoke `/midnight-verify:verify` with the
claim text and its source page; collect supported/refuted/inconclusive with evidence into
`<run>/verify-report.md`.

**Stage 8 — Report.** Present the verification report. GATE: offer to fix the refuted claims.

**Stage 9 — Fix → PR (only if accepted).**
1. Ask clarifying questions about ambiguous refuted claims.
2. Ensure `main` is current (`git fetch`, fast-forward).
3. `git checkout -b fix/<slug>`.
4. Apply edits to the docs files. Use judgement on commits: a substantial single fix may be
   its own commit; several small fixes to one file may be one per-file commit — all on the one
   branch.
5. GATE: offer to re-verify each fix (re-run `/midnight-verify:verify` on the corrected claim)
   before finalizing.
6. GATE: offer to push and open a PR with `gh pr create`, body listing the fixed claims + evidence.

Never mutate git (branch/commit/push/PR) except behind the explicit Stage 9 gates. Write all
per-run artifacts under `${CLAUDE_PLUGIN_DATA}/<docs-repo>/runs/<iso-ts>/`.
````

- [ ] **Step 2: Validate the command frontmatter**

Run: `python -c "t=open('commands/update-drifted-docs.md').read(); assert t.startswith('---') and 'description:' in t and 'argument-hint:' in t; print('command frontmatter OK')"`
Expected: `command frontmatter OK`

- [ ] **Step 3: Commit**

```bash
git add commands/update-drifted-docs.md
git commit -m "feat: /update-drifted-docs orchestrator command"
```

---

### Task 9: Full test run + README

**Files:**
- Create: `README.md` (plugin usage) — overwrite the existing stub
- Test: whole suite

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Run the whole suite**

Run: `python -m pytest -v`
Expected: PASS — all tests from Tasks 1–6 green (14+ tests).

- [ ] **Step 2: Write the README**

```markdown
# midnight-docs-drift

A Claude Code plugin. Run `/update-drifted-docs [path]` from inside a `midnight-docs`
checkout to detect pages that have drifted behind the repos they document, then interactively
extract → classify → severity-rank → verify → fix → PR the stale claims.

**Requires:** the `midnight-fact-check` and `midnight-verify` plugins installed, and `gh`
authenticated with org read access. State is kept under `${CLAUDE_PLUGIN_DATA}`.

Deterministic stages are Python scripts in `scripts/` (unit-tested in `tests/`); claim
extraction/classification/verification are delegated to the sibling plugins.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: plugin README + full green suite"
```

---

## Self-Review

**Spec coverage:** D1 (reuse siblings) → Tasks 8/9 + plugin.json notes; D2 (run from checkout + path scope) → Task 8 preflight/args; D3 (`${CLAUDE_PLUGIN_DATA}`) → all script `--out` paths + Task 8; D4 (own the gates) → Task 8 stages; D5 (offer re-verify) → Task 8 Stage 9.5; D6 (one branch, judgement commits) → Task 8 Stage 9.4; D7 (14-day TTL) → `lib.is_cache_fresh` + Task 8 Stage 1; D8 (flags + LFDT-Minokawa/compact) → Task 2 `--extra-repo` default + repo_scan; D9 (presets + custom subset) → Task 8 Stage 6. Pipeline stages 1–9, state layout, and reuse contracts all have tasks. No gaps.

**Placeholder scan:** every code step contains complete code; every command step has an exact command + expected output. No TBD/TODO.

**Type consistency:** `map_page`, `severity_for`, `resolve_publish`, `drift_for_page`, `summarize`, `build_repo_list`, `is_active` names/signatures are used identically in their tests and (where wired) in `main()` shells and the command. State JSON shapes (`repos.json` `.repos`, map `.pages`, drift `.stale_pages`) are consistent across `repo_scan`/`build_map`/`drift_detect`/Task 8.
