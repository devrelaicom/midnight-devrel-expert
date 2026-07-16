# midnight-reports Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a `midnight-reports` plugin whose `/midnight-reports:pr <repo> [timeframe]` command generates a self-contained, themed HTML PR-activity report for any GitHub repo, then offers a paste-ready Slack message.

**Architecture:** A thin command loads the `pr-activity-report` skill, which drives a deterministic Python helper (`scripts/pr_report.py` with `fetch` and `build` subcommands, backed by pure modules `lib`/`enrich`/`render`). The script reports **facts** (per-PR enrichment + a per-check failure-rate table) and renders HTML from a committed template; the **model** infers CI noise, reads PR threads to write `narrative.json`, publishes the Artifact, and (on request) writes a Slack message in a vendored casual voice.

**Tech Stack:** Python 3 stdlib only (argparse, subprocess, json, html, re, datetime), `gh` CLI, pytest (local dev gate), bash marketplace validation.

## Global Constraints

- Plugin name is **`midnight-reports`**; command namespace is therefore **`/midnight-reports:pr`** (prefix must equal plugin name). [spec D1]
- Scripts are a package run via `python3 -m scripts.<mod>` from the plugin root; pure core is unit-tested, the `gh` I/O shell is not (exercised by dry-run). [house pattern: `plugins/midnight-docs-drift`]
- **Script reports facts; model makes judgments.** No "noise" verdict, no interpretive triage framing baked into the script. `ciStatusRaw` derives only from actual check conclusions; a mechanical `priority`/`blockedOn` exists **solely** to order the action queue. [spec D3]
- `<repo>` accepts `owner/name` or a `github.com/owner/name[/...]` URL → normalized to `owner/name`. [spec D5]
- `[timeframe]` accepts `Nd`/`Nw`/`Nmo` or `YYYY-MM-DD`; **default `2w`**; resolved to an ISO date used as `gh` `updated:>=<since>`. [spec D6]
- Output: publish an Artifact (favicon 🌙, title `<repo> · PR Review Watch`) **and** save under `${CLAUDE_PLUGIN_DATA}/<owner>/<name>/runs/<iso-ts>/`; never write to cwd. [spec D9]
- Report identity is a repo-agnostic "review watch" dashboard, parameterized by repo name. [spec D7]
- Model cannot toggle artifact visibility (verified). The enable-sharing reminder is given at offer time, never inside the Slack message. [spec D12]
- **Slack output isolation (hard rule):** when the Slack message is delivered, the entire response is the message text and nothing else — no preamble/postamble/question/code fence; only trailing content is the report link as the last line. [spec D15]
- Slack voice: vendored `references/slack-voice.md` (slack-casual). Zero em-dashes, inclusive/non-gendered language, no AI tropes. [spec D13]
- Slack content rubric: lead with what matters to DevRel; flag surprising/urgent (team-owned, zero-blame, never pin a problem on a person); always a genuine good-news item; individual cudos only when earned and sparingly; never a negative individual call-out. [spec D14]
- ASCII only in generated HTML/JS source except intentional unicode via escapes; straight quotes.

---

## File Structure

```
plugins/midnight-reports/
  .claude-plugin/plugin.json            # metadata (name, version, description, keywords)
  commands/pr.md                        # thin wrapper: normalize args -> load skill
  skills/pr-activity-report/
    SKILL.md                            # workflow + facts/judgment boundary + Slack rubric
    references/
      template.html                     # themed skeleton with <!--MARKER--> injection points + filter JS
      data-contract.md                  # report-data.json + narrative.json schemas
      slack-voice.md                    # vendored slack-casual voice (Slack message only)
  scripts/
    __init__.py
    lib.py                              # parse_repo, resolve_since, iso/date helpers  (pure)
    enrich.py                           # per-PR enrichment + failure-rate table + mechanical triage (pure)
    render.py                           # report-data + narrative -> HTML fragments + render_report (pure)
    pr_report.py                        # CLI: fetch (gh shell) | build (template render)
    tests/
      __init__.py
      test_lib.py
      test_enrich.py
      test_render.py
  README.md
```

Plus marketplace-level changes (shared by all plugins, not specific to this one):
- Append one entry to `.claude-plugin/marketplace.json`.
- Create `scripts/ci/run-python-tests.sh` — a single shared runner that runs `pytest` in every
  plugin that has Python tests (Task 10).
- Add a `python-tests` job to `.github/workflows/validate.yml` that invokes it (Task 10).
- Add a "Adding Python tests to your plugin" section to the repo-root `README.md` (Task 10).

Responsibilities: `lib` = argument/time helpers; `enrich` = turn raw `gh` PR dicts into fact records; `render` = turn fact + narrative dicts into HTML; `pr_report` = CLI glue + the only module that shells out to `gh` or touches the filesystem.

---

### Task 1: Plugin scaffold + marketplace registration

**Files:**
- Create: `plugins/midnight-reports/.claude-plugin/plugin.json`
- Create: `plugins/midnight-reports/scripts/__init__.py` (empty)
- Create: `plugins/midnight-reports/scripts/tests/__init__.py` (empty)
- Modify: `.claude-plugin/marketplace.json` (append plugin entry)

**Interfaces:**
- Produces: a registered plugin directory that `bash scripts/ci/validate.sh` accepts.

- [ ] **Step 1: Create `plugin.json`**

```json
{
  "name": "midnight-reports",
  "version": "0.1.0",
  "description": "Generate self-contained HTML pull-request activity reports for any GitHub repo. /midnight-reports:pr <repo> [timeframe] fetches PRs via gh, computes CI/triage/age facts (leaving CI-noise judgment to the model), renders a themed dashboard-plus-narrative report, publishes it as an Artifact, and offers a paste-ready Slack summary in a zero-blame casual voice.",
  "author": {
    "name": "Aaron Bassett",
    "email": "aaron@devrel-ai.com"
  },
  "homepage": "https://github.com/devrelaicom/midnight-devrel-expert",
  "repository": "https://github.com/devrelaicom/midnight-devrel-expert.git",
  "license": "MIT",
  "keywords": ["midnight", "github", "pull-requests", "report", "dashboard", "devrel", "gh", "artifact"]
}
```

- [ ] **Step 2: Create the two empty `__init__.py` files**

```bash
mkdir -p plugins/midnight-reports/scripts/tests
: > plugins/midnight-reports/scripts/__init__.py
: > plugins/midnight-reports/scripts/tests/__init__.py
```

- [ ] **Step 3: Append the plugin to `.claude-plugin/marketplace.json`**

Add this object to the `plugins` array (after the `gha` entry):

```json
    { "name": "midnight-reports", "source": "./plugins/midnight-reports" }
```

- [ ] **Step 4: Validate structure**

Run: `bash scripts/ci/validate.sh`
Expected: output includes `Plugin validated: midnight-reports` and `All validation checks passed` (exit 0).

- [ ] **Step 5: Commit**

```bash
git add plugins/midnight-reports/.claude-plugin/plugin.json plugins/midnight-reports/scripts/__init__.py plugins/midnight-reports/scripts/tests/__init__.py .claude-plugin/marketplace.json
git commit -m "feat(midnight-reports): scaffold plugin + register in marketplace"
```

---

### Task 2: `lib.py` — argument + time helpers

**Files:**
- Create: `plugins/midnight-reports/scripts/lib.py`
- Test: `plugins/midnight-reports/scripts/tests/test_lib.py`

**Interfaces:**
- Produces:
  - `parse_repo(s: str) -> str` — normalizes `owner/name` or a github URL to `"owner/name"`; raises `ValueError` on bad input.
  - `resolve_since(timeframe: str, now: datetime|None=None) -> str` — `Nd`/`Nw`/`Nmo` or `YYYY-MM-DD` → ISO date `"YYYY-MM-DD"`; raises `ValueError`.
  - `iso_now() -> str`, `parse_iso(s: str) -> datetime`, `days_between(earlier_iso: str, now: datetime) -> int`.

Run all commands in this task from `plugins/midnight-reports/`.

- [ ] **Step 1: Write the failing test**

Create `scripts/tests/test_lib.py`:

```python
from datetime import datetime, timezone
import pytest
import scripts.lib as lib

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)

def test_parse_repo_bare():
    assert lib.parse_repo("midnightntwrk/midnight-docs") == "midnightntwrk/midnight-docs"

def test_parse_repo_url_forms():
    assert lib.parse_repo("https://github.com/foo/bar") == "foo/bar"
    assert lib.parse_repo("https://github.com/foo/bar/tree/main/x") == "foo/bar"
    assert lib.parse_repo("git@github.com:foo/bar.git") == "foo/bar"
    assert lib.parse_repo("github.com/foo/bar.git") == "foo/bar"

def test_parse_repo_rejects_garbage():
    for bad in ["", "just-a-name", "https://github.com/onlyowner"]:
        with pytest.raises(ValueError):
            lib.parse_repo(bad)

def test_resolve_since_relative():
    assert lib.resolve_since("2w", NOW) == "2026-07-02"
    assert lib.resolve_since("10d", NOW) == "2026-07-06"
    assert lib.resolve_since("3mo", NOW) == "2026-04-17"

def test_resolve_since_absolute_and_bad():
    assert lib.resolve_since("2026-01-05", NOW) == "2026-01-05"
    with pytest.raises(ValueError):
        lib.resolve_since("soon", NOW)

def test_days_between():
    assert lib.days_between("2026-07-06T00:00:00Z", NOW) == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest scripts/tests/test_lib.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'scripts.lib'` or attribute errors).

