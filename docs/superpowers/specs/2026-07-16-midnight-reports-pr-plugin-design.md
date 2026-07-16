# Design: `midnight-reports` plugin — `/midnight-reports:pr`

- **Date:** 2026-07-16
- **Status:** Draft (awaiting spec review)
- **Repo:** `devrelaicom/midnight-devrel-expert`

## 1. Summary

A new Claude Code plugin, **`midnight-reports`**, housed in this marketplace. Its
first (and, for now, only) capability is a command **`/midnight-reports:pr`** that
produces a **self-contained, themed HTML report** of a GitHub repository's pull-request
activity over a timeframe. The report keeps the metrics dashboard (KPI tiles, open-PR
triage meters, outcome distribution, a priority-ranked action queue, a filterable table
of every active PR) **and** adds a narrative layer (executive summary, recurring themes,
observations/commentary, and watch-items) — i.e. the artifact produced by hand in the
originating session, turned into a repeatable tool.

The work splits cleanly along a **facts vs. judgment** boundary:

- A deterministic Python helper (`pr_report.py`) fetches PRs via `gh`, strips bot-comment
  noise, computes enrichment (bot detection, ages, review state, per-PR failing checks,
  and an aggregate **per-check failure-rate table**), and renders the final HTML. The
  script reports facts; it never decides what a fact *means*.
- The **model** (driven by the `pr-activity-report` skill) reads the failure-rate table
  and **infers** which failing checks are systemic noise, reads the PR threads for the
  open and notable PRs, and writes the narrative. It then runs the renderer and publishes.

The command is a **thin wrapper** around the skill so the same workflow is equally
invocable by a human (`/midnight-reports:pr owner/name 2w`) or by the model on its own.

## 2. Goals / Non-goals

**Goals**
- One command that takes `<repo> [timeframe]` and produces a polished, self-contained
  HTML PR-activity report, published as an Artifact and saved to the plugin data dir.
- Accept `<repo>` as `owner/name` **or** a `github.com/owner/name[/...]` URL.
- Default the timeframe to **2 weeks**; also accept `Nd` / `Nw` / `Nmo` and ISO dates.
- Keep the deterministic data + rendering work in a **testable script**; keep the
  inference (CI-noise, narrative) in the **model**.
- Work for **any** public/accessible GitHub repo, not just Midnight repos.

**Non-goals**
- Not a live/served dashboard; each run emits one static HTML snapshot.
- The script does **not** classify CI failures as "noise" — that is model judgment.
- Not a general analytics warehouse; scope is one repo, one timeframe, per run.
- No write operations on the target repo (read-only via `gh`).

## 3. Key decisions (decision log)

| # | Decision |
|---|---|
| D1 | Plugin name is **`midnight-reports`** (plural); command namespace therefore is **`/midnight-reports:pr`**. Plugin name and command prefix must match. |
| D2 | **Command is a thin wrapper**: it parses/normalizes args and loads the `pr-activity-report` skill, which owns the whole workflow. Model-invocable via the skill directly. |
| D3 | **Script reports facts, model makes judgments.** `pr_report.py` emits a per-check failure-rate table but assigns **no** "noise" verdict. The model infers systemic-noise checks and the honest "real CI-blocked" count. |
| D4 | **Approach A rendering**: `pr_report.py build` renders the final HTML from a committed `references/template.html` + `report-data.json` (facts) + `narrative.json` (model prose). The 70 KB of CSS/JS boilerplate lives once in the template; every run is deterministic. |
| D5 | `<repo>` accepts `owner/name` or any `github.com/owner/name[/...]` URL → normalized to `owner/name`. Invalid input fails fast with a clear message. |
| D6 | Timeframe accepts `Nd`/`Nw`/`Nmo` or an ISO date (`YYYY-MM-DD`); **default `2w`**. Converted to an ISO cutoff used in `gh`'s `updated:>=` search qualifier. |
| D7 | Report identity is a repo-agnostic **"review watch"** dashboard (the moon = *watch*), parameterized by repo name — honest for any repo, not Midnight-branded. |
| D8 | Narrative depth is bounded: the model reads threads for **open + notable** PRs (changes-requested, superseded, headline merges), not all PRs, to control cost. |
| D9 | Output is **both** a published Artifact (via the Artifact tool) **and** a saved file under `${CLAUDE_PLUGIN_DATA}/<owner>/<name>/runs/<iso-ts>/`. Nothing written to cwd. |
| D10 | `pr_report.py` gets **fixture-based unit tests** (saved `gh` JSON → assert enrichment + arg parsing), consistent with sibling plugins and marketplace CI. |

## 4. Plugin layout

```
plugins/midnight-reports/
  .claude-plugin/plugin.json                 # metadata (name, version, description, keywords)
  commands/
    pr.md                                     # thin wrapper: normalize args -> load skill
  skills/
    pr-activity-report/
      SKILL.md                                # workflow + rubrics (facts/judgment boundary, narrative rubric)
      references/
        template.html                         # themed, interactive skeleton with injection markers
        data-contract.md                      # report-data.json + narrative.json schemas
  scripts/
    pr_report.py                              # fetch | build subcommands
    tests/
      test_pr_report.py                       # fixture-based unit tests
      fixtures/
        gh-prs.sample.json                    # captured gh output for tests
  README.md
```

Plus one entry appended to `.claude-plugin/marketplace.json`:

```json
{ "name": "midnight-reports", "source": "./plugins/midnight-reports" }
```

## 5. Invocation & argument parsing

`/midnight-reports:pr <repo> [timeframe]`

