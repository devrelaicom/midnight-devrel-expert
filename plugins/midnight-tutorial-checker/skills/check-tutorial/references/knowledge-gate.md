# Knowledge-gate procedure

This is the procedure `persona-runner` (Task 8) runs **once per tutorial step**
to turn that step into zero or more `finding` objects (see
`skills/check-tutorial/references/report-schema.md` for the exact finding
shape and enum values). It has five stages, run in order:

1. Extract demands
2. Tag each demand with an axis
3. Gate against the persona
4. Assign type and severity
5. Emit a finding

The persona channel (this procedure) and the ground-truth channel (actually
running the step's command/action) are kept separate throughout. A step's
demands are judged against the persona *regardless* of whether the underlying
command happened to work; the two channels only meet in Section 4, where a
ground-truth failure overrides persona judgement.

## 1. Extract demands

Before any axis or persona is considered, read the step's prose, code blocks,
and expected output, and enumerate everything the reader is required to
already have, in three buckets:

- **Concepts** — jargon, terms, or ideas the step uses without teaching them
  (e.g. "witness", "the proof server", "a nullifier").
- **Skills** — abilities the step assumes the reader already has (e.g.
  reading a stack trace, editing a multi-file project, knowing what a CLI
  flag is).
- **Environment state** — anything the step assumes is already true of the
  reader's machine or session, whether from an earlier step or left
  unstated (e.g. "Docker is running", "the CLI from step 1 is on PATH", "a
  second terminal is open").

List every demand you find, even if it looks trivial — triviality is decided
later, in Section 3, by comparing against the persona, not here.

### Worked example 1

Step text: *"Add a witness that returns the user's secret balance, then run
`compact compile --skip-zk contracts/counter.compact` to confirm it
compiles."*

Extracted demands:

- Concept: what a "witness" is and why its value stays private.
- Concept: the compiler distinguishes a witness from a circuit (implied,
  not stated).
- Skill: editing a Compact source file.
- Skill: reading `compact compile` output well enough to tell success from
  failure.
- Environment state: the Compact CLI is already installed and on `PATH`
  (assumed carried over from an earlier step).
- Environment state: `contracts/counter.compact` already exists with the
  scaffolding this snippet is meant to be added to.

### Worked example 2

Step text: *"Open a second terminal, start the proof server with `docker
compose up proof-server -d`, then run the wallet sync script. If you see
`ECONNREFUSED`, make sure Docker Desktop is running."*

Extracted demands:

- Concept: what the proof server is and why the wallet needs it running.
- Skill: comfort managing more than one terminal/session at once.
- Skill: recognizing and interpreting a network error code
  (`ECONNREFUSED`) well enough to act on the stated fix.
- Environment state: Docker (and Docker Desktop specifically) is installed.
- Environment state: the wallet sync script referenced here was created by
  an earlier step and still works.

## 2. Tag each demand with an axis

Every demand extracted in Section 1 gets tagged with exactly one of the five
axes from `skills/check-tutorial/personas/_axes.md`:
`experience | patience | domain-knowledge | tooling | comprehension`. Use
this rule of thumb, applied to the demand's *category* from Section 1:

| Demand looks like… | Axis |
| --- | --- |
| A blockchain/crypto/ZK term or Midnight-specific concept (witness, nullifier, DUST, disclose, shielded/unshielded) | `domain-knowledge` |
| A general software-engineering skill or concept not specific to Midnight (what a function/variable is, reading an ordinary stack trace, multi-file project layout) | `experience` |
| A CLI/tool/environment requirement (installing something, a flag, `PATH`, Docker, a package manager, a compiler switch) | `tooling` |
| Dense, idiomatic, or ambiguous prose — independent of whether the underlying fact is ever defined | `comprehension` |

`patience` is never assigned in this step. Per `_axes.md`, patience does not
gate *what* a step demands — it gates *how many* already-gated demands a
persona will tolerate before a finding's severity escalates. Patience is only
applied later, in Section 4.

Examples (matching the brief's canonical cases):

- "knows what a witness is" → `domain-knowledge`.
- "read a TS/Node stack trace" → `tooling` (interpreting CLI/runtime output
  is a tooling skill), while "read *any* ordinary error message and reason
  about what went wrong" with no CLI-specific knowledge required →
  `experience`.
- A jargon-dense sentence, even if every term in it is technically defined
  elsewhere → `comprehension` (the failure mode is misreading or skipping
  the sentence, not lacking the underlying concept).
- "Docker Desktop must be running" → `tooling`.

Applying this to worked example 1: "what a witness is" and "witness vs.
circuit" → `domain-knowledge`; "editing a Compact file" → `experience`
(general code-editing skill, not Midnight-specific); "reading compiler
output" and "CLI already on PATH" → `tooling`.

Applying this to worked example 2: "what the proof server is" →
`domain-knowledge`; "managing two terminals" → `experience`; "interpreting
`ECONNREFUSED`" and "Docker installed" → `tooling`.

## 3. Gate against the persona

For each tagged demand, compare the level it implicitly requires against the
persona's configured level for that axis (`skills/check-tutorial/personas/_axes.md`
defines the allowed levels per axis and what each level does and does not
cover). Walk the axis's level list in the order given in `_axes.md` — each
level's description states what is still gated at that level and what is no
longer gated. If the persona's level covers the demand (the demand is called
out as *not* gated at that level or below it), the demand passes the gate
silently and contributes no finding. If the persona's level does not cover
the demand — the demand falls in the "still gated" set for that level — it
becomes a **candidate finding** carried into Section 4.

Rule for `domain-knowledge` specifically: do not decide from first
principles whether a Midnight/blockchain/ZK term is "assumed knowledge" for
this persona. Instead, look the term up in
`skills/check-tutorial/references/midnight-concepts.md` (a sibling
reference) to find which knowledge tier it belongs to, and compare that tier
against the persona's `domain-knowledge` level per the tier boundaries
`_axes.md` describes for `none`/`some`/`strong`. If the term isn't listed
there, treat it conservatively as **not** assumed knowledge (i.e. gate it)
rather than guessing.

Rule for `patience`: track, per step, how many candidate findings have
already been produced by this loop. `patience` doesn't decide *whether* a
demand is gated — it decides how much a run of *surmountable* already-gated
demands (comprehension-only gaps, or blocker gaps with a documented
workaround) in the same step escalates severity in Section 4: a low-patience
persona escalates on the very first one; medium on the second unresolved
one; high tolerates an extended run of such friction before escalating on
accumulation alone. A genuine dead end — a gated demand that blocks
mechanical progress with no documented path forward anywhere — is not part
of this accumulation and is not gated by patience at all: it resolves to
`show-stopper` immediately for every persona, regardless of patience level
(Section 4, row 5). Carry the per-step count of surmountable candidates
forward into Section 4.

Worked example 1 against the `student` preset (`experience: beginner,
domain-knowledge: none, tooling: some`): "what a witness is" is gated
(`domain-knowledge: none` treats ZK/Midnight terms as undefined) →
candidate. "editing a Compact file" is not gated (`experience: beginner`
covers ordinary code editing) → passes silently. "CLI already on PATH" is
not gated (`tooling: some` covers a working CLI already set up from a prior
step) → passes silently.

## 4. Assign type and severity

Every candidate finding (plus the step's ground-truth result) resolves to
exactly one `type` and one `severity` via the table below, read top to
bottom — the first matching row applies.

| # | Condition | `type` | `severity` |
| --- | --- | --- | --- |
| 1 | `groundTruthResult` is `fail` (the real command/action genuinely did not work) | `error` | `show-stopper` if the tutorial gives no documented workaround; `major` if it does. This applies to **every** persona identically — a broken command blocks everyone regardless of axis levels. |
| 2 | `groundTruthResult` is `pass`/`n/a` and no demand from Section 3 was gated for this step | `smooth` | `info` |
| 3 | A demand was gated, the gap does not stop the persona from completing the step's required action (it's informational — they can still type the command / click the button without understanding the term), and this step's patience threshold (see below) has not yet been crossed | `assumed-knowledge` | `minor` |
| 4 | A demand was gated, the gap *does* stop the persona from completing the step's required action (they cannot tell what value to use, which flag applies, or what the next literal action is), **but the tutorial documents a path forward** elsewhere (a workaround, a link, a later step that fills the gap), and this step's patience threshold has not yet been crossed | `blocker` | `major` |
| 5 | A demand was gated, the gap stops the persona's mechanical progress exactly as in row 4, **and the tutorial documents no path forward anywhere** — a genuine dead end, with nothing left to try and nowhere to look | `blocker` | `show-stopper` — **immediately, independent of the patience counter.** A dead end is a dead end on the first encounter; it does not need a second gap or an exhausted patience budget to qualify. |
| 6 | A demand was gated (whether currently classed as row 3, or row 4 with a documented workaround) and this step's patience threshold **has** been crossed | `blocker` | `show-stopper` |

**Patience threshold**, evaluated per step using the running count from
Section 3 and the persona's `patience` level (`_axes.md`). This threshold
governs only the *accumulation* path to `show-stopper` (row 6): repeated
row-3 comprehension-only gaps, or row-4 gaps that each have their own
documented workaround, piling up until the persona's tolerance runs out. It
has no bearing on row 5 — a genuine dead end escalates on first contact
regardless of patience level, because there is nothing left to accumulate
against.

- `low` — crossed on the **first** gated demand in the step.
- `medium` — crossed on the **second** gated demand in the step that
  remains unresolved (the first gap alone does not cross it).
- `high` — crossed only after an extended run of accumulated, individually-
  resolvable friction (row-3 gaps, or row-4 gaps each with their own
  workaround) with no relief in sight — many more than a second or third
  gap. A persona at any patience level that instead hits a genuine dead end
  (row 5: no documented path forward at all) escalates immediately; `high`
  patience buys tolerance for friction, not immunity to dead ends.

**`show-stopper` is defined as**: this persona cannot proceed past this step
without outside help — leaving the tutorial to search elsewhere, asking
another person, or the tutorial's own next step being impossible to perform
without the missing knowledge. This is exactly what row 5 (an immediate,
undocumented dead end) and row 6 (accumulated friction past the patience
threshold) both describe, from two different paths to the same outcome. The
*first* `show-stopper` finding of the walk sets `verdict.fellOffAtStep` (in
the assembled report) to its step — but classifying a step as `show-stopper`
never ends the walk: it marks where the persona would give up, while the
audit continues through every remaining step so one pass surfaces every
show-stopper (see `persona-runner`'s Section 2).

**`error` note**: `error` is reserved exclusively for row 1 — a ground-truth
failure. It is never assigned to a finding whose only problem is a gated
demand; those are always `assumed-knowledge` or `blocker`. Conversely, `error`
is never downgraded based on persona axes: the command either worked or it
didn't, independent of who is reading.

**`assumed-knowledge` vs. `blocker`**: both are persona-specific and both can
occur on the same tutorial for different personas at the same step. The
distinguishing question is whether the gap stops forward *mechanical*
progress (rows 4/5 → `blocker`) or only understanding while the reader can
still technically continue (row 3 → `assumed-knowledge`). Among the
`blocker` rows, row 4 has a documented way through (so it starts at `major`
and only reaches `show-stopper` via row 6's patience accumulation) while row
5 has none at all (so it is `show-stopper` immediately). Row 6 shows that
either row 3 or row-4-with-a-workaround can still escalate to
`blocker`/`show-stopper` once patience runs out, even without ever hitting a
row-5 dead end.

## 5. Emit a finding

For each candidate resolved in Section 4 (plus exactly one `smooth` finding
per row-2 step, and exactly one `error` finding per row-1 step, in addition
to — not instead of — any unrelated gated demands the same step also
produced), populate every field of the finding schema
(`skills/check-tutorial/references/report-schema.md`):

| Field | How to populate it |
| --- | --- |
| `step` | The 1-based index of the step currently being walked. |
| `title` | Copy verbatim from this step's entry in `report-data.steps[].title`. |
| `type` | The value resolved in Section 4 (`smooth`, `assumed-knowledge`, `blocker`, or `error`). |
| `axis` | The axis assigned in Section 2 for the demand this finding is about; `none` for `smooth` findings and for `error` findings (a ground-truth failure is not attributable to any persona axis). |
| `severity` | The value resolved in Section 4 (`info`, `minor`, `major`, `show-stopper`). |
| `knowledgeNeeded` | The specific concept, fact, or skill from Section 1 that the persona lacked (e.g. `"what a witness is and why it is private"`). Empty string `""` for `smooth` and `error` findings, since there is no missing knowledge to name. |
| `groundTruthResult` | `pass`, `fail`, or `n/a` — whatever was actually observed when the step's command/action was executed independently of persona judgement. `n/a` only applies to purely conceptual gaps with nothing to execute. |
| `suggestedFix` | One concrete edit to the tutorial that would remove this finding (e.g. `"Define 'witness' on first use and link to the privacy concept page."`). Empty string `""` when there is nothing to suggest (typically only for `smooth` findings; an `error` finding should still suggest a fix if the failure is fixable in the tutorial's own instructions, e.g. a stale flag). |
| `detail` | Free-text explanation of what was actually observed at this step, written so a tutorial author can act on it without re-deriving Sections 1–4 themselves. |

Ordering: emit findings for a step in the order their demands were extracted
in Section 1. A step produces at least one finding; it may produce several
when multiple independent demands are gated for the same persona (e.g. an
`assumed-knowledge` finding for a jargon term and a separate `blocker`
finding for a missing environment-state assumption in the same step).
