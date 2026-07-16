---
name: midnight-relnotes:check
description: Report which Midnight release notes are stale — newest published stable version ahead of the newest relnote — and flag any item more than one version behind. Also surfaces prerelease activity. Run from inside a midnight-docs checkout.
allowed-tools: Skill, Agent, AskUserQuestion, Bash, Read, Write
argument-hint: "[item ...] (default: all items)"
---

Report stale release notes across the requested items (default: all).

## Step 1: Preflight

Load `relnotes-doctor` and run it. If `gh` is unauthenticated or the cwd is not
a midnight-docs checkout, report the gap and stop. Capture `DOCS_REPO="$(pwd)"`.

## Step 2: Load methodology + manifest

Load the `relnotes-methodology` skill. Ensure the manifest exists and is fresh:
`python3 -m scripts.manifest refresh --docs-repo "$DOCS_REPO" --out ${CLAUDE_PLUGIN_DATA}/items.json`
(run from `${CLAUDE_PLUGIN_ROOT}`). Surface any `UNMAPPED` dirs to the user.

## Step 3: Scout in parallel

Split the target items into batches of ~5 and dispatch a `release-scout`
agent per batch, passing the batch's manifest entries and `DOCS_REPO`.

## Step 4: Report

Merge the scouts' verdict rows into one table: item, latest relnote, latest
stable, versions behind, prerelease. Call out, in their own list, every item
**more than one version behind** (these need the individual-vs-combined
decision at generate time). End with the exact `/midnight-relnotes:generate`
invocation the user would run for the stale set.
