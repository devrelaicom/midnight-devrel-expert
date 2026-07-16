# midnight-relnotes plugin — design

**Date:** 2026-07-16
**Status:** Approved (design); pending implementation plan
**Author:** Aaron Bassett (with Claude Code)

## Purpose

Automate the DevRel task of keeping `docs/relnotes/` in the `midnightntwrk/midnight-docs`
repository current. Two jobs sit at the core: detect when a published component has moved
ahead of its newest release note (staleness), and generate a new, on-voice release note for
one or more items, opened as a PR. Four supporting capabilities round out the first version:
an exhaustive status dashboard, a structural validator/linter, a prerelease radar, and an
automatic draft reviewer.

The plugin is a sibling to `midnight-docs-drift` in the same marketplace. `docs-drift`
deliberately **excludes** `docs/relnotes/`; this plugin **owns** it. The two are complements.

## Scope boundary

- Operates from **inside a `midnight-docs` checkout**. The command captures
  `DOCS_REPO="$(pwd)"` at preflight (before any `cd`), exactly as `docs-drift` does, so
  worktrees branch off the real repository.
- **All state and generated artifacts live under `${CLAUDE_PLUGIN_DATA}`** — the committed
  manifest, run directories, caches, and dashboard reports. Nothing is written into the docs
  project tree except the release note `.mdx` and its `DynamicList` component edit, and only
  on a worktree branch named `relnote/*`.

## Key findings from research

These shaped the design and must be preserved in implementation.