- [ ] **Step 3: Write `scripts/lib.py`**

```python
"""Shared helpers for the pr_report pipeline (pure, unit-tested)."""
import re
from datetime import datetime, timezone, timedelta

_GITHUB = re.compile(r"^(?:https?://)?(?:www\.)?github\.com/", re.I)
_SSH = re.compile(r"^git@github\.com:", re.I)
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))

def parse_repo(s: str) -> str:
    t = (s or "").strip()
    t = _GITHUB.sub("", t)
    t = _SSH.sub("", t)
    t = t.split("?", 1)[0].split("#", 1)[0]
    parts = [p for p in t.split("/") if p]
    if len(parts) < 2:
        raise ValueError("cannot parse repo from %r" % (s,))
    owner, name = parts[0], parts[1]
    if name.endswith(".git"):
        name = name[:-4]
    repo = "%s/%s" % (owner, name)
    if not _REPO.match(repo):
        raise ValueError("invalid repo %r from %r" % (repo, s))
    return repo

def resolve_since(timeframe: str, now=None) -> str:
    now = now or datetime.now(timezone.utc)
    t = (timeframe or "").strip().lower()
    m = re.fullmatch(r"(\d+)(d|w|mo)", t)
    if m:
        n = int(m.group(1))
        days = {"d": 1, "w": 7, "mo": 30}[m.group(2)] * n
        return (now - timedelta(days=days)).date().isoformat()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        datetime.strptime(t, "%Y-%m-%d")  # validate
        return t
    raise ValueError("cannot parse timeframe %r (use Nd/Nw/Nmo or YYYY-MM-DD)" % (timeframe,))

def days_between(earlier_iso: str, now) -> int:
    return max(0, int((now - parse_iso(earlier_iso)).total_seconds() // 86400))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest scripts/tests/test_lib.py -q`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/lib.py scripts/tests/test_lib.py
git commit -m "feat(midnight-reports): repo + timeframe parsing helpers"
```

---

### Task 3: `enrich.py` — PR enrichment + failure-rate table

**Files:**
- Create: `plugins/midnight-reports/scripts/enrich.py`
- Test: `plugins/midnight-reports/scripts/tests/test_enrich.py`

**Interfaces:**
- Consumes: `scripts.lib.days_between`, `scripts.lib.iso_now`.
- Produces:
  - `is_bot_author(author: dict) -> bool`, `is_bot_commenter(login: str) -> bool`
  - `failing_checks(rollup: list) -> list[{"name","conclusion"}]` (includes systemic checks; no noise verdict)
  - `ci_status_raw(rollup: list) -> "failing"|"pending"|"passing"|"mixed"|"none"`
  - `check_failure_rates(open_prs: list) -> list[{"name","failed","total","rate"}]`
  - `enrich_pr(pr: dict, now: datetime) -> dict`
  - `build_report_data(raw_prs: list, repo: str, since: str, now: datetime) -> {"meta","checkFailureRates","prs"}`

Raw `gh` `statusCheckRollup` items are either `CheckRun` (`name`,`status`,`conclusion`) or `StatusContext` (`context`,`state`).

- [ ] **Step 1: Write the failing test**

Create `scripts/tests/test_enrich.py`:

```python
from datetime import datetime, timezone
import scripts.enrich as en

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)

def check(name, conclusion=None, status="COMPLETED"):
    return {"__typename": "CheckRun", "name": name, "status": status, "conclusion": conclusion}

def ctx(name, state):
    return {"__typename": "StatusContext", "context": name, "state": state}

def pr(number, state="OPEN", author="alice", is_bot=False, review="REVIEW_REQUIRED",
       rollup=None, comments=None, reviews=None, created="2026-07-10T00:00:00Z",
       updated="2026-07-15T00:00:00Z"):
    return {"number": number, "title": "t%d" % number, "url": "u%d" % number, "state": state,
            "isDraft": False, "baseRefName": "main",
            "author": {"login": author, "is_bot": is_bot}, "createdAt": created,
            "updatedAt": updated, "closedAt": None, "mergedAt": None, "reviewDecision": review,
            "additions": 5, "deletions": 1, "changedFiles": 2, "labels": [{"name": "x"}],
            "statusCheckRollup": rollup or [], "comments": comments or [], "reviews": reviews or []}

def test_bot_detection():
    assert en.is_bot_author({"login": "app/dependabot", "is_bot": True}) is True
    assert en.is_bot_author({"login": "app/renovate"}) is True
    assert en.is_bot_author({"login": "alice"}) is False
    assert en.is_bot_commenter("vercel") is True
    assert en.is_bot_commenter("github-actions") is True
    assert en.is_bot_commenter("CLAassistant") is True
    assert en.is_bot_commenter("alice") is False

def test_failing_checks_and_status():
    roll = [check("build", "SUCCESS"), ctx("Vercel", "FAILURE"),
            check("deploy", "FAILURE"), check("lint", None, status="IN_PROGRESS")]
    fails = en.failing_checks(roll)
    names = {f["name"]: f["conclusion"] for f in fails}
    assert names["Vercel"] == "FAILURE"
    assert names["deploy"] == "FAILURE"
    assert names["lint"] == "PENDING"
    assert "build" not in names
    assert en.ci_status_raw(roll) == "failing"
    assert en.ci_status_raw([check("a", "SUCCESS"), check("b", "SKIPPED")]) == "passing"
    assert en.ci_status_raw([]) == "none"

def test_failure_rates_are_facts_only():
    prs = [pr(1, rollup=[ctx("Vercel", "FAILURE"), check("build", "SUCCESS")]),
           pr(2, rollup=[ctx("Vercel", "FAILURE"), check("build", "FAILURE")])]
    rates = en.check_failure_rates(prs)
    row = {r["name"]: r for r in rates}
    assert row["Vercel"] == {"name": "Vercel", "failed": 2, "total": 2, "rate": 1.0}
    assert row["build"]["failed"] == 1 and row["build"]["total"] == 2
    assert rates[0]["name"] == "Vercel"  # sorted by rate desc

def test_enrich_strips_bot_discussion_and_computes_ages():
    p = pr(7, comments=[{"author": {"login": "vercel"}}, {"author": {"login": "bob"}}],
           reviews=[{"author": {"login": "github-actions"}, "state": "COMMENTED", "submittedAt": "2026-07-11T00:00:00Z"},
                    {"author": {"login": "carol"}, "state": "APPROVED", "submittedAt": "2026-07-12T00:00:00Z"}],
           created="2026-07-06T00:00:00Z", updated="2026-07-14T00:00:00Z")
    r = en.enrich_pr(p, NOW)
    assert r["humanComments"] == 1
    assert [rv["who"] for rv in r["reviews"]] == ["carol"]
    assert r["ageDays"] == 10 and r["idleDays"] == 2
    assert r["authorType"] == "human"

def test_mechanical_priority_orders_queue():
    approved = en.enrich_pr(pr(1, review="APPROVED"), NOW)
    cifail = en.enrich_pr(pr(2, rollup=[check("deploy", "FAILURE")]), NOW)
    changes = en.enrich_pr(pr(3, review="CHANGES_REQUESTED"), NOW)
    assert approved["priority"] == 1 and approved["blockedOn"] == "maintainer"
    assert cifail["priority"] == 2 and "CI" in cifail["blockedOn"]
    assert changes["priority"] == 4 and changes["blockedOn"] == "author"

def test_build_report_data_totals():
    prs = [pr(1, state="OPEN"), pr(2, state="MERGED"), pr(3, state="CLOSED"),
           pr(4, state="OPEN", author="app/dependabot", is_bot=True)]
    data = en.build_report_data(prs, "o/n", "2026-07-02", NOW)
    t = data["meta"]["totals"]
    assert t == {"total": 4, "open": 2, "merged": 1, "closed": 1, "human": 3, "bot": 1}
    assert [p["number"] for p in data["prs"]] == [4, 3, 2, 1]  # sorted desc
    assert data["meta"]["repo"] == "o/n" and data["meta"]["since"] == "2026-07-02"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest scripts/tests/test_enrich.py -q`
Expected: FAIL (`No module named 'scripts.enrich'`).

- [ ] **Step 3: Write `scripts/enrich.py`**

```python
"""Pure PR enrichment: facts only. Deciding which failing checks are 'noise' is the model's job."""
from . import lib

_BOT_COMMENTERS = ("vercel", "github-actions", "coderabbit", "cla")
_FAILURE = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "STARTUP_FAILURE", "ACTION_REQUIRED"}
_PENDING = {"PENDING", "EXPECTED", ""}
_REVIEW_ORDER = {"APPROVED", "CHANGES_REQUESTED", "REVIEW_REQUIRED", "NONE"}

def is_bot_author(author):
    a = author or {}
    return bool(a.get("is_bot")) or str(a.get("login", "")).startswith("app/")

def is_bot_commenter(login):
    l = (login or "").lower()
    return l.startswith("app/") or any(b in l for b in _BOT_COMMENTERS)

def _name(it):
    return it.get("name") or it.get("context") or "?"

def _conclusion(it):
    return (it.get("conclusion") or it.get("state") or "").upper()

def _incomplete(it):
    return (it.get("status") or "COMPLETED").upper() != "COMPLETED"

def _is_failure(it):
    return _conclusion(it) in _FAILURE

