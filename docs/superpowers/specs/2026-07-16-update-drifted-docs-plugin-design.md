# Design: `/update-drifted-docs` plugin

- **Date:** 2026-07-16
- **Status:** Draft (awaiting spec review)
- **Repo:** `devrelaicom/midnight-devrel-expert`

## 1. Summary

A Claude Code plugin housed in this repo that adds a single interactive command,
`/update-drifted-docs`, which detects and repairs **documentation drift** in the
`midnightntwrk/midnight-docs` site. "Drift" = a docs page that was last edited
*before* the source repo(s) it describes were last published, and whose factual
claims may therefore be stale.

The command orchestrates a multi-stage pipeline with user checkpoints between
stages, reusing the installed `midnight-expert` plugin family for the claim work
(`midnight-fact-check` for extraction/classification, `midnight-verify` for
verification) and shipping its own deterministic scripts for the drift-specific
stages (repo scan, docs→repo mapping, drift detection, severity).

This session's `.research/` artifacts are the reference implementation.

## 2. Goals / Non-goals

**Goals**
- One command, run from inside a `midnight-docs` checkout, that takes a maintainer
  from "which docs have drifted?" to "PR that fixes the refuted claims."
- Interactive: a user gate between every consequential stage (regenerate caches?
  exclude files? what to verify? fix? push/PR?).
- Cheap re-runs via caching (repo list, docs→repo map) and optional path scoping.
- Reuse, not reimplement, the sibling plugins' claim/verify machinery.

**Non-goals**
- Not a general-purpose docs linter; it is Midnight/`midnight-docs`-specific.
- Does not reimplement claim extraction, classification, or verification.
- Does not auto-fix without explicit user approval and (optional) re-verification.

## 3. Key decisions (decision log)

| # | Decision |
|---|---|
| D1 | Plugin lives in `devrelaicom/midnight-devrel-expert`; **reuses** `midnight-fact-check` + `midnight-verify` as soft dependencies (assumed installed). |
| D2 | Run **from inside a `midnight-docs` checkout** (cwd). Optional positional `path` arg scopes the whole run to a subtree (e.g. `docs/tutorials/bboard`). |
| D3 | State lives under **`${CLAUDE_PLUGIN_DATA}`**, keyed by org + docs-repo remote. Nothing is written into the docs working tree. |
| D4 | The command **owns the flow + all interactive gates**; it dispatches the siblings' agents (`claim-extractor`, `domain-classifier`) and calls `/midnight-verify:verify`, rather than delegating to the autonomous `/midnight-fact-check:check`. |
| D5 | Re-verifying a fix before commit is **offered as a prompt** during the fix stage, not done automatically. |
| D6 | Fixes land on **one `fix/<slug>` branch**; commit granularity is a judgement call — a substantial single fix may be its own commit, or several small fixes to one file may be rolled into one per-file commit. |
| D7 | Repo-list cache is considered stale after **14 days** (always show generated-at and let the user decide regardless). |
| D8 | Config is **overridable by flags**. The repo list always includes the cross-org repo **`LFDT-Minokawa/compact`** (the real Compact compiler source) in addition to active `midnightntwrk` repos. |
| D9 | Verification subset (stage 6) offers presets **and** a user-specified custom subset. |

## 4. Plugin layout

```
midnight-devrel-expert/
  .claude-plugin/plugin.json          # metadata; documents soft-deps on midnight-fact-check + midnight-verify
  commands/
    update-drifted-docs.md            # orchestrator prompt (owns all gates + stage sequencing)
  scripts/
    repo_scan.py                      # gh GraphQL org scan -> active repo list (+ extra cross-org repos)
    build_map.py                      # deterministic tech/tool + repo-URL -> repo inference
    drift_detect.py                   # release-else-HEAD publish date vs per-file git mtime
    severity_pass.py                  # heuristic blast-radius severity (high/medium/low)
    aggregate.py                      # merge per-batch claim JSON, produce summaries
  skills/
    docs-drift-methodology/           # rubrics: active-repo criteria, repo-reference rules,
                                      #   drift semantics, severity tiers, mapping guidance for agents
```

