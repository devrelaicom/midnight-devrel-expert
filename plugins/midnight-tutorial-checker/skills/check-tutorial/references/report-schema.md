# Report schema

This document describes the two JSON shapes used by the tutorial-check report
pipeline: the **finding** object and the **report-data** object. `render-report.mjs`
consumes a report-data object and produces the HTML report; `persona-runner` (Task 8)
produces findings; the SKILL engine (Task 9) assembles the report-data object and
invokes the renderer.

`skills/check-tutorial/scripts/render-report.mjs` is the executable source of truth
for this schema — if this document and the renderer ever disagree, the renderer wins.

## `finding`

One observation made by a persona at one tutorial step.

```
{
  step: number,
  title: string,
  type: "smooth" | "assumed-knowledge" | "blocker" | "error",
  axis: "experience" | "patience" | "domain-knowledge" | "tooling" | "comprehension" | "none",
  severity: "info" | "minor" | "major" | "show-stopper",
  knowledgeNeeded: string,
  groundTruthResult: "pass" | "fail" | "n/a",
  suggestedFix: string,
  detail: string
}
```

| Field | Meaning |
| --- | --- |
| `step` | 1-based index of the tutorial step this finding is about. |
| `title` | Short label for the step, matching the corresponding entry in `report-data.steps`. |
| `type` | What kind of thing happened at this step. |
| `axis` | Which persona axis (if any) this finding is attributed to. |
| `severity` | How bad this finding is for the persona's progress. |
| `knowledgeNeeded` | Concept or fact the persona needed but the tutorial didn't supply (empty string if none). |
| `groundTruthResult` | Whether the underlying command/action actually succeeded when run for real, independent of persona experience. |
| `suggestedFix` | A concrete edit to the tutorial that would address this finding (empty string if none). |
| `detail` | Free-text explanation of what was observed. |

### Enum values

- `type`: `smooth` (no issue), `assumed-knowledge` (tutorial assumes something not taught), `blocker` (persona could not proceed), `error` (a command/action genuinely failed).
- `axis`: `experience`, `patience`, `domain-knowledge`, `tooling`, `comprehension`, or `none` (finding isn't attributable to a specific axis).
- `severity`: `info` < `minor` < `major` < `show-stopper`, in ascending order of impact.
- `groundTruthResult`: `pass` (verified to work), `fail` (verified to not work), `n/a` (not independently executed — e.g. a purely conceptual gap).

### Example

```json
{ "step": 2, "title": "Write the contract", "type": "blocker", "axis": "domain-knowledge", "severity": "show-stopper", "knowledgeNeeded": "what a witness is and why it is private", "groundTruthResult": "n/a", "suggestedFix": "Define 'witness' on first use and link to the privacy concept page.", "detail": "The term 'witness' appears with no definition; a beginner with no blockchain background cannot proceed." }
```

## `report-data`

The full report for one run of the tutorial checker, in either `single` or `compare` mode.

```
{
  tutorial: { title: string, source: string, fetchedAt: string },
  generatedAt: string,
  mode: "single" | "compare",
  steps: [ { index: number, title: string, summary: string } ],
  personas: [
    {
      name: string,
      axes: {
        experience: string,
        patience: string,
        "domain-knowledge": string,
        tooling: string,
        comprehension: string
      },
      verdict: { completed: boolean, fellOffAtStep: number | null, summary: string },
      severityCounts: { info: number, minor: number, major: number, "show-stopper": number },
      findings: [ finding ]
    }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `tutorial.title` | Title of the tutorial being checked. |
| `tutorial.source` | URL or file path the tutorial was fetched/read from. |
| `tutorial.fetchedAt` | ISO 8601 timestamp of when the tutorial content was retrieved. |
| `generatedAt` | ISO 8601 timestamp of when the report itself was generated. |
| `mode` | `single` — one persona walked the tutorial; `compare` — multiple personas walked it and are compared (blocker matrix). |
| `steps` | Ordered list of the tutorial's steps, independent of any persona. |
| `steps[].index` | 1-based step number, matches `finding.step`. |
| `steps[].title` | Short label for the step. |
| `steps[].summary` | One-line description of what the step asks the reader to do. |
| `personas` | One entry per persona that walked the tutorial (length 1 in `single` mode). |
| `personas[].name` | Persona identifier/label, e.g. `"student"`. |
| `personas[].axes` | The five persona axes and their configured level for this run. |
| `personas[].verdict.completed` | Whether this persona finished the tutorial. |
| `personas[].verdict.fellOffAtStep` | Step index where the persona got stuck, or `null` if `completed` is `true`. |
| `personas[].verdict.summary` | One-line human summary of the outcome. |
| `personas[].severityCounts` | Count of findings at each severity level for this persona. |
| `personas[].findings` | Ordered list of `finding` objects for this persona, one (or more) per step walked. |

### Enum values

- `mode`: `single`, `compare`.
- `axes.*` values are free-form strings (e.g. `"beginner"`, `"medium"`, `"none"`, `"some"`, `"fluent"`) defined by the persona presets in Task 4; the schema does not constrain them further.

### Example

```json
{
  "tutorial": { "title": "Midnight Counter Tutorial", "source": "https://example.test/counter", "fetchedAt": "2026-07-06T11:59:00Z" },
  "generatedAt": "2026-07-06T12:00:00Z",
  "mode": "single",
  "steps": [
    { "index": 1, "title": "Install the toolchain", "summary": "Install Compact CLI and Node." },
    { "index": 2, "title": "Write the contract", "summary": "Add a witness and a circuit." },
    { "index": 3, "title": "Compile", "summary": "Run compact compile." }
  ],
  "personas": [
    {
      "name": "student",
      "axes": { "experience": "beginner", "patience": "medium", "domain-knowledge": "none", "tooling": "some", "comprehension": "fluent" },
      "verdict": { "completed": false, "fellOffAtStep": 2, "summary": "Blocked at step 2 by an undefined 'witness' concept." },
      "severityCounts": { "info": 1, "minor": 1, "major": 0, "show-stopper": 1 },
      "findings": [
        { "step": 1, "title": "Install the toolchain", "type": "smooth", "axis": "none", "severity": "info", "knowledgeNeeded": "", "groundTruthResult": "pass", "suggestedFix": "", "detail": "Install commands ran cleanly." },
        { "step": 2, "title": "Write the contract", "type": "blocker", "axis": "domain-knowledge", "severity": "show-stopper", "knowledgeNeeded": "what a witness is and why it is private", "groundTruthResult": "n/a", "suggestedFix": "Define 'witness' on first use and link to the privacy concept page.", "detail": "The term 'witness' appears with no definition; a beginner with no blockchain background cannot proceed." },
        { "step": 3, "title": "Compile", "type": "assumed-knowledge", "axis": "none", "severity": "minor", "knowledgeNeeded": "", "groundTruthResult": "pass", "suggestedFix": "Show the expected output directory.", "detail": "Compiles, but the tutorial does not say where output lands." }
      ]
    }
  ]
}
```

This example is reused verbatim as the test fixture at
`skills/check-tutorial/scripts/fixtures/single.json`.
