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
| `version_source` | `npm:<pkg>` \| `gh-release` \| `crates:<crate>` (resolved via cargo/crates.io, else the crate's `Cargo.toml` — **untracked only if neither resolves**) \| `ignored` (deprecated, not tracked). Unrecognised values are treated as untracked, never silently resolved as GitHub releases. |
| `tag_prefix` | stripped from GitHub tags (indexer `v`, `ledger-`, `compactc-v`, `compact-v`, `node-`); also filters a monorepo's tags to this stream |
| `filename_scheme` | `dash` (`midnight-js-4-1-1`) \| `dotted` (`toolchain-0.31.0`) |
| `dynamiclist` | `src/components/DynamicList<Item>.js` |
| `source_path` / `source_ref` | for `crates:*` only: the crate's path + branch in `repo` (e.g. `proof-server` @ `ledger-8`) — used by the Cargo.toml fallback, which also follows `version.workspace = true` into the workspace root |
| `status_vocab` | `["LATEST","SUPPORTED","DEPRECATED"]` |

The seed that maps dirs → sources lives in **`scripts/seed.json`** (data, not code),
keyed by dir basename; `file_prefix` defaults to the basename. Build/refresh the
manifest with `python3 -m scripts.manifest refresh --docs-repo "$DOCS_REPO" --out ${CLAUDE_PLUGIN_DATA}/items.json`.
Any dir printed as `UNMAPPED` must be added to `scripts/seed.json`
before it can be checked or generated — surface these to the user; never skip them silently.

**Crates (`crates:<crate>`)** are resolved like any tracked source: cargo /
crates.io first, then the crate's `Cargo.toml` at `source_path`@`source_ref`
(following `version.workspace = true` into the workspace root). A crate whose only
resolvable version is a prerelease shows no stable and nothing to be "behind" —
truthful, not stale. A crate becomes **untracked** only when neither cargo nor the
Cargo.toml yields a version (the resolver never errors and never fabricates one).

**Untracked/ignored items** appear in the manifest and dashboard but have no
meaningful `behind` — they are labelled `untracked` / `ignored` and never flagged
stale.

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
