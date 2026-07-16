---
name: midnight-relnotes:generate
description: Generate release note(s) for the requested items on a relnote/* worktree, in the current relnotes voice and structure, one commit per note. Handles natural specs like "midnight-wallet-api", "for any stale releases", "for stale @midnight-ntwrk/* packages". Offers to push + open a PR, then housekeeping. Run from inside a midnight-docs checkout.
allowed-tools: Skill, Agent, AskUserQuestion, Bash, Read, Write, Edit
argument-hint: "<item | 'for any stale releases' | 'for stale @midnight-ntwrk/* packages'>"
---

Generate release note(s) for the items in `$ARGUMENTS`.

## Step 1: Preflight

Load `relnotes-doctor`; stop on gh-auth / not-a-docs-checkout. Capture
`DOCS_REPO="$(pwd)"`. Load `relnotes-methodology`. Refresh the manifest.

## Step 2: Resolve the target set

Interpret `$ARGUMENTS`:
- a bare item name → that item.
- "for any stale releases" → run the check logic (dispatch `release-scout`)
  and take every stale item.
- "for stale @midnight-ntwrk/* packages" or a glob → the stale items whose
  `version_source`/`repo` matches the pattern.

Confirm the resolved list with the user before writing anything.

## Step 3: Per-item version decision

For each target, if it is **more than one version behind**, apply the
methodology policy: `AskUserQuestion` — individual notes per published version,
or one combined note. **If no response within a reasonable window, default to
individual per-version notes** and continue.

## Step 4: Author

For each note to produce (per-version or combined), create the worktree
(`references/worktree-workflow.md`) and dispatch a `relnote-author` agent with
the item entry, the target version(s), and the previous relnote version. The
author writes the `.mdx`, registers the DynamicList entry, validates, and makes
**one commit per note**.

## Step 5: Review

Dispatch `relnote-reviewer` on each draft. Relay its PASS / fix list. Apply
fixes (re-dispatch the author or edit directly) until it passes.

## Step 6: Offer push + PR

Show the commits. Offer to push the branch and open a PR against
`midnightntwrk/midnight-docs`. On approval, push and `gh pr create`.

## Step 7: Housekeeping

Once pushed, ask whether to remove the local worktree
(`git -C "$DOCS_REPO" worktree remove <path>`). Note the branch can be
re-fetched if needed.
