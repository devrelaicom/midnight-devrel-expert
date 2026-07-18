---
description: Walk a Midnight tutorial as a configurable user persona and report where each kind of user gets stuck.
argument-hint: <url|filepath|content> [--student|--hobbyist|--dev-new-to-web3|--expert|--non-native-speaker] [--experience <level>] [--patience <level>] [--domain-knowledge <level>] [--tooling <level>] [--comprehension <level>] [--compare] [--personas a,b,c] [--follow-links N] [--persona "free text"]
---

# /check-tutorial

This command is a **thin entry point only**. It does not fetch the
tutorial, resolve personas, dispatch persona-runner agents, synthesize a
report, or render HTML — all of that logic lives in, and stays in, the
`check-tutorial` skill (`${CLAUDE_PLUGIN_ROOT}/skills/check-tutorial/SKILL.md`).
This command's entire job is to split `$ARGUMENTS` into a source plus a set
of raw flags, document what those flags mean, and hand them to the skill
unresolved.

## Step 1 — Split `$ARGUMENTS`

Identify, from the raw `$ARGUMENTS` string:

- **`source`** (positional) — everything before the first recognized flag
  token. A bare invocation with no flags at all treats the whole string as
  `source`. `source` is one of:
  - a URL (`http://…` / `https://…`)
  - a local filepath
  - literal pasted tutorial content
- The **raw flag tokens** present, verbatim, grouped only by *kind* (not
  interpreted or resolved — that is the skill's job):
  - `presetFlags` — any of `--student`, `--hobbyist`, `--dev-new-to-web3`,
    `--expert`, `--non-native-speaker` that appear.
  - `axisFlags` — any of `--experience`, `--patience`,
    `--domain-knowledge`, `--tooling`, `--comprehension`, each with its
    following value token.
  - `freeformPersona` — the quoted text following `--persona`, if present.
  - `compare` — whether `--compare` is present.
  - `personasList` — the comma-separated names following `--personas`, if
    present.
  - `followLinks` — the integer following `--follow-links`, if present.

Do not decide *which* persona(s) this run uses, or whether it's a
single-persona or compare run — that resolution happens in the skill's
Stage 2, not here.

## Step 2 — Flags this command supports

| Flag | Kind | Meaning |
|---|---|---|
| `--student` | preset | One of five bundled persona presets (`${CLAUDE_PLUGIN_ROOT}/skills/check-tutorial/personas/student.md`) — a full set of axis values. |
| `--hobbyist` | preset | Preset persona (`${CLAUDE_PLUGIN_ROOT}/skills/check-tutorial/personas/hobbyist.md`). **This is the default persona when no persona flags of any kind are given.** |
| `--dev-new-to-web3` | preset | Preset persona (`${CLAUDE_PLUGIN_ROOT}/skills/check-tutorial/personas/dev-new-to-web3.md`). |
| `--expert` | preset | Preset persona (`${CLAUDE_PLUGIN_ROOT}/skills/check-tutorial/personas/expert.md`). |
| `--non-native-speaker` | preset | Preset persona (`${CLAUDE_PLUGIN_ROOT}/skills/check-tutorial/personas/non-native-speaker.md`). |
| `--experience <level>` | axis override | `none` \| `beginner` \| `intermediate` \| `expert`. Applies only when resolving a single persona. |
| `--patience <level>` | axis override | `low` \| `medium` \| `high`. Applies only when resolving a single persona. |
| `--domain-knowledge <level>` | axis override | `none` \| `some` \| `strong`. Applies only when resolving a single persona. |
| `--tooling <level>` | axis override | `none` \| `some` \| `strong`. Applies only when resolving a single persona. |
| `--comprehension <level>` | axis override | `basic` \| `intermediate` \| `fluent` \| `native`. Applies only when resolving a single persona. |
| `--compare` | sweep | Runs the default trio — `student`, `hobbyist`, `expert` — in parallel and produces the comparative blocker matrix. |
| `--personas a,b,c` | sweep | Explicit, comma-separated list of preset names to sweep (each must be one of the five presets above). |
| `--follow-links N` | discovery | Tunes multi-page discovery. By default the skill discovers the tutorial's full page set (following in-scope Next/Previous links) plus its prerequisites, then asks you to confirm the map before reviewing. `N=0` skips discovery (treat the single supplied source as the whole tutorial); `N ≥ 1` caps the discovered page count at `N`. |
| `--persona "free text"` | freeform | A freeform natural-language persona description. Applies only when resolving a single persona. |

Allowed axis levels are defined authoritatively in
`${CLAUDE_PLUGIN_ROOT}/skills/check-tutorial/personas/_axes.md` — this table
mirrors, and must not drift from, that file.

**Resolution rules this command must not contradict** (full detail in the
skill's Stage 2 — this command does not implement any of it, it only
states the rules so callers know what to expect):

- **No persona flags at all** (no preset, no axis flag, no `--persona`, no
  `--compare`, no `--personas`) → defaults to the **`hobbyist`** preset.
- **Single-persona precedence**: preset (baseline) → individual `--<axis>`
  flags (override matching axes) → freeform `--persona` (inferred, applied
  last). Each later source overrides only the axes it touches.
- **A sweep is triggered** by any of: an explicit `--compare`, two or more
  preset flags given together, a preset flag combined with `--personas`,
  or `--personas` alone. In every sweep, each named persona uses its stock
  preset's axis values unmodified — any `--<axis>` flag or `--persona`
  text present alongside a sweep trigger is ignored.

## Step 3 — Invoke the skill

Invoke the `check-tutorial` skill via the `Skill` tool, passing through
exactly what Step 1 identified — the `source` plus the raw, unresolved
flag groups (`presetFlags`, `axisFlags`, `freeformPersona`, `compare`,
`personasList`, `followLinks`). Do not pre-resolve a persona profile, do
not fetch or read the source yourself, and do not skip ahead to any later
stage — Stages 1 through 5 of
`${CLAUDE_PLUGIN_ROOT}/skills/check-tutorial/SKILL.md` (ingest, resolve
persona(s), walk, synthesize, report) own all of that, in that order.
