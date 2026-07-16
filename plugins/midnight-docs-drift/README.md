# midnight-docs-drift

A Claude Code plugin. Run `/update-drifted-docs [path]` from inside a `midnight-docs`
checkout to detect pages that have drifted behind the repos they document, then interactively
extract → classify → severity-rank → verify → fix → PR the stale claims.

**Requires:** the `midnight-fact-check` and `midnight-verify` plugins installed, and `gh`
authenticated with org read access. State is kept under `${CLAUDE_PLUGIN_DATA}`.

Deterministic stages are Python scripts in `scripts/` (unit-tested in `tests/`); claim
extraction/classification/verification are delegated to the sibling plugins.