def _is_pending(it):
    if _is_failure(it):
        return False
    return _incomplete(it) or _conclusion(it) in _PENDING

def failing_checks(rollup):
    out = []
    for it in rollup or []:
        if _is_failure(it):
            out.append({"name": _name(it), "conclusion": _conclusion(it)})
        elif _is_pending(it):
            out.append({"name": _name(it), "conclusion": "PENDING"})
    return out

def ci_status_raw(rollup):
    items = rollup or []
    if not items:
        return "none"
    if any(_is_failure(it) for it in items):
        return "failing"
    if any(_is_pending(it) for it in items):
        return "pending"
    if {_conclusion(it) for it in items} <= {"SUCCESS", "NEUTRAL", "SKIPPED", ""}:
        return "passing"
    return "mixed"

def check_failure_rates(open_prs):
    tally = {}
    for pr in open_prs:
        for it in pr.get("statusCheckRollup") or []:
            rec = tally.setdefault(_name(it), [0, 0])
            rec[1] += 1
            if _is_failure(it):
                rec[0] += 1
    rows = [{"name": n, "failed": f, "total": t, "rate": round(f / t, 3) if t else 0.0}
            for n, (f, t) in tally.items()]
    return sorted(rows, key=lambda r: (r["rate"], r["failed"]), reverse=True)

def _mechanical_triage(pr, author_type, fails):
    if pr["state"] != "OPEN":
        return {"blockedOn": "", "priority": 99, "action": ""}
    hard = [c for c in fails if c["conclusion"] != "PENDING"]
    rd = pr.get("reviewDecision") or "NONE"
    if hard:
        return {"blockedOn": "author (CI)", "priority": 2, "action": "Fix failing CI checks"}
    if rd == "APPROVED":
        return {"blockedOn": "maintainer", "priority": 1, "action": "Approved - ready to merge"}
    if rd == "CHANGES_REQUESTED":
        return {"blockedOn": "author", "priority": 4, "action": "Author to address review feedback"}
    if author_type == "bot":
        return {"blockedOn": "maintainer", "priority": 5, "action": "Dependency bump - review & merge"}
    if rd == "REVIEW_REQUIRED":
        return {"blockedOn": "maintainer", "priority": 3, "action": "Needs a maintainer review"}
    return {"blockedOn": "maintainer", "priority": 6, "action": "Triage"}

def enrich_pr(pr, now):
    author = pr.get("author") or {}
    atype = "bot" if is_bot_author(author) else "human"
    fails = failing_checks(pr.get("statusCheckRollup"))
    human_comments = [c for c in (pr.get("comments") or [])
                      if not is_bot_commenter((c.get("author") or {}).get("login", ""))]
    reviews = [{"who": (r.get("author") or {}).get("login", ""), "state": r.get("state"),
                "at": (r.get("submittedAt") or "")[:10]}
               for r in (pr.get("reviews") or [])
               if not is_bot_commenter((r.get("author") or {}).get("login", ""))]
    rec = {
        "number": pr["number"], "title": pr.get("title", ""), "url": pr.get("url", ""),
        "state": pr["state"], "isDraft": bool(pr.get("isDraft")),
        "baseRefName": pr.get("baseRefName", ""),
        "author": author.get("login", ""), "authorType": atype,
        "createdAt": pr.get("createdAt"), "updatedAt": pr.get("updatedAt"),
        "closedAt": pr.get("closedAt"), "mergedAt": pr.get("mergedAt"),
        "reviewDecision": pr.get("reviewDecision") or "NONE",
        "additions": pr.get("additions", 0), "deletions": pr.get("deletions", 0),
        "changedFiles": pr.get("changedFiles", 0),
        "labels": [l.get("name") for l in (pr.get("labels") or [])],
        "failingChecks": fails, "ciStatusRaw": ci_status_raw(pr.get("statusCheckRollup")),
        "humanComments": len(human_comments), "reviews": reviews,
        "ageDays": lib.days_between(pr["createdAt"], now) if pr.get("createdAt") else 0,
        "idleDays": lib.days_between(pr["updatedAt"], now) if pr.get("updatedAt") else 0,
    }
    rec.update(_mechanical_triage(pr, atype, fails))
    return rec