- **Deterministic work → scripts.** Repo scan, drift math, severity, aggregation are
  pure functions of git/GitHub state and are shipped as reproducible Python.
- **Judgement work → agents/siblings.** Docs→repo mapping (reading pages), claim
  extraction, classification, verification, and fixing are agent-driven.
- **`docs-drift-methodology` skill** encodes the rubrics the command and its dispatched
  agents follow, so behavior is documented and tunable in one place.

## 5. Configuration & flags

Defaults, each overridable by a command flag:

| Setting | Default | Flag |
|---|---|---|
| Org | `midnightntwrk` | `--org` |
| Extra (cross-org) repos | `["LFDT-Minokawa/compact"]` | `--extra-repo` (repeatable) |
| Active-repo window | 6 months | `--since` |
| Repo-list staleness TTL | 14 days | `--repos-ttl` |
| Docs repo | auto-detected from cwd git remote | `--docs-remote` |
| Path scope | whole `docs/` | positional `path` arg |
| Map policy | prompt | `--remap {all,new,reuse}` |

Persistent config may also live in a plugin settings file; flags win over settings,
settings win over defaults.

## 6. Invocation & preflight

`/update-drifted-docs [path] [flags]`

Preflight (fail fast with actionable messages):
1. cwd is a git repo whose remote matches the configured docs repo (else offer to `--docs-remote` or cd).
2. `gh auth status` OK with org read scope.
3. `midnight-fact-check` and `midnight-verify` plugins resolvable (else explain how to install).
4. Resolve `path` scope to a set of eligible files (`*.mdx`/`*.md`, excluding `_`-prefixed and, by default, `relnotes/`).

## 7. Pipeline stages

Each stage lists: **input → action (script/agent/command) → output/cache → gate**.

**Stage 1 — Repo list.**
Load `${CLAUDE_PLUGIN_DATA}/<org>/repos.json`. If present, show its `generated_at`
and whether it is within the 14-day TTL. **Gate:** regenerate or reuse. On
regenerate/absent → `repo_scan.py` (gh GraphQL, active-repo filter: not archived,
not empty/scaffold-only, commit within window) **plus** the configured extra repos
(`LFDT-Minokawa/compact`). Write cache with `generated_at`.

**Stage 2 — Docs→repo map.**
Load `${CLAUDE_PLUGIN_DATA}/<docs-repo>/docs-repo-map.json`. Diff its keys against
the current scoped doc files. **Gate:** if new/removed pages exist → *remap all* vs
*only new pages*; if none → *remap* vs *use existing*. Mapping action: dispatch
reader agents over the target pages (extract referenced tech/tools + explicit repo
URLs, per the methodology skill) then `build_map.py` infers the relevant repos from
the stage-1 repo list (linked = explicit URL; inferred = component→repo). Update cache.

**Stage 3 — Drift detect.**
`drift_detect.py`: for each mapped repo compute last-published (latest release
`published_at`, else default-branch HEAD `committedDate`); for each scoped doc read
its last-modified via git; flag pages whose mtime predates any mapped repo's publish.
Output `runs/<ts>/drift.json`.

**Stage 4 — Drift summary + gate.**
Render each drifted page → the repo(s) published more recently (date + release/push).
**Gate:** exclude any files, or continue with all → apply exclusions to the working set.

**Stage 5 — Claims.**
Over the (possibly reduced) drifted set: dispatch `midnight-fact-check`'s
`claim-extractor` agents in parallel batches, then `domain-classifier`, then
`severity_pass.py`. `aggregate.py` merges to `runs/<ts>/claims/` + `severity.json`.

**Stage 6 — Claims summary + gate.**
Present counts as domain × severity. **Gate:** verify *all*, a **preset subset**
(high-severity only · one domain · one page/subtree · high+medium excluding
unclassified), or a **user-specified custom subset**.

**Stage 7 — Verify.**
Run `/midnight-verify:verify` over the selected claims. Collect
supported / refuted / inconclusive with evidence, to `runs/<ts>/verify-report.md`.

**Stage 8 — Report + gate.**
Present the verification report. **Gate:** offer to fix the refuted claims.

