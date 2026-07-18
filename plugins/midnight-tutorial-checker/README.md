# midnight-tutorial-checker

A Claude Code plugin that walks a Midnight Network tutorial as a configurable
reader persona, actually executes the tutorial's verifiable steps against the
real Midnight toolchain, and produces an HTML report plus a chat summary of
where — and for which kind of reader — the tutorial breaks down.

## What it does

Point it at a Midnight tutorial (a URL, a local file, or pasted text) and it:

1. **Maps & ingests** the tutorial — when the source is one page of a
   multi-page series, it discovers the whole tutorial by following in-scope
   *Next*/*Previous* links (and gathers any *Prerequisites* it references,
   which may themselves be multi-page), being careful not to wander into a
   *different* tutorial the last page happens to link to. It shows you the
   discovered **Prerequisites** and **Tutorial pages** lists and waits for
   your confirmation/corrections, then fetches or reads every confirmed page
   — links may be URLs or local file paths, even mixed in one
   document — and segments them into an ordered list of steps.
2. **Resolves** one or more reader personas — a bundled preset, an axis-level
   override, a freeform natural-language description, or a comparative sweep
   of several personas at once.
3. **Walks** every step twice per persona, through two independent channels:
   - a **knowledge-gate (persona) channel** that judges whether *this*
     persona — given its experience, patience, domain knowledge, tooling
     comfort, and reading comprehension — could plausibly follow the step as
     written; and
   - a **ground-truth (execution) channel** that actually runs the step's
     verifiable action (a `compact compile`, a contract-only snippet, a
     contract+witness pair, or a devnet-touching SDK call) and records
     whether it genuinely works, independent of who's reading it.

   The walk audits the **whole** tutorial in a single pass. When a persona
   hits a show-stopper the report marks where they would give up
   (`fellOffAtStep`), but the checker keeps going — so one run lists *every*
   show-stopper and blocker to fix, rather than reporting only the first and
   forcing you to re-run after each fix.
4. **Synthesizes** both channels into a structured `report-data` object —
   one entry per persona, with per-step findings, a completion verdict, and
   severity counts.
5. **Reports** the result as a self-contained HTML file under
   `./tutorial-reports/` plus a concise chat summary.

The point is to catch two different classes of tutorial problems at once:
places where the *prose* assumes knowledge a given reader doesn't have, and
places where the *commands* are simply broken, regardless of who's reading
them.

## Installation

This is a standard Claude Code plugin — three ways to install it:

**From a local checkout** (this repository):

```
/plugin marketplace add /path/to/midnight-tutorial-checker
/plugin install midnight-tutorial-checker
```

**From a git remote**, once published:

```
/plugin marketplace add <git-url-or-owner/repo>
/plugin install midnight-tutorial-checker
```

**For plugin development**, symlink or clone the repo directly into your
Claude Code plugins directory so edits are picked up without reinstalling.

No `npm install` is required — the report renderer and test suite use only
Node.js built-ins (`node:fs`, `node:test`, `node:assert`).

## Usage

```
/check-tutorial <url|filepath|content> [flags]
```

`source` is positional and can be a URL (`http://…`/`https://…`), a local
filepath, or literal pasted tutorial content — whichever comes before the
first recognized flag.

### Flags

| Flag | Kind | Meaning |
|---|---|---|
| `--student` | preset | Beginner developer, no blockchain background. `experience: beginner`, `patience: medium`, `domain-knowledge: none`, `tooling: some`, `comprehension: fluent`. |
| `--hobbyist` | preset | Weekend tinkerer with some prior chain exposure. `experience: intermediate`, `patience: high`, `domain-knowledge: some`, `tooling: some`, `comprehension: fluent`. **This is the default persona when no persona flags of any kind are given.** |
| `--dev-new-to-web3` | preset | Experienced software engineer, new to blockchain/crypto specifically. `experience: expert`, `patience: medium`, `domain-knowledge: none`, `tooling: strong`, `comprehension: native`. |
| `--expert` | preset | Experienced Midnight/ZK developer. `experience: expert`, `patience: low`, `domain-knowledge: strong`, `tooling: strong`, `comprehension: native`. |
| `--non-native-speaker` | preset | Technically competent reader with limited English fluency. `experience: intermediate`, `patience: medium`, `domain-knowledge: some`, `tooling: some`, `comprehension: basic`. |
| `--experience <level>` | axis override | `none` \| `beginner` \| `intermediate` \| `expert`. Single-persona runs only. |
| `--patience <level>` | axis override | `low` \| `medium` \| `high`. Single-persona runs only. |
| `--domain-knowledge <level>` | axis override | `none` \| `some` \| `strong`. Single-persona runs only. |
| `--tooling <level>` | axis override | `none` \| `some` \| `strong`. Single-persona runs only. |
| `--comprehension <level>` | axis override | `basic` \| `intermediate` \| `fluent` \| `native`. Single-persona runs only. |
| `--compare` | sweep | Runs the default trio — `student`, `hobbyist`, `expert` — in parallel and produces a comparative blocker matrix. |
| `--personas a,b,c` | sweep | Explicit, comma-separated list of preset names to sweep (each must be one of the five presets above). |
| `--follow-links N` | discovery | Tunes multi-page discovery (see below). By default the checker discovers the tutorial's full page set plus its prerequisites and asks you to confirm. `--follow-links 0` skips discovery (single supplied source only); `N ≥ 1` caps the discovered page count at `N`. |
| `--persona "free text"` | freeform | A freeform natural-language persona description, inferred into axis values. Single-persona runs only. |

### Persona axes

Every persona is defined by five axes — `experience`, `patience`,
`domain-knowledge`, `tooling`, and `comprehension` — each with its own set
of allowed levels. The authoritative definitions, including exactly what
each level gates and why, live in
[`skills/check-tutorial/personas/_axes.md`](skills/check-tutorial/personas/_axes.md);
the table above only summarizes the five bundled presets built from those
axes. There is deliberately no "reading-behavior" axis — the checker models
*what a persona knows and tolerates*, not how they scroll or skim.

### Resolution rules

- **No persona flags at all** (no preset, no axis flag, no `--persona`, no
  `--compare`, no `--personas`) defaults to the **`hobbyist`** preset — a
  mid-range reader. The chat summary states explicitly when this default was
  used.
- **Single-persona precedence**: preset (baseline) → individual `--<axis>`
  flags (override matching axes) → freeform `--persona` text (inferred and
  applied last). Each later source overrides only the axes it touches.
- **A sweep is triggered** by any of: an explicit `--compare`, two or more
  preset flags given together, a preset flag combined with `--personas`, or
  `--personas` alone. In every sweep, each named persona uses its stock
  preset's axis values unmodified — any `--<axis>` flag or `--persona` text
  present alongside a sweep trigger is ignored, so it can't silently apply to
  just one member of the sweep.

### Example invocation

```
/check-tutorial https://docs.midnight.network/tutorial/counter --student
```

Walks the counter tutorial at that URL as the `student` preset persona,
executing every verifiable step against the real toolchain, and writes an
HTML report to `./tutorial-reports/`.

A comparative sweep:

```
/check-tutorial ./my-tutorial.md --compare
```

Walks the same tutorial as `student`, `hobbyist`, and `expert` in parallel
and adds a blocker matrix comparing all three.

## The report

Each run produces a self-contained HTML file under `./tutorial-reports/`
(named `<tutorial-slug>-<persona-or-compare>-<timestamp>.html`) plus a chat
summary. The HTML report contains, per persona walked:

- **Persona card** — the persona's name and its five axis values
  (`experience`, `patience`, `domain-knowledge`, `tooling`, `comprehension`)
  at a glance.
- **Verdict** — whether that persona completed the tutorial or got stuck,
  the step index it fell off at (if any), a one-line summary, and a count of
  findings at each severity (`info`, `minor`, `major`, `show-stopper`).
- **Step timeline** — one row per finding, in step order: the step title,
  what kind of finding it was (`smooth`, `assumed-knowledge`, `blocker`, or
  `error`), which axis (if any) it's attributed to, its severity, whether
  the underlying command/action actually ran (`groundTruthResult`), what
  knowledge the persona needed but wasn't given, and a suggested fix.
  - The **assumed-knowledge inventory** for a persona is just its timeline
    rows of type `assumed-knowledge` — the concepts the tutorial leaned on
    without teaching.
  - The **blockers** for a persona are its timeline rows of type `blocker`
    or `error` — points where that persona (or the command itself) could
    not proceed.
- **Blocker matrix** (`--compare` runs only) — a persona-by-step grid
  showing the worst severity each persona hit at each step, so you can see
  at a glance where personas diverge (e.g. a student blocked at step 2 while
  an expert sails through).
- **Recommendations** — the `suggestedFix` text attached to each
  non-trivial finding: a concrete, minimal edit (define a term on first use,
  show expected output, add a missing flag) rather than a vague "improve
  this section." Drawn from the timeline's `suggestedFix` column, not a
  separate rendered panel.

The chat summary echoes the verdict(s), the top show-stopper findings across
all personas walked, the most common assumed-knowledge gaps, and the
report's file path (both as a clickable `file://` URI and the relative
`./tutorial-reports/...` path).

## Ground-truth execution requires the Midnight toolchain

The ground-truth (execution) channel is not a simulation — it genuinely
compiles code, runs circuits, and (for SDK/devnet steps) deploys and calls
contracts. That means a full run depends on:

- The **Midnight Compact CLI** being installed and on `PATH`, for direct
  compile checks and for the dispatched `midnight-verify` agents
  (`cli-tester`, `contract-writer`, `witness-verifier`, `sdk-tester`) that
  handle anything beyond a plain compile.
- A **local Midnight devnet** (node + indexer + proof server) running and
  healthy, for any step that deploys a contract, calls a circuit, or
  otherwise talks to a live network. The checker reuses a running devnet —
  it never starts or restarts one as a side effect of a health check — and
  serializes devnet-touching actions across a `--compare` sweep so parallel
  personas don't corrupt each other's results.
- The **`midnight-verify` plugin's agents** being available for dispatch, so
  ground-truth results for anything beyond a bare CLI compile can be
  observed and interpreted rather than guessed.

If any of these are missing or unreachable, the checker does not fabricate a
`pass` or `fail` — it records `groundTruthResult: "n/a"` with a `detail`
explaining that the check was environment/tooling-limited, and the persona
(knowledge-gate) channel still runs and reports independently.