- **`<repo>`** (required): `owner/name` or `https://github.com/owner/name[/tree/...]`.
  Normalization strips scheme/host/trailing path and validates `^[\w.-]+/[\w.-]+$`.
- **`[timeframe]`** (optional, default `2w`): one of
  - `Nd` (days), `Nw` (weeks), `Nmo` (months) — relative to *now*;
  - `YYYY-MM-DD` — an absolute cutoff.
  Resolved to an ISO date `since` passed to `gh` as `updated:>=<since>`.

The command body (`pr.md`) does minimal work: echo the resolved `owner/name` + `since`,
then hand off to the skill. All real logic lives in the skill + script.

## 6. Workflow (in `SKILL.md`)

1. **Preflight.** Confirm `gh auth status`; normalize/validate args; resolve `since`.
2. **Fetch (script).**
   `python3 -m scripts.pr_report fetch --repo <owner/name> --since <iso> --out <run>/report-data.json`
   Emits all per-PR facts + the aggregate `checkFailureRates` table. Bot-comment noise
   (vercel, github-actions, dependabot, renovate, coderabbit, CLA assistant) stripped from
   discussion counts.
3. **CI-noise inference (model).** Read `checkFailureRates`; reason about each check's
   name/role; decide which failing checks are systemic noise vs. real. Produce the honest
   "real CI-blocked" set. **Not** a script threshold.
4. **Narrative (model).** Read PR threads for open + notable PRs; write `narrative.json`:
   `executive_summary`, `themes[]`, `observations[]`, `watch_items[]`, plus the
   `noise_checks[]` / `real_ci_blocked[]` decision and any "ball-in-court" nuances.
5. **Build (script).**
   `python3 -m scripts.pr_report build --data <run>/report-data.json --narrative <run>/narrative.json --out <run>/report.html`
6. **Publish (model).** Publish `report.html` via the Artifact tool (favicon 🌙, title
   `<repo> · PR Review Watch`); report the URL and the saved path to the user.

## 7. Script — I/O contracts

### `pr_report.py fetch`
- **In:** `--repo owner/name`, `--since <iso-date>`, `--out <path>`.
- **Does:** `gh pr list --repo <r> --search "updated:>=<since>" --state all --limit <N> --json …`
  (number, title, state, isDraft, author, timestamps, reviewDecision, additions, deletions,
  changedFiles, labels, comments, reviews, statusCheckRollup). Enriches each PR.
- **Out (`report-data.json`):**
  - `meta`: `{ repo, since, generatedAt, totals: {open, merged, closed, human, bot} }`
  - `checkFailureRates`: `[{ name, failed, total, rate }]` computed **across the open PRs**
    (the set whose CI status is actionable) — **facts only**, no verdict.
  - `prs[]`: `{ number, title, url, state, isDraft, author, authorType(bot|human),
    createdAt, updatedAt, closedAt, mergedAt, reviewDecision, additions, deletions,
    changedFiles, labels[], failingChecks[{name,conclusion}], ciStatusRaw, humanComments,
    reviews[{who,state,at}], ageDays, idleDays }`.
  - `ciStatusRaw` is derived only from actual check conclusions (no noise judgment). A
    mechanical `blockedOn`/`priority` MAY be provided **solely to order the action queue**
    deterministically; the *interpretive* framing (what actually unblocks each PR, the
    ball-in-court nuance) lives in the model's narrative sections, never by rewriting the
    queue data.

### `pr_report.py build`
- **In:** `--data report-data.json`, `--narrative narrative.json`, `--out report.html`.
- **Does:** load `references/template.html`; render fact-driven sections (KPIs, meters,
  distribution, action queue, table) from `report-data.json`; render narrative sections
  (lede, themes, observations, watch-items) from `narrative.json`; inject at markers.
- **Out:** one self-contained HTML file (inlined CSS/JS, no external requests, light+dark,
  filterable table, theme toggle).

### `narrative.json` (written by the model)
`{ executive_summary: str|str[], themes: [{name, count, blurb, prs[]}],
   observations: [{tag, kind(pattern|caution|win|note), title, body_html, meta_prs[]}],
   watch_items: [{severity(crit|warn|info), title, desc_html}],
   noise_checks: [str], real_ci_blocked: [pr_number] }`

## 8. State & output layout

- Per-run artifacts under **`${CLAUDE_PLUGIN_DATA}/<owner>/<name>/runs/<iso-ts>/`**:
  `report-data.json`, `narrative.json`, `report.html`.
- Nothing is written into the current working directory.

## 9. Testing approach

- `tests/test_pr_report.py` runs against `fixtures/gh-prs.sample.json` (captured real output):
  - **Arg parsing:** `owner/name`, full URL, `/tree/...` URL → normalized; bad input rejected.
  - **Timeframe:** `2w` default, `10d`, `3mo`, ISO date → correct `since`.
  - **Enrichment:** bot vs. human classification; `ageDays`/`idleDays` math; bot-comment
    stripping; `failingChecks` extraction; `checkFailureRates` aggregation (counts correct,
    **no** noise verdict emitted).
  - **Build:** `build` on sample data + a minimal `narrative.json` yields valid, self-contained
    HTML (well-formed, all markers replaced, no external URLs).
- Wired into the existing marketplace validation CI the same way sibling plugin tests are.

## 10. Open questions / future

- Additional report types under the same plugin (e.g. `issues`, `releases`) — the plural
  name leaves room; out of scope now.
- Multi-repo / org-wide rollups — explicitly deferred.
- Auto-refresh / scheduled runs (via `/loop` or a routine) — a usage pattern, not built in.