def build_report_data(raw_prs, repo, since, now):
    prs = [enrich_pr(p, now) for p in raw_prs]
    open_raw = [p for p in raw_prs if p["state"] == "OPEN"]
    def n_state(s):
        return len([p for p in prs if p["state"] == s])
    meta = {
        "repo": repo, "since": since, "generatedAt": lib.iso_now(),
        "totals": {
            "total": len(prs), "open": n_state("OPEN"), "merged": n_state("MERGED"),
            "closed": n_state("CLOSED"),
            "human": len([p for p in prs if p["authorType"] == "human"]),
            "bot": len([p for p in prs if p["authorType"] == "bot"]),
        },
    }
    return {"meta": meta, "checkFailureRates": check_failure_rates(open_raw),
            "prs": sorted(prs, key=lambda p: p["number"], reverse=True)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest scripts/tests/test_enrich.py -q`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/enrich.py scripts/tests/test_enrich.py
git commit -m "feat(midnight-reports): PR enrichment + per-check failure-rate table"
```

---

### Task 4: `render.py` — facts + narrative to HTML fragments

**Files:**
- Create: `plugins/midnight-reports/scripts/render.py`
- Test: `plugins/midnight-reports/scripts/tests/test_render.py`

**Interfaces:**
- Consumes: `report-data.json` shape (Task 3 output), `narrative.json` shape (below).
- Produces:
  - `esc(s) -> str`
  - `render_report(template: str, data: dict, narrative: dict) -> str` — replaces every `<!--MARKER-->` and returns full HTML.
  - Fragment functions: `render_meta`, `render_kpis`, `render_meters`, `render_distro`, `render_themes`, `render_observations`, `render_queue`, `render_table`, `render_watch`, `render_foot`, `render_lede`.
- `narrative.json`: `{ executive_summary: str|list[str], themes: [{name,count,blurb,prs:[int]}], observations: [{tag,kind,title,body_html,meta_prs:[int]}], watch_items: [{severity,title,desc_html}], noise_checks: [str], real_ci_blocked: [int] }`. `kind` ∈ `pattern|caution|win|note`; `severity` ∈ `crit|warn|info`.

The model's CI-noise judgment reaches the rendered report **here**: `render_meters`/`render_queue`/`render_table` read `narrative["noise_checks"]` and `narrative["real_ci_blocked"]`.

- [ ] **Step 1: Write the failing test**

Create `scripts/tests/test_render.py`:

```python
import re
import scripts.render as rd

DATA = {
    "meta": {"repo": "o/n", "since": "2026-07-02", "generatedAt": "2026-07-16T00:00:00+00:00",
             "totals": {"total": 3, "open": 2, "merged": 1, "closed": 0, "human": 2, "bot": 1}},
    "checkFailureRates": [{"name": "Vercel", "failed": 2, "total": 2, "rate": 1.0}],
    "prs": [
        {"number": 9, "title": "Add <thing> & stuff", "url": "https://x/9", "state": "OPEN",
         "isDraft": False, "baseRefName": "main", "author": "alice", "authorType": "human",
         "reviewDecision": "REVIEW_REQUIRED", "additions": 5, "deletions": 1, "changedFiles": 2,
         "failingChecks": [{"name": "Vercel", "conclusion": "FAILURE"}], "ciStatusRaw": "failing",
         "humanComments": 1, "reviews": [], "ageDays": 3, "idleDays": 0,
         "blockedOn": "maintainer", "priority": 3, "action": "Needs a maintainer review"},
        {"number": 8, "title": "CI fix", "url": "https://x/8", "state": "OPEN",
         "isDraft": False, "baseRefName": "main", "author": "app/bot", "authorType": "bot",
         "reviewDecision": "REVIEW_REQUIRED",
         "additions": 2, "deletions": 2, "changedFiles": 1,
         "failingChecks": [{"name": "deploy", "conclusion": "FAILURE"}], "ciStatusRaw": "failing",
         "humanComments": 0, "reviews": [], "ageDays": 9, "idleDays": 0,
         "blockedOn": "author (CI)", "priority": 2, "action": "Fix failing CI checks"},
    ],
}
NARR = {
    "executive_summary": ["Solid two weeks.", "One CI signal is noise."],
    "themes": [{"name": "Docs", "count": 2, "blurb": "New pages", "prs": [9]}],
    "observations": [{"tag": "CI signal", "kind": "caution", "title": "Vercel is noise",
                      "body_html": "Fails on <b>2/2</b> PRs.", "meta_prs": [9]}],
    "watch_items": [{"severity": "warn", "title": "Watch this", "desc_html": "Do the <i>thing</i>."}],
    "noise_checks": ["Vercel"],
    "real_ci_blocked": [8],
}
TEMPLATE = ("<html><body><div id=meta><!--META--></div><div id=lede><!--LEDE--></div>"
            "<div id=kpis><!--KPIS--></div><div id=meters><!--METERS--></div>"
            "<div id=distro><!--DISTRO--></div><div id=themes><!--THEMES--></div>"
            "<div id=obs><!--OBSERVATIONS--></div><div id=queue><!--QUEUE--></div>"
            "<table><tbody><!--TABLE--></tbody></table><div id=watch><!--WATCH--></div>"
            "<footer><!--FOOT--></footer></body></html>")

def test_esc_escapes_html():
    assert rd.esc("a & <b>") == "a &amp; &lt;b&gt;"

def test_render_report_replaces_all_markers():
    out = rd.render_report(TEMPLATE, DATA, NARR)
    assert "<!--" not in out               # every marker consumed
    assert "Add &lt;thing&gt; &amp; stuff" in out   # title escaped
    assert "o/n" in out                    # meta repo present

def test_noise_and_real_ci_blocked_reflected():
    out = rd.render_report(TEMPLATE, DATA, NARR)
    # PR 9's only failing check is Vercel (noise) -> shown green + noise marker, not "fail"
    assert "Ⓥ" in out                 # circled V noise marker for PR 9
    # meters "CI blocked (real)" count comes from real_ci_blocked -> 1
    assert re.search(r'm-num">1<', out)

def test_narrative_sections_present():
    out = rd.render_report(TEMPLATE, DATA, NARR)
    assert "Solid two weeks." in out
    assert "New pages" in out
    assert "Vercel is noise" in out
    assert "Watch this" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest scripts/tests/test_render.py -q`
Expected: FAIL (`No module named 'scripts.render'`).

- [ ] **Step 3: Write `scripts/render.py`**

```python
"""Pure HTML rendering: facts (report-data) + model prose (narrative) -> HTML.

render_report replaces every <!--MARKER--> in the template. The model's CI-noise
judgment enters via narrative['noise_checks'] and narrative['real_ci_blocked'].
"""
import html

_MARKERS = ["META", "LEDE", "KPIS", "METERS", "DISTRO", "THEMES",
            "OBSERVATIONS", "QUEUE", "TABLE", "WATCH", "FOOT"]
_REVIEW = {"APPROVED": ("good", "approved"), "CHANGES_REQUESTED": ("warn", "changes requested"),
           "REVIEW_REQUIRED": ("accent", "review required"), "NONE": ("", "no review")}
_REVIEW_SHORT = {"APPROVED": ("good", "approved"), "CHANGES_REQUESTED": ("warn", "changes req."),
                 "REVIEW_REQUIRED": ("accent", "review req."), "NONE": ("", "—")}
_QCLASS = {1: "p-merge", 2: "p-ci", 3: "p-review", 4: "p-author", 5: "p-bot"}

def esc(s):
    return html.escape("" if s is None else str(s), quote=True)

def _chip(cls, text):
    c = (" " + cls) if cls else ""
    return '<span class="chip%s">%s</span>' % (c, esc(text))

def _open(data):
    return [p for p in data["prs"] if p["state"] == "OPEN"]

def _real_fails(pr, noise):
    return [c for c in pr["failingChecks"] if c["conclusion"] != "PENDING" and c["name"] not in noise]

def _pending(pr):
    return [c for c in pr["failingChecks"] if c["conclusion"] == "PENDING"]

def render_meta(meta):
    gen = meta["generatedAt"][:10]
    return ('<div>Repo <strong>%s</strong></div>'
            '<div>Window <strong>%s → %s</strong></div>'
            '<div>Generated <strong>%s</strong></div>'
            '<button class="theme-toggle" id="themeBtn">◐ Toggle theme</button>'
            % (esc(meta["repo"]), esc(meta["since"]), esc(gen), esc(gen)))

def render_lede(narrative):
    summ = narrative.get("executive_summary") or []
    if isinstance(summ, str):
        summ = [summ]
    paras = "".join("<p>%s</p>" % esc(p) for p in summ)
    return ('<div class="eyebrow">The window in review</div>%s' % paras)

def render_kpis(data):
    t = data["meta"]["totals"]
    resolved = t["merged"] + t["closed"]
    rate = round(t["merged"] / resolved * 100) if resolved else 0
    open_h = len([p for p in _open(data) if p["authorType"] == "human"])
    open_b = t["open"] - open_h
    needs = len([p for p in _open(data) if str(p["blockedOn"]).startswith("maintainer")])
    tiles = [("Open", t["open"], "var(--good)", "<b>%d</b> human · <b>%d</b> bot" % (open_h, open_b)),
             ("Merged", t["merged"], "var(--accent)", "%d%% of resolved PRs landed" % rate),
             ("Closed unmerged", t["closed"], "var(--ink-3)", "superseded / duplicates"),
             ("Needs a maintainer", needs, "var(--warning)", "review, merge or triage")]
    return "\n".join(
        '<div class="tile"><span class="stripe" style="background:%s"></span>'
        '<div class="k-label">%s</div><div class="k-num">%d</div>'
        '<div class="k-sub">%s</div></div>' % (stripe, esc(label), num, sub)
        for label, num, stripe, sub in tiles)

def render_meters(data, narrative):
    o = _open(data)
    approved = len([p for p in o if p["reviewDecision"] == "APPROVED"])
    review_req = len([p for p in o if p["reviewDecision"] == "REVIEW_REQUIRED"])
    changes = len([p for p in o if p["reviewDecision"] == "CHANGES_REQUESTED"])
    real_blocked = len(narrative.get("real_ci_blocked") or [])
    rows = [(approved, "Approved · ready to merge", "var(--good)"),
            (review_req, "Awaiting first review", "var(--accent)"),
            (changes, "Changes requested", "var(--warning)"),
            (real_blocked, "CI blocked (real)", "var(--critical)")]
    return "\n".join(
        '<div class="meter"><span class="dot" style="background:%s"></span>'
        '<div><div class="m-num">%d</div><div class="m-label">%s</div></div></div>'
        % (c, n, esc(l)) for n, l, c in rows)

def render_distro(data):
    t = data["meta"]["totals"]
    total = t["total"] or 1
    segs = [("Merged", t["merged"], "var(--accent)"), ("Open", t["open"], "var(--good)"),
            ("Closed", t["closed"], "var(--ink-3)")]
    bar = "".join(
        '<div class="seg" style="flex:%s;background:%s" title="%s: %d">%s</div>'
        % (n or 0.001, c, esc(l), n, (n if n else "")) for l, n, c in segs)
    leg = "".join(
        '<span><i style="background:%s"></i>%s — <b class="mono">%d</b> (%d%%)</span>'
        % (c, esc(l), n, round(n / total * 100)) for l, n, c in segs)
    return '<div class="bar">%s</div><div class="legend">%s</div>' % (bar, leg)

def render_themes(narrative):
    out = []
    for th in narrative.get("themes") or []:
        prs = "".join('<a class="prref">#%d</a>' % n for n in th.get("prs") or [])
        out.append('<div class="theme"><div class="t-hd"><span class="t-name">%s</span>'
                   '<span class="t-count">%s PRs</span></div><p>%s</p>'
                   '<div class="t-prs">%s</div></div>'
                   % (esc(th["name"]), esc(th.get("count", "")), esc(th.get("blurb", "")), prs))
    return "\n".join(out)

def render_observations(narrative):
    out = []
    for ob in narrative.get("observations") or []:
        kind = ob.get("kind", "note")
        meta = " ".join("#%d" % n for n in ob.get("meta_prs") or [])
        out.append('<div class="insight %s"><span class="i-tag">%s</span>'
                   '<h3>%s</h3><p>%s</p><div class="i-meta">%s</div></div>'
                   % (esc(kind), esc(ob.get("tag", "")), esc(ob.get("title", "")),
                      ob.get("body_html", ""), esc(meta)))
    return "\n".join(out)

def _ci_chip_full(pr, noise):
    real = _real_fails(pr, noise)
    pend = _pending(pr)
    if real:
        return _chip("crit", "CI: " + ", ".join(c["name"] for c in real))
    if pend:
        return _chip("warn", "CI pending: " + ", ".join(c["name"] for c in pend))
    return _chip("good", "CI green")

def render_queue(data, narrative):
    noise = set(narrative.get("noise_checks") or [])
    out = []
    for p in sorted(_open(data), key=lambda x: x["priority"]):
        cls = _QCLASS.get(p["priority"], "p-review")
        rc, rt = _REVIEW.get(p["reviewDecision"], ("", ""))
        author = ("\U0001f916 " if p["authorType"] == "bot" else "") + p["author"]
        foot = (_chip("", author) + _chip(rc, rt) + _ci_chip_full(p, noise)
                + _chip("", "blocked on: " + str(p["blockedOn"]))
                + _chip("", "age %dd · idle %dd" % (p["ageDays"], p["idleDays"])))
        out.append('<div class="qcard %s"><div class="q-top">'
                   '<span class="q-num"><a href="%s" target="_blank" rel="noopener">#%d</a></span>'
                   '<span class="q-action">%s</span></div>'
                   '<div class="q-title"><a href="%s" target="_blank" rel="noopener">%s</a></div>'
                   '<div class="q-foot">%s</div></div>'
                   % (cls, esc(p["url"]), p["number"], esc(p["action"]),
                      esc(p["url"]), esc(p["title"]), foot))
    return "\n".join(out)

def render_table(data, narrative):
    noise = set(narrative.get("noise_checks") or [])
    dash = '<span style="color:var(--ink-3)">—</span>'
    rows = []
    for p in data["prs"]:
        real = _real_fails(p, noise)
        pend = _pending(p)
        if real:
            ci = _chip("crit", "fail")
        elif pend:
            ci = _chip("warn", "pending")
        elif p["ciStatusRaw"] == "passing" or p["failingChecks"]:
            ci = _chip("good", "green")
        else:
            ci = _chip("", "—")
        vnote = ""
        if p["state"] == "OPEN" and any(c["name"] in noise for c in p["failingChecks"]):
            vnote = (' <span title="systemic check failing repo-wide (noise)"'
                     ' style="color:var(--ink-3)">Ⓥ</span>')
        rc, rt = _REVIEW_SHORT.get(p["reviewDecision"], ("", "—"))
        text = esc(("%d %s %s" % (p["number"], p["title"], p["author"])).lower())
        draft = " · draft" if p["isDraft"] else ""
        botspan = ' <span class="bot">bot</span>' if p["authorType"] == "bot" else ""
        files = "%d file%s" % (p["changedFiles"], "" if p["changedFiles"] == 1 else "s")
        review_cell = _chip(rc, rt) if p["state"] == "OPEN" else dash
        ci_cell = (ci + vnote) if p["state"] == "OPEN" else dash
        rows.append(
            '<tr data-state="%s" data-author="%s" data-text="%s">'
            '<td class="c-num"><a href="%s" target="_blank" rel="noopener">#%d</a></td>'
            '<td class="c-title"><div class="t-main">%s</div>'
            '<div class="t-sub">%s · %s</div></td>'
            '<td class="c-author">%s%s</td>'
            '<td><span class="state-pill s-%s"><span class="sq"></span>%s%s</span></td>'
            '<td>%s</td><td>%s</td>'
            '<td class="num"><span class="diff-add">+%d</span> <span class="diff-del">−%d</span></td>'
            '<td class="num">%dd / %dd</td>'
            '<td class="num">%d\U0001f4ac %d✓</td></tr>'
            % (p["state"], p["authorType"], text, esc(p["url"]), p["number"],
               esc(p["title"]), esc(p["baseRefName"]), files, esc(p["author"]), botspan,
               p["state"], p["state"].lower(), draft, review_cell, ci_cell,
               p["additions"], p["deletions"], p["ageDays"], p["idleDays"],
               p["humanComments"], len(p["reviews"])))
    return "\n".join(rows)

def render_watch(narrative):
    out = []
    for w in narrative.get("watch_items") or []:
        out.append('<div class="witem %s"><div class="w-sev"></div><div class="w-body">'
                   '<div class="w-title">%s</div><div class="w-desc">%s</div></div></div>'
                   % (esc(w.get("severity", "info")), esc(w.get("title", "")), w.get("desc_html", "")))
    return "\n".join(out)

def render_foot(data):
    t = data["meta"]["totals"]
    return ('%d PRs · %d open · %d merged · %d closed'
            % (t["total"], t["open"], t["merged"], t["closed"]))

def render_report(template, data, narrative):
    frag = {
        "META": render_meta(data["meta"]), "LEDE": render_lede(narrative),
        "KPIS": render_kpis(data), "METERS": render_meters(data, narrative),
        "DISTRO": render_distro(data), "THEMES": render_themes(narrative),
        "OBSERVATIONS": render_observations(narrative), "QUEUE": render_queue(data, narrative),
        "TABLE": render_table(data, narrative), "WATCH": render_watch(narrative),
        "FOOT": render_foot(data),
    }
    out = template
    for k in _MARKERS:
        out = out.replace("<!--%s-->" % k, frag[k])
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest scripts/tests/test_render.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py scripts/tests/test_render.py
git commit -m "feat(midnight-reports): HTML fragment rendering from facts + narrative"
```

---

### Task 5: `references/template.html` — themed skeleton with markers

**Files:**
- Create: `plugins/midnight-reports/skills/pr-activity-report/references/template.html`
- Source: `docs/superpowers/specs/assets/2026-07-16-pr-report-reference.html` (the validated report from design)

**Interfaces:**
- Consumes: nothing at build time except being read by `render_report`.
- Produces: a template containing exactly these markers, each once: `<!--META--> <!--LEDE--> <!--KPIS--> <!--METERS--> <!--DISTRO--> <!--THEMES--> <!--OBSERVATIONS--> <!--QUEUE--> <!--TABLE--> <!--WATCH--> <!--FOOT-->`.

The reference asset renders all content from an embedded JSON blob via JS. The template instead carries **empty section shells with markers**; Python injects server-rendered HTML, and the JS is reduced to filtering/search/theme-toggle over already-rendered `<tr>` rows.

- [ ] **Step 1: Copy the reference asset as the starting point**

Run from the repo root (creates the references dir, then copies):
```bash
mkdir -p plugins/midnight-reports/skills/pr-activity-report/references
cp docs/superpowers/specs/assets/2026-07-16-pr-report-reference.html \
   plugins/midnight-reports/skills/pr-activity-report/references/template.html
```

- [ ] **Step 2: Keep the entire `<style>` block verbatim**

The reference file has no `<html>`/`<body>` wrapper (the Artifact host adds one); it is `<title>`,
then `<style>`, then `<div class="wrap">...</div>`, then a `<script>`. Keep the `<style>...</style>`
block (design tokens, light/dark themes, all component classes: `.tile .k-num`, `.meter`,
`.distro .seg`, `.qcard`, `.chip` variants, `.state-pill`, `.witem`, `.insight`, `.theme`,
`.lede`, table styles, etc.) exactly as-is. It is already validated. Do not modify it.

- [ ] **Step 3: Replace the `<div class="wrap">` body with the marker skeleton**

Replace the whole `<div class="wrap"> ... </div>` block (everything the JS used to populate) with:

```html
<div class="wrap">
  <header class="masthead">
    <div>
      <div class="brand-eyebrow"><span class="moon"></span>PR Review Watch</div>
      <h1>Pull Request Activity Report</h1>
      <p class="subtitle">Status of every pull request with activity in the window, triaged by what each one is waiting on.</p>
    </div>
    <div class="meta-block"><!--META--></div>
  </header>

  <div class="lede"><!--LEDE--></div>

  <section><div class="sec-head"><h2>At a glance</h2></div>
    <div class="kpis"><!--KPIS--></div></section>

  <section><div class="sec-head"><h2>Open-PR triage</h2></div>
    <div class="meters"><!--METERS--></div></section>

  <section><div class="sec-head"><h2>Window outcomes</h2></div>
    <div class="distro"><!--DISTRO--></div></section>

  <section><div class="sec-head"><h2>What the work was about</h2></div>
    <div class="themes"><!--THEMES--></div></section>

  <section><div class="sec-head"><h2>Observations &amp; commentary</h2></div>
    <div class="insights"><!--OBSERVATIONS--></div></section>

  <section><div class="sec-head"><h2>Action queue</h2></div>
    <div class="queue"><!--QUEUE--></div></section>

  <section><div class="sec-head"><h2>All active PRs</h2></div>
    <div class="toolbar">
      <div class="filters" id="filters">
        <button class="fbtn" data-f="all" aria-pressed="true">All</button>
        <button class="fbtn" data-f="OPEN" aria-pressed="false">Open</button>
        <button class="fbtn" data-f="MERGED" aria-pressed="false">Merged</button>
        <button class="fbtn" data-f="CLOSED" aria-pressed="false">Closed</button>
        <button class="fbtn" data-f="human" aria-pressed="false">Humans only</button>
        <button class="fbtn" data-f="bot" aria-pressed="false">Bots only</button>
      </div>
      <input class="search" id="search" type="search" placeholder="Filter by title, author, #..." aria-label="Search PRs">
    </div>
    <div class="table-scroll"><table>
      <thead><tr><th>PR</th><th>Title</th><th>Author</th><th>State</th><th>Review</th><th>CI</th><th>Size</th><th>Age / Idle</th><th>Disc.</th></tr></thead>
      <tbody id="tbody"><!--TABLE--></tbody>
    </table><div class="empty-note hidden" id="empty">No PRs match this filter.</div></div>
  </section>

  <section><div class="sec-head"><h2>Notes &amp; watch-items</h2></div>
    <div class="watch"><!--WATCH--></div></section>

  <footer><span><!--FOOT--></span><span>Generated by Claude Code · data via GitHub API</span></footer>
</div>
```

- [ ] **Step 4: Replace the trailing `<script>` with filter-only JS**

Delete the old `<script type="application/json" id="data">...</script>` and the content-building `<script>`. Add this single script before `</body>` (or at end of file):

```html
<script>
(function () {
  "use strict";
  var $ = function (s) { return document.querySelector(s); };
  var rows = [].slice.call(document.querySelectorAll("#tbody tr"));
  var stateFilter = "all", search = "";
  function applies(tr) {
    var ok = true;
    if (stateFilter === "human" || stateFilter === "bot") ok = tr.getAttribute("data-author") === stateFilter;
    else if (stateFilter !== "all") ok = tr.getAttribute("data-state") === stateFilter;
    if (ok && search) ok = (tr.getAttribute("data-text") || "").indexOf(search) >= 0;
    return ok;
  }
  function refresh() {
    var shown = 0;
    rows.forEach(function (tr) { var v = applies(tr); tr.classList.toggle("hidden", !v); if (v) shown++; });
    var empty = $("#empty"); if (empty) empty.classList.toggle("hidden", shown > 0);
  }
  var filters = $("#filters");
  if (filters) filters.addEventListener("click", function (e) {
    var b = e.target.closest(".fbtn"); if (!b) return;
    [].slice.call(filters.children).forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
    stateFilter = b.getAttribute("data-f"); refresh();
  });
  var searchEl = $("#search");
  if (searchEl) searchEl.addEventListener("input", function (e) { search = e.target.value.trim().toLowerCase(); refresh(); });
  var themeBtn = $("#themeBtn");
  if (themeBtn) themeBtn.addEventListener("click", function () {
    var cur = document.documentElement.getAttribute("data-theme");
    var next = cur === "dark" ? "light" : cur === "light" ? "dark"
      : (matchMedia("(prefers-color-scheme: dark)").matches ? "light" : "dark");
    document.documentElement.setAttribute("data-theme", next);
  });
  refresh();
})();
</script>
```

- [ ] **Step 5: Verify the template has exactly the 11 markers and no leftover data script**

Run (from repo root):
```bash
f=plugins/midnight-reports/skills/pr-activity-report/references/template.html
for m in META LEDE KPIS METERS DISTRO THEMES OBSERVATIONS QUEUE TABLE WATCH FOOT; do
  c=$(grep -c "<!--$m-->" "$f"); echo "$m=$c"; done
grep -c 'type="application/json"' "$f"
```
Expected: every marker `=1`; the json-script count is `0`.

- [ ] **Step 6: Smoke-test the full render against the template**

Run (from `plugins/midnight-reports/`):
```bash
python3 - <<'PY'
import scripts.render as r
import scripts.tests.test_render as tt
t = open("skills/pr-activity-report/references/template.html").read()
html = r.render_report(t, tt.DATA, tt.NARR)
for m in ["META","LEDE","KPIS","METERS","DISTRO","THEMES","OBSERVATIONS","QUEUE","TABLE","WATCH","FOOT"]:
    assert ("<!--%s-->" % m) not in html, "marker %s not consumed" % m
open("/tmp/mr_smoke.html","w").write(html)
print("rendered", len(html), "bytes; all markers consumed")
PY
```
Expected: prints `rendered <N> bytes; all markers consumed`, no assertion error.

- [ ] **Step 7: Commit**

```bash
git add plugins/midnight-reports/skills/pr-activity-report/references/template.html
git commit -m "feat(midnight-reports): report template with injection markers + filter JS"
```

---

### Task 6: `pr_report.py` CLI — `fetch` (gh shell) + `build`

**Files:**
- Create: `plugins/midnight-reports/scripts/pr_report.py`

**Interfaces:**
- Consumes: `scripts.lib`, `scripts.enrich`, `scripts.render`.
- Produces the CLI: `python3 -m scripts.pr_report fetch --repo <owner/name> --since <iso> [--limit N] --out <path>` and `python3 -m scripts.pr_report build --data <path> --narrative <path> --template <path> --out <path>`.
- The `gh` shell (`_gh_fetch`) is not unit-tested (matches house pattern); `build` reuses the unit-tested `render_report`.

- [ ] **Step 1: Write `scripts/pr_report.py`**

```python
"""CLI: fetch PRs via gh (facts only) and build the HTML report.

Subcommands:
  fetch  --repo owner/name --since YYYY-MM-DD [--limit N] --out report-data.json
  build  --data report-data.json --narrative narrative.json --template template.html --out report.html
"""
import argparse, json, subprocess, sys
from datetime import datetime, timezone
from . import lib, enrich, render

_FIELDS = ("number,title,state,isDraft,author,createdAt,updatedAt,closedAt,mergedAt,"
           "url,labels,baseRefName,additions,deletions,changedFiles,reviewDecision,"
           "comments,reviews,statusCheckRollup")

def _gh_fetch(repo, since, limit):
    search = "updated:>=%s" % since
    proc = subprocess.run(
        ["gh", "pr", "list", "--repo", repo, "--search", search, "--state", "all",
         "--limit", str(limit), "--json", _FIELDS],
        capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)

def cmd_fetch(a):
    repo = lib.parse_repo(a.repo)
    raw = _gh_fetch(repo, a.since, a.limit)
    now = datetime.now(timezone.utc)
    data = enrich.build_report_data(raw, repo, a.since, now)
    with open(a.out, "w") as fh:
        json.dump(data, fh, indent=2)
    print("%d PRs -> %s" % (len(data["prs"]), a.out))

def cmd_build(a):
    data = json.load(open(a.data))
    narrative = json.load(open(a.narrative))
    template = open(a.template).read()
    html = render.render_report(template, data, narrative)
    with open(a.out, "w") as fh:
        fh.write(html)
    print("report -> %s (%d bytes)" % (a.out, len(html)))

def main(argv=None):
    ap = argparse.ArgumentParser(prog="pr_report")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--repo", required=True)
    f.add_argument("--since", required=True, help="ISO date YYYY-MM-DD")
    f.add_argument("--limit", type=int, default=200)
    f.add_argument("--out", required=True)
    f.set_defaults(func=cmd_fetch)
    b = sub.add_parser("build")
    b.add_argument("--data", required=True)
    b.add_argument("--narrative", required=True)
    b.add_argument("--template", required=True)
    b.add_argument("--out", required=True)
    b.set_defaults(func=cmd_build)
    a = ap.parse_args(argv)
    a.func(a)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the CLI wires up (no network)**

Run (from `plugins/midnight-reports/`):
```bash
python3 -m scripts.pr_report --help
python3 -m scripts.pr_report fetch --help
python3 -m scripts.pr_report build --help
```
Expected: each prints usage and exits 0; `fetch` shows `--repo/--since/--limit/--out`, `build` shows `--data/--narrative/--template/--out`.

- [ ] **Step 3: End-to-end `build` smoke test with fixture data**

Run (from `plugins/midnight-reports/`):
```bash
python3 -c "import json,scripts.tests.test_render as tt; json.dump(tt.DATA,open('/tmp/mr_data.json','w')); json.dump(tt.NARR,open('/tmp/mr_narr.json','w'))"
python3 -m scripts.pr_report build --data /tmp/mr_data.json --narrative /tmp/mr_narr.json \
  --template skills/pr-activity-report/references/template.html --out /tmp/mr_report.html
for m in META LEDE KPIS METERS DISTRO THEMES OBSERVATIONS QUEUE TABLE WATCH FOOT; do
  grep -q "<!--$m-->" /tmp/mr_report.html && echo "LEFTOVER $m" || true; done; echo "marker check done"
```
Expected: prints `report -> /tmp/mr_report.html (<N> bytes)` then `marker check done` with no `LEFTOVER` lines.

- [ ] **Step 4: Full test suite green**

Run (from `plugins/midnight-reports/`): `python3 -m pytest scripts/tests -q`
Expected: PASS (all tests from Tasks 2-4).

- [ ] **Step 5: Commit**

```bash
git add scripts/pr_report.py
git commit -m "feat(midnight-reports): pr_report CLI (gh fetch + template build)"
```

---

### Task 7: References — `data-contract.md` + vendored `slack-voice.md`

**Files:**
- Create: `plugins/midnight-reports/skills/pr-activity-report/references/data-contract.md`
- Create: `plugins/midnight-reports/skills/pr-activity-report/references/slack-voice.md`

**Interfaces:**
- Produces: the schemas the model fills (`narrative.json`) and reads (`report-data.json`), and the voice profile loaded only when writing the Slack message.

- [ ] **Step 1: Write `data-contract.md`**

```markdown
# Data contract

Two JSON files flow between the script and the model.

## report-data.json (written by `pr_report.py fetch` — facts only)

- `meta`: `{ repo, since, generatedAt (ISO), totals: {total, open, merged, closed, human, bot} }`
- `checkFailureRates`: `[{ name, failed, total, rate }]` across the **open** PRs. Facts only.
  A high `rate` means a check fails on most open PRs; whether that means "noise" is **your**
  judgment, not the script's.
- `prs[]` (sorted by number desc): `{ number, title, url, state, isDraft, baseRefName, author,
  authorType (bot|human), createdAt, updatedAt, closedAt, mergedAt, reviewDecision, additions,
  deletions, changedFiles, labels[], failingChecks[{name,conclusion}], ciStatusRaw, humanComments,
  reviews[{who,state,at}], ageDays, idleDays, blockedOn, priority, action }`.
  `ciStatusRaw`/`priority`/`blockedOn` are mechanical defaults (priority only orders the queue).

## narrative.json (written by YOU, the model — judgment)

- `executive_summary`: string or list of strings (the lede).
- `themes`: `[{ name, count, blurb, prs: [int] }]` — recurring threads in the window.
- `observations`: `[{ tag, kind, title, body_html, meta_prs: [int] }]`; `kind` ∈
  `pattern | caution | win | note`. `body_html` may contain inline `<b>`, `<a>`, `<em>`, `<span class="mono">`.
- `watch_items`: `[{ severity, title, desc_html }]`; `severity` ∈ `crit | warn | info`.
- `noise_checks`: `[str]` — check names you judge to be systemic noise (demoted out of "real"
  CI-blocked; shown with a marker). Derived from `checkFailureRates` + what each check does.
- `real_ci_blocked`: `[int]` — PR numbers with a genuinely failing (non-noise) check.

Keep `body_html`/`desc_html` self-contained (no scripts, no external URLs except real PR links).
```

- [ ] **Step 2: Write `slack-voice.md` (vendored voice profile)**

Save the slack-casual voice profile **provided in the design conversation** to this path, verbatim, with one change: replace its YAML frontmatter block with the plain-reference header below (so it is a reference doc, not an auto-triggering skill).

Replacement header (use in place of the original `--- ... ---` frontmatter):

```markdown
# Slack voice — slack-casual (reference, not a skill)

> Loaded by SKILL.md ONLY when composing the optional Slack message. Not a registered skill.
> Zero em-dashes. Inclusive, non-gendered language. No AI tropes. Lead with the point.
```

Keep every other section of the provided profile (Quick Reference, Audience, Voice Exemplars, Voice Profile, Voice Markers, Anti-Voice, tropes.fyi catalog, Internal Checks, etc.) unchanged.

- [ ] **Step 3: Sanity-check the vendored file**

Run (from repo root):
```bash
f=plugins/midnight-reports/skills/pr-activity-report/references/slack-voice.md
grep -c "ZERO em-dashes\|zero-tolerance" "$f"   # expect >= 1
head -3 "$f"                                     # expect the reference header, not YAML ---
```
Expected: grep count ≥ 1; the head shows the reference header.

- [ ] **Step 4: Commit**

```bash
git add plugins/midnight-reports/skills/pr-activity-report/references/data-contract.md \
        plugins/midnight-reports/skills/pr-activity-report/references/slack-voice.md
git commit -m "docs(midnight-reports): data contract + vendored slack voice reference"
```

---

### Task 8: `SKILL.md` — the workflow

**Files:**
- Create: `plugins/midnight-reports/skills/pr-activity-report/SKILL.md`

**Interfaces:**
- Consumes: `scripts.pr_report`, the three references, the Artifact tool.
- Produces: the model-facing workflow with the facts/judgment boundary, the Slack rubric, and the D15 output-isolation rule.

- [ ] **Step 1: Write `SKILL.md`**

````markdown
---
name: pr-activity-report
description: This skill should be used to generate a pull-request activity report for a GitHub repository over a timeframe, and to share it. Triggers on "/midnight-reports:pr", "PR report", "pull request report", "PR activity dashboard", "report on open PRs", or a request to summarize/triage a repo's recent pull requests. Fetches PRs via gh, computes CI/triage/age facts, has the model infer CI noise and write narrative, renders a self-contained HTML report, publishes it as an Artifact, and offers a paste-ready Slack message.
---

# PR Activity Report

Generate a self-contained HTML report of a repo's pull-request activity, publish it, and
optionally produce a Slack message. Run scripts from the plugin root
(`${CLAUDE_PLUGIN_ROOT}`). Write run artifacts under
`${CLAUDE_PLUGIN_DATA}/<owner>/<name>/runs/<iso-ts>/`. Never write to the user's cwd.

## The one rule that shapes everything

**The script reports facts. You make the judgments.** The failing-CI numbers, ages, and
review states are facts from `pr_report.py`. Which failing checks are *noise*, what actually
unblocks a PR, and what the two weeks *mean* are yours. Do not push judgment into the script;
do not treat a mechanical `priority` as if it were an assessment.

## Workflow

1. **Preflight.** Confirm `gh auth status` is OK. Resolve args:
   - `<repo>`: pass through `scripts.lib.parse_repo` (accepts `owner/name` or a github URL).
   - `[timeframe]`: default `2w`; resolve with `scripts.lib.resolve_since` (`Nd`/`Nw`/`Nmo` or ISO date).
   - Create the run dir: `RUN="${CLAUDE_PLUGIN_DATA}/<owner>/<name>/runs/<iso-ts>"`.

2. **Fetch (facts).**
   `(cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m scripts.pr_report fetch --repo <owner/name> --since <iso> --out "$RUN/report-data.json")`

3. **Infer CI noise (judgment).** Read `report-data.json` → `checkFailureRates`. Reason about
   each check by name and role. A check that fails on most open PRs regardless of the change
   (e.g. a repo-wide deploy/preview integration) is systemic noise. Record the noise check
   names and the PR numbers that have a genuinely failing (non-noise) check.

4. **Read threads + write narrative (judgment).** For the **open** PRs and the **notable**
   merged/closed ones (approved-but-unmerged, changes-requested, superseded, headline merges),
   read the PR body and review thread with `gh pr view <n> --json ...`. Watch for "ball-in-court"
   nuance (a contributor who already replied to a change request is waiting on the maintainer).
   Write `$RUN/narrative.json` per `references/data-contract.md`: `executive_summary`, `themes`,
   `observations`, `watch_items`, `noise_checks`, `real_ci_blocked`. Keep prose specific and honest.

5. **Build.**
   `(cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m scripts.pr_report build --data "$RUN/report-data.json" --narrative "$RUN/narrative.json" --template "${CLAUDE_PLUGIN_ROOT}/skills/pr-activity-report/references/template.html" --out "$RUN/report.html")`

6. **Publish.** Publish `$RUN/report.html` via the Artifact tool: favicon 🌙, title
   `<owner>/<name> · PR Review Watch`, a one-sentence description.

7. **Report + offer.** Respond with the few most important findings (honestly framed) and the
   Artifact URL + the saved `$RUN/report.html` path. Note here, once, that to share it the user
   must set the artifact to "anyone with the link" via the claude.ai share menu (you cannot do
   this yourself). Then ask whether they want a short, paste-ready Slack message for the team.
   Stop and wait.

8. **Slack message (only if yes).** Load `references/slack-voice.md` and write the message per
   the rubric below, ending with the report link as the **last line**.

   **OUTPUT ISOLATION (hard rule):** your entire response is the message text and nothing else.
   No preamble, no postamble, no follow-up question, no code fence, no "here's your message", no
   sharing reminder (already given in step 7). The user will `/copy` the whole response straight
   into Slack; any stray token gets pasted in front of colleagues.

## Slack content rubric

- Lead with what matters to DevRel: the findings that change what the team does next.
- Flag anything surprising the team likely does not know.
- Flag anything urgent, framed as team-owned and zero-blame. Never attribute a problem to a person.
- Always include one genuine good-news item.
- Give individual cudos only when earned and sparingly; never call out a person negatively.
- Voice: `references/slack-voice.md`. Zero em-dashes, inclusive language, no AI tropes, bullets
  for multi-point content, Slack emoji shortcodes only where they carry tone.

## Notes

- The report is self-contained (inline CSS/JS, no external requests). Do not add external links
  beyond real PR URLs.
- If `gh` returns zero PRs, still build the report (it will read as an empty window) and say so.
````

- [ ] **Step 2: Verify the skill frontmatter parses**

Run (from repo root):
```bash
python3 -c "import io,sys; t=open('plugins/midnight-reports/skills/pr-activity-report/SKILL.md').read(); assert t.startswith('---'); fm=t.split('---',2)[1]; assert 'name: pr-activity-report' in fm and 'description:' in fm; print('frontmatter ok')"
```
Expected: prints `frontmatter ok`.

- [ ] **Step 3: Commit**

```bash
git add plugins/midnight-reports/skills/pr-activity-report/SKILL.md
git commit -m "feat(midnight-reports): pr-activity-report skill workflow"
```

---

### Task 9: `commands/pr.md` (thin wrapper) + `README.md`

**Files:**
- Create: `plugins/midnight-reports/commands/pr.md`
- Create: `plugins/midnight-reports/README.md`
- Modify: `README.md` (repo root — add a Plugins-table row)

**Interfaces:**
- Consumes: the `pr-activity-report` skill.
- Produces: the `/midnight-reports:pr` command surface.

- [ ] **Step 1: Write `commands/pr.md`**

```markdown
---
description: Generate a self-contained HTML pull-request activity report for a GitHub repo over a timeframe, publish it as an Artifact, and optionally produce a paste-ready Slack message. Accepts owner/name or a github.com URL; timeframe defaults to 2 weeks.
argument-hint: "<repo> [timeframe]  e.g. midnightntwrk/midnight-docs 2w"
---

Load the `pr-activity-report` skill and run its workflow.

Arguments:
- `$1` = repository, as `owner/name` or a `github.com/owner/name[/...]` URL (required).
- `$2` = timeframe, one of `Nd` / `Nw` / `Nmo` or `YYYY-MM-DD` (optional; default `2w`).

Normalize `$1` with `scripts.lib.parse_repo` and resolve `$2` with `scripts.lib.resolve_since`
(from `${CLAUDE_PLUGIN_ROOT}`), echo the resolved `owner/name` and `since` date, then follow the
skill's workflow end to end (fetch facts → infer CI noise → read threads and write narrative →
build → publish → report + offer Slack message). Honor the skill's Slack output-isolation rule.

