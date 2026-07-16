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
to install them and stop). Capture the docs checkout path now, before any `cd`, as
`DOCS_REPO="$(pwd)"` — every later stage that touches the docs repo uses this absolute path.
Resolve eligible files under the scope: `*.mdx`/`*.md`, excluding `_`-prefixed segments and
(by default) `docs/relnotes/`.

**Stage 1 — Repo list.** Look for `${CLAUDE_PLUGIN_DATA}/<org>/repos.json`. If it exists,
report its `generated_at` and whether it is within the TTL (14 days). GATE: ask regenerate or
reuse. On regenerate/absent, run:
`(cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m scripts.repo_scan --org <org> --since <iso-cutoff> --out ${CLAUDE_PLUGIN_DATA}/<org>/repos.json)`

**Stage 2 — Docs→repo map.** Load `${CLAUDE_PLUGIN_DATA}/<docs-repo>/docs-repo-map.json`.
Diff its keys against the scoped eligible files. GATE: if new/removed pages → remap all vs
only new; if none → remap vs reuse. To (re)map: dispatch reader agents over the target pages
to produce `{page:[tech/tool + repo-URL items]}` per the methodology skill, write it to the
run dir, then run:
`(cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m scripts.build_map --page-items <items.json> --repos ${CLAUDE_PLUGIN_DATA}/<org>/repos.json --out ${CLAUDE_PLUGIN_DATA}/<docs-repo>/docs-repo-map.json)`

**Stage 3 — Drift detect.** Run:
`(cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m scripts.drift_detect --docs-repo "$DOCS_REPO" --map ${CLAUDE_PLUGIN_DATA}/<docs-repo>/docs-repo-map.json --out <run>/drift.json)`

**Stage 4 — Drift summary.** Render each drifted page → the repos published more recently
(date + release/push). GATE: ask the user to exclude any files or continue with all; apply
exclusions to the working set.

**Stage 5 — Claims.** For the working set, dispatch `midnight-fact-check`'s `claim-extractor`
agents in parallel batches (each writes a claim batch JSON to `<run>/claims/`), then dispatch
`domain-classifier`. Then run:
`(cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m scripts.severity_pass --claims-glob "<run>/claims/claims-batch-*.json")`
`(cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m scripts.aggregate --claims-glob "<run>/claims/claims-batch-*.json" --out <run>/severity.json)`

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
