# midnight-reports

Generate PR-activity reports for any GitHub repository.

## `/midnight-reports:pr <repo> [timeframe]`

Fetches every pull request with activity in the timeframe (default 2 weeks), then produces a
self-contained, themed HTML report: KPI tiles, open-PR triage, an action queue ranked by what
unblocks each PR, a filterable table of all active PRs, plus a narrative layer (executive
summary, themes, observations, watch-items). The report is published as an Artifact and saved
under the plugin data dir. After publishing, the command offers a paste-ready Slack summary.

- `<repo>`: `owner/name` or a `github.com/owner/name` URL.
- `[timeframe]`: `Nd` / `Nw` / `Nmo` or `YYYY-MM-DD` (default `2w`).

### Design

The work splits along a facts/judgment boundary. `scripts/pr_report.py` (pure `lib`/`enrich`/
`render` modules + a thin `gh` shell) reports facts and renders HTML from
`skills/pr-activity-report/references/template.html`. The model infers which failing CI checks
are systemic noise, reads PR threads to write the narrative, publishes, and writes the Slack
message in the vendored `slack-voice.md` voice.

### Requirements

- `gh` CLI, authenticated (`gh auth status`).
- Python 3 (stdlib only).

### Tests

`cd plugins/midnight-reports && python3 -m pytest scripts/tests -q`