**Stage 9 — Fix → PR (if accepted).**
1. Ask clarifying questions about ambiguous/underspecified refuted claims.
2. Ensure `main` is current (`git fetch`, fast-forward/rebase as appropriate).
3. Create `fix/<slug>` branch.
4. Apply edits. Commit with judgement (per-fix vs per-file rollup) on the one branch.
5. **Gate:** offer to re-verify each fix before finalizing (D5).
6. **Gate:** offer to push and open a PR (`gh pr create`) with a body listing the
   fixed claims and their evidence.

## 8. State & caching layout

```
${CLAUDE_PLUGIN_DATA}/
  <org>/repos.json                      # {generated_at, window, repos:[{name,url,last_commit,desc,...}]}
  <docs-repo>/docs-repo-map.json        # {generated_at, pages:{path:{linked:[],inferred:[]}}}
  <docs-repo>/runs/<iso-ts>/
    drift.json                          # {page:{doc_modified, behind:[{repo,published,method}]}}
    claims/claims-batch-*.json          # extractor output + domain + severity
    severity.json                       # aggregate severity breakdown
    verify-report.md                    # stage-7 results
    fixes.json                          # applied edits + re-verify status (if fix stage ran)
```

Persistent caches survive runs; per-run dirs give inspectability and resumability
(a re-run can detect an in-progress run and offer to resume from the last completed stage).

## 9. Reuse contracts (sibling dependencies)

| Need | Reused from | How invoked |
|---|---|---|
| Claim extraction | `midnight-fact-check` `claim-extractor` agent + `fact-check-extraction` skill | Dispatch agents in parallel batches from the command |
| Domain classification | `midnight-fact-check` `domain-classifier` agent + `fact-check-classification` skill | Dispatch after extraction |
| Verification | `midnight-verify` `/verify` command | `SlashCommand` per selected claim/subset |

If a sibling is missing/incompatible, preflight explains the fix; the command does
**not** silently reimplement it.

## 10. Scripts — I/O contracts (reference impl exists in this session's `.research/`)

- **`repo_scan.py`** → `repos.json`. GraphQL over org (paginated, ordered by
  `PUSHED_AT`), enrich with `committedDate`/tree to drop scaffold-only repos, append
  extra cross-org repos. Deterministic, no LLM.
- **`build_map.py`** → updates `docs-repo-map.json`. Input: per-page tech/tool + repo
  URLs (from reader agents) + `repos.json`. Output: `{linked, inferred}` per page.
- **`drift_detect.py`** → `drift.json`. Requires full git history (unshallow if the
  checkout is shallow). Release-else-HEAD publish date; per-file `git log -1 %cI`.
- **`severity_pass.py`** → adds `severity` + `severity_signal` to each claim.
  Heuristic = blast-radius if stale/wrong (code-exact → high; named-construct
  behaviour → medium; conceptual → low). Rubric documented in the methodology skill.
- **`aggregate.py`** → merges batches; emits totals, domain×severity, per-page counts.

## 11. Error handling & resumability

- Every stage validates its inputs and writes its output before the next begins.
- Shallow docs checkout → auto-unshallow before drift detection (with a note).
- Non-existent referenced repos (e.g. docs linking a repo that isn't in the org) are
  dropped from the map with a warning, not treated as drift.
- A re-run that finds an incomplete `runs/<ts>/` offers to resume or start fresh.
- Every network/git mutation (branch, commit, push, PR) is behind an explicit gate.

## 12. Testing approach

- **Scripts:** unit tests with fixture git repos and recorded GitHub API responses
  (deterministic; no live network in tests).
- **Command:** a dry-run/`--no-write` mode that executes stages 1–8 and stops before
  any git mutation, for end-to-end rehearsal on a real `midnight-docs` checkout.
- **Reuse contracts:** a preflight self-test that confirms the sibling agents/commands
  resolve before a real run.

## 13. Open questions / future

- Whether to later add a non-interactive `--ci` mode (report-only, exit non-zero on
  drift) for scheduled runs — out of scope for v1.
- Whether the docs→repo map should eventually be publishable as a shared artifact —
  deferred; v1 keeps it per-user in `${CLAUDE_PLUGIN_DATA}`.