If `$1` is missing, ask for the repository and stop.
```

- [ ] **Step 2: Write `README.md`**

```markdown
# midnight-reports

Generate PR-activity reports for any GitHub repository.

## `/midnight-reports:pr <repo> [timeframe]`

Fetches every pull request with activity in the timeframe (default 2 weeks), then produces a
self-contained, themed HTML report: KPI tiles, open-PR triage, an action queue ranked by what
unblocks each PR, a filterable table of all active PRs, plus a narrative layer (executive
summary, themes, observations, watch-items). The report is published as an Artifact and saved
under the plugin data dir. After publishing, the command offers a paste-ready Slack summary.

- `<repo>`: `owner/name` or a `github.com/owner/name` URL.
- `[timeframe]`: `Nd` / `Nw` / `Nmo` or `YYYY-MM-DD` (default `2w`).

### Design

The work splits along a facts/judgment boundary. `scripts/pr_report.py` (pure `lib`/`enrich`/
`render` modules + a thin `gh` shell) reports facts and renders HTML from
`skills/pr-activity-report/references/template.html`. The model infers which failing CI checks
are systemic noise, reads PR threads to write the narrative, publishes, and writes the Slack
message in the vendored `slack-voice.md` voice.

### Requirements

- `gh` CLI, authenticated (`gh auth status`).
- Python 3 (stdlib only).

