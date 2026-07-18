# Midnight Tutorial Checker — Design Spec

**Date:** 2026-07-06
**Status:** Approved (pending spec review)

## Purpose

A Claude Code plugin that evaluates the *experience* of following a Midnight
Network tutorial. Invoked as `/check-tutorial <source> [flags]`, it works
through a tutorial while role-playing a configurable **user persona**, then
produces a detailed HTML report and a formatted chat summary describing where —
and for *which kinds of user* — the tutorial breaks down.

The core value: separate "does the tutorial technically work" from "could *this
type of user* actually get through it," and surface assumed knowledge, blockers,
errors, and show-stoppers accordingly.

## Decisions (locked)

| Decision | Choice |
|---|---|
| Execution model | **Hybrid** — reason through every step as the persona, but really execute the verifiable/risky parts. |
| Persona axes | `experience`, `patience`, `domain-knowledge` (blockchain/crypto/ZK), `tooling` (TS/JS, CLI, env-setup), `comprehension` (English fluency / reading level). *Reading-behavior axis excluded.* |
| Midnight coupling | **Deep integration** — delegate ground-truth checks to the existing Midnight toolchain (compact CLI, devnet skill, `midnight-verify` agents). |
| Personas per run | **Single by default**, opt-in parallel sweep via `--compare` / `--personas a,b,c`. |
| Packaging | **Plugin**: thin command + skill engine + `persona-runner` agent + templates. |
| Persona mechanism | **Structured knowledge-gate** — per step, extract what it demands, gate against the persona profile. |
| Safety posture | **Inherit the harness operating mode** — no bespoke confirmation layer or `--yes` flag; the ambient permission mode governs prompts. |
| Report output | Self-contained HTML file saved to the project + formatted chat summary. Not auto-opened; print clickable path. |

## Architecture

### Pipeline

`/check-tutorial <source> [flags]` runs five stages:

1. **Ingest** — resolve the tutorial (URL / filepath / pasted content), segment
   into an ordered step list.
2. **Resolve persona(s)** — turn flags/preset into concrete axis-value
   profiles (one, or several for `--compare`).
3. **Walk** — per step, run two separate channels (persona knowledge-gate +
   ground-truth execution), logging structured findings.
4. **Synthesize** — roll per-step findings into: assumed-knowledge inventory,
   blockers/show-stoppers, persona-impact narrative, and (for `--compare`) a
   cross-persona blocker matrix.
5. **Report** — write the HTML report to disk and print the chat summary.

### Persona engine

**Axes** — each a named level (e.g. `none | some | strong`, or
`low | medium | high`):

- `experience` — general software-dev experience.
- `patience` — tolerance for friction before giving up / how much they
  troubleshoot.
- `domain-knowledge` — blockchain / crypto / zero-knowledge familiarity.
- `tooling` — TypeScript/JS proficiency, CLI & terminal comfort, environment
  setup (Node, Docker, npm).
- `comprehension` — English fluency / reading level.

**Specification precedence** (later overrides earlier):

1. **Preset** — `--student`, `--hobbyist`, `--dev-new-to-web3`, `--expert`,
   `--non-native-speaker`. Each preset is a bundle of axis values defined in its
   own `personas/*.md`.
2. **Individual flags** — `--experience beginner --patience low` override the
   preset's values for those axes.
3. **Freeform** — `--persona "bootcamp grad, first blockchain project, shaky on
   the terminal"` inferred into axis values.

**Enactment — structured knowledge-gate.** For each step:

1. Extract the concrete demands the step places on the reader (concepts they must
   already know, skills they must have, environment state they must have reached).
2. Tag each demand with the axis it draws on.
3. Gate each demand against the persona's profile. Any demand outside the
   profile becomes an `assumed-knowledge` or `blocker` finding with a severity.

Execution still happens regardless (ground-truth channel), but "did it
technically work" is recorded separately from "would *this persona* get through
it."

### Ingestion

- **URL** → fetched via Rover (cached, clean Markdown, prompt-injection guarded;
  page text treated strictly as *data*, never instructions).
- **Filepath** → read directly (`.md`, `.mdx`, `.html`, plain text).
- **Pasted content** → taken inline.
- **Multi-page** → follow "Next"/pagination links up to a shallow depth
  (`--follow-links N`, default shallow), or accept several sources at once.

Output: an ordered step list (prose, code blocks, commands, expected outputs)
that becomes the spine the persona walks.

### Execution & verification

Two channels per step, kept **separate** in the log:

