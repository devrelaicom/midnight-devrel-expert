# Turning source history into a release note

Goal: a comprehensive, accurate note for a version, grounded in what actually
changed. Never invent changes.

1. **Range.** The note covers `<previous-relnote-version>..<target-version>`.
   Use the source repo's tags with the item's `tag_prefix`.
2. **Harvest (condensed).** Run
   `${CLAUDE_PLUGIN_ROOT}/scripts/change_harvest.sh <repo> <from_tag> <to_tag>`.
   It returns the target release body, merged-PR titles, and commit subjects —
   enough to draft from without pulling full diffs into context.
3. **Go deeper only where needed.** For a change whose intent is unclear, read
   the specific PR (`gh pr view <n> --repo <repo>`) or the specific diff
   (`gh api repos/<repo>/compare/<from>...<to>`). Prefer the `source-digger`
   subagent for this so bulk output stays out of the author's context.
4. **Classify** each change into the note's sections: new features, breaking
   changes (with migration steps), bug fixes and quality improvements, known
   issues. Breaking changes always get a **Migration** line.
5. **Ground every claim.** Every bullet should trace to a PR, commit, or
   release-body line. If you cannot ground it, drop it.