### Tests

`cd plugins/midnight-reports && python3 -m pytest scripts/tests -q`
```

- [ ] **Step 3: Add a Plugins-table row to the repo-root `README.md`**

In `README.md`, add this row to the `## Plugins` table (after the `gha` row):

```markdown
| [`midnight-reports`](./plugins/midnight-reports) | Generates self-contained HTML pull-request activity reports for any GitHub repo (`/midnight-reports:pr <repo> [timeframe]`): metrics dashboard, action queue, and narrative commentary, published as an Artifact, with an optional paste-ready Slack summary. |
```

- [ ] **Step 4: Validate command frontmatter + plugin structure**

Run (from repo root):
```bash
python3 -c "t=open('plugins/midnight-reports/commands/pr.md').read(); assert t.startswith('---') and 'description:' in t.split('---',2)[1]; print('command ok')"
bash scripts/ci/validate.sh
```
Expected: `command ok`, and validation passes (exit 0).

- [ ] **Step 5: Commit**

```bash
git add plugins/midnight-reports/commands/pr.md plugins/midnight-reports/README.md README.md
git commit -m "feat(midnight-reports): /midnight-reports:pr command + README"
```

---

### Task 10: Marketplace CI — shared Python test runner + contributor docs

This plugin is the first with CI-run Python tests. Add **one shared runner** for the whole
marketplace (not a per-plugin workflow) that auto-discovers and runs any plugin's Python tests,
and document the opt-in convention for contributors.

