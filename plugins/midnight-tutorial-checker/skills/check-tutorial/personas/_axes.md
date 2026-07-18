# Persona axes

Five axes describe a persona. Every preset in this directory sets all five as
flat `key: value` frontmatter (see any `*.md` file next to this one). The
`persona-runner` agent reads a persona's axis values and uses them to gate
each tutorial step's demands: a demand that falls inside the persona's level
is handled without friction; a demand that falls outside it becomes an
`assumed-knowledge` or `blocker` finding (see
`skills/check-tutorial/references/report-schema.md` for the finding schema).

## Levels

| Axis | Allowed levels |
| --- | --- |
| `experience` | `none`, `beginner`, `intermediate`, `expert` |
| `patience` | `low`, `medium`, `high` |
| `domain-knowledge` | `none`, `some`, `strong` |
| `tooling` | `none`, `some`, `strong` |
| `comprehension` | `basic`, `intermediate`, `fluent`, `native` |

Values must be single tokens with no spaces — they are used as CSS class
names by the HTML renderer (e.g. `val-<value>`-style classes for axis
badges), so hyphens/underscores are fine but multi-word phrases are not.

## How each axis shifts the knowledge-gate

### `experience` — general software-development experience

- `none` — cannot be assumed to know what a terminal, a variable, or a
  function is; any step that leans on general programming fluency (not just
  Midnight-specific concepts) is gated.
- `beginner` — knows the basics of coding (variables, functions, running a
  script) but has shallow exposure to real projects; multi-file setups,
  package managers, and non-trivial error messages are gated.
- `intermediate` — comfortable building and debugging ordinary applications;
  only unusual or advanced software-engineering demands (e.g. concurrency,
  build-tool internals) are gated.
- `expert` — nothing on general software-development grounds is gated;
  findings on this axis only fire for Midnight-specific novelty, which is
  covered by `domain-knowledge` instead.

### `patience` — tolerance for friction before giving up

- `low` — the first unexplained-but-*surmountable* error, ambiguous
  instruction, or dead link (one the tutorial does document a way through)
  escalates straight to a `blocker`/`show-stopper` finding; this persona does
  not troubleshoot.
- `medium` — will retry an unclear step once or follow one extra link before
  giving up; a second unresolved *surmountable* friction point in the same
  step escalates.
- `high` — will dig through error output, search for undocumented steps, and
  keep going through an extended run of repeated, individually-surmountable
  friction without escalating on that accumulation alone.

Unlike the other axes, `patience` does not gate *what* a step demands — it
gates how many surmountable, ungapped frictions accumulate before a
finding's severity is escalated from `minor`/`major` toward `show-stopper`.
This governs *only* the accumulation path: a genuinely broken command or a
true dead end (a gated demand that blocks mechanical progress with no
documented path forward) is not surmountable friction to accumulate against
— it stops every persona immediately, on first contact, regardless of
patience level. `patience` buys tolerance for friction, not immunity to dead
ends.

### `domain-knowledge` — blockchain / crypto / zero-knowledge familiarity

- `none` — blockchain, crypto, and ZK terms (witness, DUST, nullifier,
  proof server, shielded/unshielded, disclose) are treated as **undefined**
  unless the tutorial defines them inline on first use.
- `some` — foundational terms (wallet, transaction, smart contract) are
  assumed known; Midnight-specific or ZK-specific terms (witness, nullifier,
  DUST, disclose) still need a definition or link.
- `strong` — the full Midnight/ZK vocabulary is assumed known; findings on
  this axis only fire for genuinely novel or contract-specific concepts the
  tutorial introduces without any explanation at all.

### `tooling` — TypeScript/JS proficiency, CLI comfort, environment setup

- `none` — cannot be assumed to have Node, a package manager, Docker, or a
  terminal already working; every environment-setup instruction (install,
  path, env var, compiler flag) must be spelled out or it's gated.
- `some` — has a working dev environment and basic CLI comfort, but
  unfamiliar/uncommon flags, multi-step Docker Compose setups, or
  project-specific tooling (the Compact CLI, devnet scripts) need explicit
  instructions.
- `strong` — comfortable with CLIs, Docker, and TypeScript tooling in
  general; only Midnight-specific tool quirks (undocumented compact CLI
  flags, proof-server ports) are gated.

### `comprehension` — English fluency / reading level

- `basic` — short sentences and common vocabulary only; idioms, dense
  paragraphs, or jargon-heavy explanations (even if the jargon is
  *technically* defined) risk being misread or skipped, gating the step.
- `intermediate` — can follow longer sentences and common technical
  vocabulary; idiomatic phrasing, humor, or ambiguous pronoun references
  still risk misreading.
- `fluent` — reads technical prose comfortably; only genuinely ambiguous
  wording or missing referents (e.g. "then run it" with an unclear
  antecedent) are gated.
- `native` — nothing is gated on comprehension grounds alone; findings on
  this axis only fire for prose that is ambiguous or unclear to any reader,
  regardless of fluency.

## Precedence rule

When resolving the persona for a run, later sources override earlier ones
for any axis they touch:

1. **Preset** — a `--student` / `--hobbyist` / `--dev-new-to-web3` /
   `--expert` / `--non-native-speaker` flag selects one of the files in this
   directory and supplies all five axis values as a baseline.
2. **Individual flags** — `--experience beginner --patience low` (etc.)
   override the preset's value for that specific axis only; axes not
   mentioned keep the preset's value.
3. **Freeform** — a `--persona "<free text>"` description is inferred into
   axis values and applied last, filling in (or overriding) any axis not
   already pinned by a preset or an individual flag.