- **Persona channel** — the knowledge-gate (judgement, not execution).
- **Ground-truth channel** — actually run the verifiable bits *as written*:
  - `compact compile` via the compact CLI;
  - contract / SDK / devnet steps dispatched to the relevant `midnight-verify`
    agents;
  - devnet state checked via the devnet-health skill (reuse a running devnet;
    do not blindly restart it).

Semantics: execution verifies the tutorial's **own happy path works**; the
persona layer judges whether *this user* could follow it. A broken command is a
blocker for **everyone**; an unexplained concept is a blocker only for personas
who lack it.

**Isolation** — each run (and each persona in a `--compare` sweep) gets its own
scratch workspace; the skill never mutates the user's project. The devnet is the
one shared resource, so devnet-touching steps are serialized across a parallel
sweep.

**Safety** — the skill runs commands normally and relies on the ambient Claude
Code permission mode for confirmation. Heavy/irreversible steps (dependency
installs, Docker/devnet start, on-chain deploys) surface through the harness's
own permission prompts. No custom confirmation logic.

### Orchestration

The skill dispatches **one `persona-runner` subagent per persona**. A single run
is `N=1`; `--compare` fans out `N` runners in parallel. Each runner walks its
persona end-to-end and returns a structured finding log. The skill then
synthesizes across logs and renders both outputs. This keeps each walkthrough's
context clean and makes the sweep trivially parallel.

## Reporting

### Finding schema

Each finding produced by a `persona-runner`:

- `step` — step identifier / index.
- `type` — `smooth | assumed-knowledge | blocker | error`.
- `axis` — which persona gap this draws on (or `none` for universal issues).
- `severity` — `info | minor | major | show-stopper`.
- `knowledge-needed-to-progress` — what a user would have to know/do to get past
  it.
- `ground-truth-result` — did the real command pass/fail (or `n/a`).
- `suggested-fix` — recommended change for the tutorial author.

### HTML report

Self-contained, theme-aware, saved to
`./tutorial-reports/<slug>-<persona>-<timestamp>.html`. Sections:

- **Header + persona card** — axes visualized
  (experience/patience/domain/tooling/comprehension).
- **Verdict** — could this persona finish? where do they fall off? counts by
  severity.
- **Persona impact** — how acting as this user changed the walkthrough.
- **Assumed-knowledge inventory** — every concept the tutorial takes for granted,
  flagged where undefined/unlinked (drawing on a Midnight concept library:
  witness, DUST, disclose, proof server, etc.).
- **Step timeline** — each step's status + what it demanded + real execution
  result.
- **Blockers & errors** — detailed; each with severity, show-stopper flag,
  knowledge-needed, and fix.
- **Blocker matrix** (`--compare` only) — personas × steps heatmap.
- **Recommendations** — prioritized fixes for the tutorial author.

### Chat summary

Concise markdown: verdict, top show-stoppers, headline assumed-knowledge gaps,
and the clickable path to the HTML file.

## File layout

```
midnight-tutorial-checker/
  .claude-plugin/plugin.json
  commands/check-tutorial.md          # thin: parse <source> + flags, resolve persona(s), invoke skill
  skills/check-tutorial/
    SKILL.md                          # engine: pipeline + knowledge-gate + orchestration
    personas/                         # student.md, hobbyist.md, dev-new-to-web3.md,
      _axes.md                        #   expert.md, non-native-speaker.md, + axis defs
    references/
      knowledge-gate.md               # extract step demands, gate against profile
      midnight-concepts.md            # concept library for assumed-knowledge detection
      execution.md                    # dispatch to compact CLI / midnight-verify / devnet
      report-schema.md                # finding schema + severities
    templates/report.html             # self-contained HTML template
  agents/persona-runner.md            # walks ONE persona end-to-end; fan out N for --compare
  README.md
```

## Out of scope (YAGNI)

- A reading-behavior persona axis (skims vs. reads carefully).
- A general-purpose (non-Midnight) tutorial checker.
- A bespoke confirmation/`--yes` system (defer to harness permission mode).
- Auto-opening the HTML report.
- Full end-to-end execution of every command in strict order (hybrid model
  executes verifiable parts, not a rigid whole-tutorial run).

## Open questions for implementation planning

- Exact preset → axis-value mappings for the five starter personas.
- Concrete contents of the Midnight concept library (`midnight-concepts.md`).
- HTML template styling direction (self-contained, theme-aware).
- Devnet serialization mechanism for parallel sweeps.