**Files:**
- Create: `scripts/ci/run-python-tests.sh`
- Modify: `.github/workflows/validate.yml` (add a `python-tests` job)
- Modify: `README.md` (repo root — add "Adding Python tests to your plugin")

**Interfaces:**
- Produces: `bash scripts/ci/run-python-tests.sh` — runs `python3 -m pytest` from each plugin
  root that contains `test_*.py`; exits non-zero if any plugin's tests fail.

- [ ] **Step 1: Write `scripts/ci/run-python-tests.sh`**

```bash
#!/usr/bin/env bash
# run-python-tests.sh - One shared runner for the whole marketplace.
# Runs pytest from each plugin root that contains test_*.py, so `import scripts.*`
# resolves and each plugin's tests run isolated from its siblings. A plugin opts in
# simply by adding test_*.py (see README "Adding Python tests to your plugin").
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGINS_DIR="$ROOT/plugins"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2; exit 1
fi
if ! python3 -m pytest --version >/dev/null 2>&1; then
  echo "pytest not installed (pip install pytest)" >&2; exit 1
fi

any=0; failed=0; summary=()
for plugin in "$PLUGINS_DIR"/*/; do
  name="$(basename "$plugin")"
  if find "$plugin" -name 'test_*.py' -not -path '*/node_modules/*' -print -quit | grep -q .; then
    any=1
    echo "==> pytest: $name"
    if ( cd "$plugin" && python3 -m pytest -q ); then
      summary+=("$name: PASS")
    else
      summary+=("$name: FAIL"); failed=1
    fi
  fi
done

echo ""
echo "== Python test summary =="
if [ "$any" = 0 ]; then
  echo "No plugin Python tests found."
  exit 0
fi
for line in "${summary[@]}"; do echo "  $line"; done
if [ "$failed" = 0 ]; then echo "All plugin Python tests passed."; else echo "Some plugin Python tests FAILED."; fi
exit "$failed"
```

