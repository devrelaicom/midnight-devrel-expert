# Data contract

Two JSON files flow between the script and the model.

## report-data.json (written by `pr_report.py fetch` — facts only)

- `meta`: `{ repo, since, generatedAt (ISO), totals: {total, open, merged, closed, human, bot} }`
- `checkFailureRates`: `[{ name, failed, total, rate }]` across the **open** PRs. Facts only.
  A high `rate` means a check fails on most open PRs; whether that means "noise" is **your**
  judgment, not the script's.
- `prs[]` (sorted by number desc): `{ number, title, url, state, isDraft, baseRefName, author,
  authorType (bot|human), createdAt, updatedAt, closedAt, mergedAt, reviewDecision, additions,
  deletions, changedFiles, labels[], failingChecks[{name,conclusion}], ciStatusRaw, humanComments,
  reviews[{who,state,at}], ageDays, idleDays, blockedOn, priority, action }`.
  `ciStatusRaw`/`priority`/`blockedOn`/`action` are mechanical defaults (priority/action only order
  and caption the queue). They are NOT model judgment.

## narrative.json (written by YOU, the model — judgment)

- `executive_summary`: string or list of strings (the lede).
- `themes`: `[{ name, count, blurb, prs: [int] }]` — recurring threads in the window.
- `observations`: `[{ tag, kind, title, body_html, meta_prs: [int] }]`; `kind` ∈
  `pattern | caution | win | note`. `body_html` may contain inline `<b>`, `<a>`, `<em>`, `<span class="mono">`.
- `watch_items`: `[{ severity, title, desc_html }]`; `severity` ∈ `crit | warn | info`.
- `noise_checks`: `[str]` — check names you judge to be systemic noise (demoted out of "real"
  CI-blocked; shown with a marker). Derived from `checkFailureRates` + what each check does.
- `real_ci_blocked`: `[int]` — PR numbers with a genuinely failing (non-noise) check.

Keep `body_html`/`desc_html` self-contained (no scripts, no external URLs except real PR links).
The renderer HTML-escapes all fact-derived text (titles, authors); your `body_html`/`desc_html`
are passed through as trusted model HTML, so keep them well-formed.
