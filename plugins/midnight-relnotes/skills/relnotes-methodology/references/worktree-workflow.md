# Worktree → commit → PR → housekeeping

1. **Preflight.** `DOCS_REPO="$(pwd)"` captured before any `cd`; `git fetch`
   and ensure the base branch is current.
2. **Worktree.** `git -C "$DOCS_REPO" worktree add "${CLAUDE_PLUGIN_DATA}/worktrees/<item>-<version>" -b relnote/<item>-<version>`.
   Combined notes use `relnote/<item>-<from>..<to>`.
3. **Write.** The `.mdx` under `docs/relnotes/<dir>/` and the `DynamicList`
   edit via `python3 -m scripts.register_release <dynamiclist-path> '<rel-json>'`.
4. **Validate + review.** `python3 -m scripts.validate_relnote '<args-json>'`,
   then the `relnote-reviewer` agent.
5. **Commit.** **One commit per note.** Message:
   `docs(relnotes): add <Item> v<version> release notes`.
6. **Offer push + PR.** On approval: push the branch and
   `gh pr create --repo midnightntwrk/midnight-docs --base <default> --title "..." --body "..."`.
7. **Housekeeping.** Once pushed, ask whether to remove the local worktree
   (`git -C "$DOCS_REPO" worktree remove <path>`). The branch can be
   re-fetched later if needed.