- [ ] **Step 2: Make it executable and run it locally**

Run (from repo root):
```bash
chmod +x scripts/ci/run-python-tests.sh
bash scripts/ci/run-python-tests.sh
```
Expected: runs `midnight-docs-drift` (21 passed) and `midnight-reports` (all Tasks 2-4 tests),
prints a summary ending `All plugin Python tests passed.`, exits 0.

- [ ] **Step 3: Add a `python-tests` job to `.github/workflows/validate.yml`**

Append this job under `jobs:` (a sibling of the existing `validate` job, same indentation):

```yaml
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install pytest
        run: python -m pip install --upgrade pip pytest

      - name: Run plugin Python tests
        run: bash scripts/ci/run-python-tests.sh
```

- [ ] **Step 4: Add the contributor section to the repo-root `README.md`**

Insert this section before `## License`:

````markdown
## Adding Python tests to your plugin

CI runs one shared runner (`scripts/ci/run-python-tests.sh`) that discovers and runs Python
tests for every plugin. There is no per-plugin workflow to set up. To opt in:

1. Put importable code in `plugins/<name>/scripts/` as a package (add an empty `scripts/__init__.py`).
2. Put tests in `plugins/<name>/scripts/tests/` (with an empty `__init__.py`) or
   `plugins/<name>/tests/`, named `test_*.py`, importing your code via the `scripts` package
   (e.g. `import scripts.mymodule as m`).
3. That is all. The runner does `cd plugins/<name> && python3 -m pytest` for any plugin containing
   `test_*.py`, so `import scripts.*` resolves and each plugin's tests run isolated from siblings.

Run them all locally the same way CI does:

```
bash scripts/ci/run-python-tests.sh
```
````

- [ ] **Step 5: Verify the workflow YAML is valid**

Run (from repo root):
```bash
python3 -c "import sys; 
try:
    import yaml; yaml.safe_load(open('.github/workflows/validate.yml')); print('yaml ok (pyyaml)')
except ImportError:
    print('pyyaml absent; skipping strict parse')"
grep -q 'python-tests:' .github/workflows/validate.yml && echo 'job present'
```
Expected: `job present` (and `yaml ok` if PyYAML is available).

- [ ] **Step 6: Commit**

```bash
git add scripts/ci/run-python-tests.sh .github/workflows/validate.yml README.md
git commit -m "ci: shared Python test runner for all plugins + contributor docs"
```

---

### Task 11: Final verification

**Files:** none (verification + optional live run).

- [ ] **Step 1: Full local gate**

Run (from repo root):
```bash
bash scripts/ci/run-python-tests.sh
bash scripts/ci/validate.sh
```
Expected: the shared runner reports `All plugin Python tests passed.` (midnight-docs-drift +
midnight-reports); structural validation exits 0 with `midnight-reports` listed as validated.

- [ ] **Step 2 (optional, network): live dry-run of fetch**

If `gh` is authenticated, confirm the fetch shell works end to end against a small window.
Run (from `plugins/midnight-reports/`):
```bash
SINCE="$(python3 -c "import scripts.lib as l; from datetime import datetime, timezone; print(l.resolve_since('1w', datetime.now(timezone.utc)))")"
python3 -m scripts.pr_report fetch --repo midnightntwrk/midnight-docs --since "$SINCE" --out /tmp/mr_live.json
python3 -c "import json; d=json.load(open('/tmp/mr_live.json')); print('repo', d['meta']['repo'], 'prs', len(d['prs']), 'checks', len(d['checkFailureRates']))"
```
Expected: prints a repo, a PR count, and a check count without error. (Skip if offline.)

- [ ] **Step 3: Confirm the branch is clean and push-ready**

Run: `git status --short && git log --oneline -12`
Expected: clean working tree; the task commits present on `feat/midnight-reports-plugin`.

---

## Self-Review (completed during planning)

- **Spec coverage:** D1 (Task 1 naming), D2 (Task 9 thin command), D3 (Tasks 3/4 facts-only + mechanical triage), D4 (Tasks 4-6 render pipeline), D5/D6 (Task 2 parsing), D7 (Task 5 repo-agnostic identity), D9 (Task 8 output paths + Task 6 build), D10 (Tasks 2-4 tests), D11 (Task 8 step 7 report+offer), D12 (Task 8 step 7 reminder placement), D13 (Task 7 vendored voice), D14 (Task 8 rubric), D15 (Task 8 step 8 output isolation). §6a rubric → Task 8. §7 contracts → Tasks 3/4/7.
- **Mid-plan requirement (shared CI Python runner):** Task 10 adds one marketplace-wide runner
  (`scripts/ci/run-python-tests.sh`) that discovers and runs every plugin's `test_*.py` from that
  plugin's root, a `python-tests` CI job, and a contributor README section — no per-plugin
  workflow. Verified locally that the only existing sibling with Python tests
  (`midnight-docs-drift`, 21 tests) passes, so the runner is green on day one.
- **Placeholder scan:** no TBD/TODO; every code step carries complete code. The vendored `slack-voice.md` (Task 7 step 2) points at a large external asset already provided in the conversation; the transformation (frontmatter → reference header) is given exactly.
- **Type consistency:** `report-data.json` fields produced in Task 3 (`failingChecks[{name,conclusion}]`, `ciStatusRaw`, `blockedOn`, `priority`, `ageDays`, `idleDays`) are consumed unchanged in Task 4 render functions and the Task 4 test. `narrative.json` keys (`noise_checks`, `real_ci_blocked`, `observations[].kind`, `watch_items[].severity`) match between Task 4 render, Task 7 contract, and Task 8 workflow.
- **Task boundaries:** Tasks 2-4 are independently testable (pure modules + TDD); Task 5 (template) and Task 6 (CLI) each end in a runnable smoke test; Task 10 (shared CI) is independently verifiable via the local runner. Each task ends green and committable.
