---
name: relnotes-methodology
description: Load this skill when running any midnight-relnotes command (check, generate, dashboard). It carries the staleness rules, version-source resolution, the items.json manifest schema, the more-than-one-version-behind policy, and the worktree/commit/PR/housekeeping workflow. Commands and agents follow it step by step.
---

# relnotes Methodology

The rubric behind every midnight-relnotes command. Load the matching
reference file for detail.

## The manifest (`${CLAUDE_PLUGIN_DATA}/items.json`)

One entry per relnotes directory:

| Field | Meaning |
|---|---|
| `dir` | e.g. `docs/relnotes/midnight-js` |
| `file_prefix` | filename stem, defaults to the dir basename (e.g. `toolchain` in the `compact` dir) |
| `repo` | source repo, `owner/name` |
| `version_source` | `npm:<pkg>` \| `gh-release` \| `crates` |
| `tag_prefix` | stripped from GitHub tags (`v`, `ledger-`, `compactc-v`) |
| `filename_scheme` | `dash` (`midnight-js-4-1-1`) \| `dotted` (`toolchain-0.31.0`) |
| `dynamiclist` | `src/components/DynamicList<Item>.js` |
| `status_vocab` | `["LATEST","SUPPORTED","DEPRECATED"]` |

Build/refresh with `python3 -m scripts.manifest refresh --docs-repo "$DOCS_REPO" --out ${CLAUDE_PLUGIN_DATA}/items.json`.
Any dir printed as `UNMAPPED` must be added to the `SEED` table in `scripts/manifest.py`
before it can be checked or generated — surface these to the user; never skip them silently.

## Staleness

For each item: resolve the latest **stable** published version
(`references/version-sources.md`) and the highest existing relnote, then
`python3 -m scripts.staleness`. Report `behind` and `gap_versions`. Always
flag items **more than one version behind**.

## The more-than-one-version-behind policy

- **check / dashboard**: report it in the output. No prompt.
- **generate**: on discovering an item is >1 behind, call `AskUserQuestion` —
  individual notes per published version, or one combined note across the
  range. If no human response arrives within a reasonable window, **default
  to individual per-version notes** and continue. Splitting a combined note
  later is harder than combining several.

## Generate workflow

Follow `references/worktree-workflow.md`: one worktree per item on
`relnote/<item>-<version>`, investigate via `references/source-investigation.md`,
draft with the `relnotes-writing` and `relnotes-authoring` skills, write the
`.mdx`, run `register_release.py`, validate, review, and make **one commit
per note**. Then offer push + PR, then housekeeping.

## Artifacts

Everything the plugin generates (manifest, run dirs, dashboard reports) lives
under `${CLAUDE_PLUGIN_DATA}`. Never write plugin artifacts into the docs
project tree.
