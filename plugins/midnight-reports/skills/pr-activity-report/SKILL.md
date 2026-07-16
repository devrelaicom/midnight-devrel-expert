---
name: pr-activity-report
description: This skill should be used to generate a pull-request activity report for a GitHub repository over a timeframe, and to share it. Triggers on "/midnight-reports:pr", "PR report", "pull request report", "PR activity dashboard", "report on open PRs", or a request to summarize/triage a repo's recent pull requests. Fetches PRs via gh, computes CI/triage/age facts, has the model infer CI noise and write narrative, renders a self-contained HTML report, publishes it as an Artifact, and offers a paste-ready Slack message.
---

# PR Activity Report

Generate a self-contained HTML report of a repo's pull-request activity, publish it, and
optionally produce a Slack message. Run scripts from the plugin root
(`${CLAUDE_PLUGIN_ROOT}`). Write run artifacts under
`${CLAUDE_PLUGIN_DATA}/<owner>/<name>/runs/<iso-ts>/`. Never write to the user's cwd.

## The one rule that shapes everything

**The script reports facts. You make the judgments.** The failing-CI numbers, ages, and
review states are facts from `pr_report.py`. Which failing checks are *noise*, what actually
unblocks a PR, and what the two weeks *mean* are yours. Do not push judgment into the script;
do not treat a mechanical `priority` as if it were an assessment.

## Workflow

1. **Preflight.** Confirm `gh auth status` is OK. Resolve args:
   - `<repo>`: pass through `scripts.lib.parse_repo` (accepts `owner/name` or a github URL).
   - `[timeframe]`: default `2w`; resolve with `scripts.lib.resolve_since` (`Nd`/`Nw`/`Nmo` or ISO date).
   - Create the run dir: `RUN="${CLAUDE_PLUGIN_DATA}/<owner>/<name>/runs/<iso-ts>"`.

2. **Fetch (facts).**
   `(cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m scripts.pr_report fetch --repo <owner/name> --since <iso> --out "$RUN/report-data.json")`

3. **Infer CI noise (judgment).** Read `report-data.json` → `checkFailureRates`. Reason about
   each check by name and role. A check that fails on most open PRs regardless of the change
   (e.g. a repo-wide deploy/preview integration) is systemic noise. Record the noise check
   names and the PR numbers that have a genuinely failing (non-noise) check.

4. **Read threads + write narrative (judgment).** For the **open** PRs and the **notable**
   merged/closed ones (approved-but-unmerged, changes-requested, superseded, headline merges),
   read the PR body and review thread with `gh pr view <n> --json ...`. Watch for "ball-in-court"
   nuance (a contributor who already replied to a change request is waiting on the maintainer).
   Write `$RUN/narrative.json` per `references/data-contract.md`: `executive_summary`, `themes`,
   `observations`, `watch_items`, `noise_checks`, `real_ci_blocked`. Keep prose specific and honest.

5. **Build.**
   `(cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m scripts.pr_report build --data "$RUN/report-data.json" --narrative "$RUN/narrative.json" --template "${CLAUDE_PLUGIN_ROOT}/skills/pr-activity-report/references/template.html" --out "$RUN/report.html")`

6. **Publish.** Publish `$RUN/report.html` via the Artifact tool: favicon 🌙, title
   `<owner>/<name> · PR Review Watch`, a one-sentence description.

7. **Report + offer.** Respond with the few most important findings (honestly framed) and the
   Artifact URL + the saved `$RUN/report.html` path. Note here, once, that to share it the user
   must set the artifact to "anyone with the link" via the claude.ai share menu (you cannot do
   this yourself). Then ask whether they want a short, paste-ready Slack message for the team.
   Stop and wait.

8. **Slack message (only if yes).** Load `references/slack-voice.md` and write the message per
   the rubric below, ending with the report link as the **last line**.

   **OUTPUT ISOLATION (hard rule):** your entire response is the message text and nothing else.
   No preamble, no postamble, no follow-up question, no code fence, no "here's your message", no
   sharing reminder (already given in step 7). The user will `/copy` the whole response straight
   into Slack; any stray token gets pasted in front of colleagues.

## Slack content rubric

- Lead with what matters to DevRel: the findings that change what the team does next.
- Flag anything surprising the team likely does not know.
- Flag anything urgent, framed as team-owned and zero-blame. Never attribute a problem to a person.
- Always include one genuine good-news item.
- Give individual cudos only when earned and sparingly; never call out a person negatively.
- Voice: `references/slack-voice.md`. Zero em-dashes, inclusive language, no AI tropes, bullets
  for multi-point content, Slack emoji shortcodes only where they carry tone.

## Notes

- The report is self-contained (inline CSS/JS, no external requests). Do not add external links
  beyond real PR URLs.
- If `gh` returns zero PRs, still build the report (it will read as an empty window) and say so.