1. **A release note is a two-file change, not one.** Every example PR (#1006, #1018, #1000)
   edits the `.mdx` detail page **and** the matching `src/components/DynamicList<Item>.js`:
   it prepends a new release object (`version`, `status: 'LATEST'`, `date`, `summary`,
   `details[]`, `artifacts[]`, `link`) and **demotes the previous `LATEST` to `SUPPORTED`**.
   Omitting the JS edit means the note never appears in the docs UI. This registration step
   is scripted deterministically.

2. **"Latest published" means latest _stable_.** `midnight-js` newest GitHub releases are all
   `v5.0.0-beta.*`/`-alpha.*`/`-rc.*`, but npm `dist-tags.latest` is `4.1.1`, which matches
   the newest relnote. Staleness resolution must read npm dist-tags and non-prerelease GitHub
   releases per item, never the raw newest tag. Pure scripting, no inference.

3. **Naming and version-source vary per item.** `midnight-js-4-1-1.mdx` (npm, `v` tag) vs
   `ledger-8-1-0.mdx` (Rust, `ledger-` tag) vs `toolchain-0.31.0.mdx` (`compactc-v` tag, dots
   kept). A per-item manifest is the only reliable mapping from a relnotes directory to its
   repo, version source, filename scheme, and DynamicList component.

4. **The current format is the rich one** used by all three example PRs: `High-level summary`
   → `Audience` → `Summary of updates` → `New features` → `Breaking changes` →
   `Bug fixes and quality improvements` → `Known issues` → `Links and references`. An older,
   lighter format exists in some files and is not the target.

5. **Plugin-provided agents ignore `model`/`skills`/`hooks` frontmatter.** Agents must
   `Skill`-invoke or Read references from their body rather than relying on preload (the
   pattern `midnight-verify`'s `source-investigator` already uses).

## The manifest

`${CLAUDE_PLUGIN_DATA}/items.json`, cached with a TTL and refreshable. One entry per
relnotes directory:

| Field | Example |
|---|---|
| `dir` | `docs/relnotes/midnight-js` |
| `repo` | `midnightntwrk/midnight-js` |
| `version_source` | `npm:@midnight-ntwrk/midnight-js` \| `gh-release` \| `crates` |
| `tag_prefix` | `v` \| `ledger-` \| `compactc-v` |
| `filename_scheme` | `dash` (`midnight-js-4-1-1`) \| `dotted` (`toolchain-0.31.0`) |
| `dynamiclist` | `src/components/DynamicListMidnightJS.js` |
| `status_vocab` | `LATEST` / `SUPPORTED` / `DEPRECATED` |

A `refresh` mode rebuilds it (reusing `repo_scan.py` concepts from `docs-drift`) and **flags
any relnotes directory not yet mapped**, so newly-added items surface rather than being
silently skipped.

## Commands

### `/midnight-relnotes:check [items…]`
Staleness report. Resolves latest stable published version per item via the version scripts,
compares to the newest existing relnote, reports versions-behind, and **flags any item more
than one version behind**. Dispatches `release-scout` agents in parallel batches so gh/npm
calls and JSON parsing never enter the main context. Also surfaces prerelease activity
(prerelease radar) as a distinct section.

### `/midnight-relnotes:generate <spec>`
Accepts natural specs: `midnight-wallet-api`, `for any stale releases`,
`for stale @midnight-ntwrk/* packages`. Resolves the target set (reusing check's logic), then
per item:

1. Create a worktree on branch `relnote/<item>-<version>` (or `relnote/<item>-<from>..<to>`
   for a combined note).
2. Investigate the source repo (via `relnote-author`, which may spawn nested `source-digger`
   subagents for change harvesting).
3. Draft the note in-voice using `relnotes-writing`, following `relnotes-authoring` structure.
4. Write the `.mdx` and run `register_release.py` to update the `DynamicList` component.
5. Run `validate_relnote.py`; then `relnote-reviewer` critiques the draft.
6. **One commit per note.**

After generation: offer to push the branch and open a PR. Once pushed, ask whether to remove
the local worktree as housekeeping (the branch can be re-fetched if needed).

**Multi-version-behind policy:** on discovering an item is >1 version behind, `generate` calls
`AskUserQuestion` — individual notes per published version, or one combined note across the
range. On no human response within a reasonable window, **default to individual per-version
notes** and continue (splitting a combined note later is harder than combining).

### `/midnight-relnotes:dashboard`
Exhaustive status table over all items: last-noted version, latest stable, versions-behind,
staleness age, prerelease activity. Asks HTML or Markdown; on no response within a reasonable
window, produces **both**. Writes to `${CLAUDE_PLUGIN_DATA}`. If the `agentbin` CLI is
present, offers to upload and returns the URL; otherwise prints the full path.

### `/midnight-relnotes:doctor`
Thin wrapper over the `relnotes-doctor` skill (mirrors `gha`).

## Skills

- **`relnotes-doctor`** — quick sense check only: authenticated `gh`, `git`, `node >=22`,
  `jq`, `python3`, `npm`, and "are we in a docs checkout". Reports gaps + install hints,
  never installs. Points to `midnight-expert`'s doctor for a full env check.
- **`relnotes-methodology`** — orchestration rubrics: staleness + version-source resolution,
  the manifest schema, the >1-version policy, and the worktree/commit/PR/housekeeping
  workflow. `references/`: `version-sources.md`, `source-investigation.md` (how to find the
  repo, use git/`gh` for commits/PRs/issues, and read diffs into a note), `worktree-workflow.md`.
- **`relnotes-authoring`** — structure, naming, and `DynamicList` registration. `references/`:
  `template-full.mdx`, `section-catalog.md` (annotated real examples of each section),
  `filename-convention.md`, `dynamiclist-registration.md`.
- **`relnotes-writing`** — the voice, generated by `/lexisim:design` during implementation.
  Mimics the current release notes' tone and structure and imports the anti-AI-trope
  forbidden-patterns list from the `tools-docs` profile. It matches the existing relnotes'
  spelling and em-dash mechanics rather than forcing Commonwealth/closed em-dashes, since the
  job is to blend into midnight-docs.

## Agents

- **`release-scout`** (parallel, read-only) — takes a batch of items, runs the version
  scripts, returns condensed staleness verdicts. Pure script-runner, tiny token footprint.
- **`relnote-author`** — owns one item end-to-end: investigates the source repo, drafts
  in-voice, writes the `.mdx`, runs registration, commits. Holds the `Agent` tool so it can
  spawn nested `source-digger` subagents.
- **`source-digger`** (nested, read-only) — given a repo + tag range, returns a condensed
  change inventory (commit subjects, merged-PR titles, release body, changelog slice) via
  wrapper scripts. Keeps bulk diffs out of the author's context.
- **`relnote-reviewer`** — critiques a draft against voice + structure + registration
  consistency before the PR is offered (a quality gate, like `gha-auditor`).

Each agent body explicitly `Skill`-invokes what it needs, since plugin agents ignore the
`skills`/`model` frontmatter.

## Scripts

Deterministic gh/npm wrappers that parse and condense; Python for anything touching
semver/JSON (matches `docs-drift`), bash only for thin shells.

| Script | Job |
|---|---|
| `doctor.sh` | Quick tool/runtime sense check |
| `latest_release.py` | Latest stable + latest prerelease per item (npm dist-tags / non-prerelease GH release / crates) |
| `latest_relnote.py` | Highest existing relnote version + filename for an item |
| `staleness.py` | Join latest-release vs latest-relnote across items → versions-behind + gap list |
| `change_harvest.sh` | Tag-range commit subjects, merged-PR titles, release body, changelog slice |
| `register_release.py` | Prepend a release object into `DynamicList<Item>.js`, demote prior LATEST → SUPPORTED |
| `validate_relnote.py` | Lint: filename, frontmatter, required sections, registration consistency, links (CI-usable) |
| `manifest.py` | Build/refresh `items.json`, flag unmapped relnote dirs |
| `dashboard.py` | Render status table to Markdown and/or HTML into `${CLAUDE_PLUGIN_DATA}` |

## Design calls made (not open questions)

- **Node floor `>=22`** in doctor, from the relnotes' own "Node.js requirement".
- **Draft reviewer runs automatically** before the PR offer, not as a separate command.
- **Python + thin bash**, matching the `docs-drift` sibling.
- **Committed manifest** over per-run auto-discovery.

## Non-goals (first version)

- Cross-item breaking-change digest / migration guide (natural later extension of dashboard).
- Editing or reformatting existing/legacy-format notes.
- Publishing anything outside a PR (no direct pushes to a docs default branch).
