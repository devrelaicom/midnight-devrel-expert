---
description: Generate a self-contained HTML pull-request activity report for a GitHub repo over a timeframe, publish it as an Artifact, and optionally produce a paste-ready Slack message. Accepts owner/name or a github.com URL; timeframe defaults to 2 weeks.
argument-hint: "<repo> [timeframe]  e.g. midnightntwrk/midnight-docs 2w"
---

Load the `pr-activity-report` skill and run its workflow.

Arguments:
- `$1` = repository, as `owner/name` or a `github.com/owner/name[/...]` URL (required).
- `$2` = timeframe, one of `Nd` / `Nw` / `Nmo` or `YYYY-MM-DD` (optional; default `2w`).

Normalize `$1` with `scripts.lib.parse_repo` and resolve `$2` with `scripts.lib.resolve_since`
(from `${CLAUDE_PLUGIN_ROOT}`), echo the resolved `owner/name` and `since` date, then follow the
skill's workflow end to end (fetch facts → infer CI noise → read threads and write narrative →
build → publish → report + offer Slack message). Honor the skill's Slack output-isolation rule.

If `$1` is missing, ask for the repository and stop.
