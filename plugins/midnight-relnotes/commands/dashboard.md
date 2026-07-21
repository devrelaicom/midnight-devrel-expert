---
name: midnight-relnotes:dashboard
description: Render an exhaustive release-note status dashboard over all items (last-noted, latest stable, versions behind, staleness, prerelease activity) as Markdown and/or HTML, saved under the plugin data dir. Two HTML styles (basic table / full custom board); shares via Claude Web artifacts, agentbin, or mdtohtml.
allowed-tools: Skill, Agent, AskUserQuestion, Bash, Read, Write, Artifact
---

Produce a full status dashboard over **all** items.

## Step 1: Preflight + data

Load `relnotes-doctor` (stop on gh-auth / not-a-docs-checkout). Capture
`DOCS_REPO="$(pwd)"`. Load `relnotes-methodology` (data rules) and
`relnotes-dashboard` (styles, disk, and sharing — the authoritative source for
Steps 3–5). Refresh the manifest. Dispatch `release-scout` agents over all items
and collect verdict rows, including `tracked:false` + `tracked_label` for
untracked/ignored items.

## Step 2: Probe tools

Run `${CLAUDE_PLUGIN_ROOT}/scripts/tool_probe.sh` **once** to learn which of
`agentbin` / `mdtohtml` / `cargo` are available. Do not probe them individually.

## Step 3: Ask (format, style, sharing)

Per `relnotes-dashboard`, ask with `AskUserQuestion` — you may consolidate into a
single call:
1. **Format** (always): HTML, Markdown, or both. **If no response arrives in a
   reasonable window, default to both.**
2. **Style** (only if HTML): Basic or Full.
3. **HTML sharing** (only if HTML) — default Claude Web: `agentbin` present →
   Claude Web / agentbin / neither; else Claude Web / neither.
4. **Markdown sharing** (only if Markdown): both tools → Claude Web / agentbin /
   neither; only agentbin → agentbin / neither; only mdtohtml → Claude Web /
   neither; neither → no share.

## Step 4: Render to disk (always, timestamped)

Build the rows JSON and run, from `${CLAUDE_PLUGIN_ROOT}`:
`python3 -m scripts.dashboard --rows '<rows-json>' --out-dir ${CLAUDE_PLUGIN_DATA}/dashboards --format <md|html|both> --style <basic|full>`.
This always writes `dashboard-YYYYMMDD-HHMMSS.{md,html,artifact.html}` under
`${CLAUDE_PLUGIN_DATA}/dashboards`. Never write into the docs project tree.

## Step 5: Share + report

Execute the chosen share targets per `relnotes-dashboard`:
- HTML → Claude Web: publish the `*.artifact.html` fragment (light neo-brutalist
  theme kept per the skill's precedence note; favicon `🌒`). HTML → agentbin: upload the `*.html`.
- Markdown → Claude Web: `mdtohtml` the `.md` first, publish that HTML. Markdown →
  agentbin: upload the **raw `.md`** (agentbin renders Markdown; no pre-convert).

Return any share URLs, and **always** print the full on-disk path(s) — they are
the deliverable whether or not anything was shared.
