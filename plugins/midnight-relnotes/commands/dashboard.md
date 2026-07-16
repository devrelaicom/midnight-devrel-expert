---
name: midnight-relnotes:dashboard
description: Render an exhaustive release-note status dashboard over all items (last-noted, latest stable, versions behind, staleness, prerelease activity) as Markdown and/or HTML, saved under the plugin data dir. Offers to upload via agentbin if available.
allowed-tools: Skill, Agent, AskUserQuestion, Bash, Read, Write
---

Produce a full status dashboard over **all** items.

## Step 1: Preflight + data

Load `relnotes-doctor` (stop on gh-auth / not-a-docs-checkout). Capture
`DOCS_REPO="$(pwd)"`. Load `relnotes-methodology`. Refresh the manifest.
Dispatch `release-scout` agents over all items and collect verdict rows.

## Step 2: Choose format

Ask the user, via `AskUserQuestion`: HTML, Markdown, or both. **If no response
arrives within a reasonable window, default to both.**

## Step 3: Render

Build the rows JSON `[{item, latest_relnote, latest_stable, behind, stale, prerelease}]`
and run, from `${CLAUDE_PLUGIN_ROOT}`:
`python3 -m scripts.dashboard --rows '<rows-json>' --out-dir ${CLAUDE_PLUGIN_DATA}/dashboards/<YYYY-MM-DD> --format <md|html|both>`.

## Step 4: Deliver

If the `agentbin` CLI is available (`command -v agentbin`), offer to upload the
report(s) and return the URL. Otherwise, print the **full path(s)** to the
generated files. Never write dashboards into the docs project tree.
