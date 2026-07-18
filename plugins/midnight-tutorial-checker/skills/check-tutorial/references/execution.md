# Ground-truth execution & isolation reference

This document tells `persona-runner` (Task 8) how to run the **ground-truth
channel** — actually executing a tutorial's verifiable steps, as distinct
from the persona (knowledge-gate) channel in
`skills/check-tutorial/references/knowledge-gate.md` — and how the SKILL
(Task 9) isolates each run so the checker never disturbs the user's project
or the shared devnet. It also defines how execution outcomes become the
`groundTruthResult` field of a `finding`
(`skills/check-tutorial/references/report-schema.md`).

The two channels are always kept separate while walking a step: the
knowledge-gate procedure judges whether *this persona* could follow the
step; this document governs whether the step's *underlying command or code
actually works*, independent of who is reading it. They only meet at
`groundTruthResult: "fail"`, per Recording results below.

## Ground-truth channel

Not every step has something to execute. Before dispatching anything,
classify the step's verifiable action (if any) into one of the kinds below,
then route it accordingly:

| Step kind | How it's executed |
| --- | --- |
| Pure compile/CLI check — the step's only verifiable action is `compact compile ...` or another direct Compact CLI invocation, with no witness/SDK/devnet involved | Run the stated command directly via the installed Compact CLI, inside the persona's scratch workspace (see Isolation). For anything beyond a plain compile — flag behavior, exit codes, `--skip-zk`, version output, comparing CLI output against the tutorial's claims — dispatch to the `midnight-verify:cli-tester` agent instead of hand-rolling the check. |
| Contract-only step — the reader writes or edits Compact contract code, no witness needed yet | Dispatch to the `midnight-verify:contract-writer` agent: it turns the step's contract snippet into a minimal compilable unit, compiles it with the Compact CLI, runs it via `@midnight-ntwrk/compact-runtime`, and reports what it observed. |
| Contract + witness step — the step pairs Compact contract code with a TypeScript witness implementation | Dispatch to the `midnight-verify:witness-verifier` agent: it compiles the contract, type-checks the witness against the generated `Witnesses` type, runs its structural checklist, and executes the combined contract+witness pipeline. |
| SDK / devnet step — the step deploys a contract, calls a circuit, or otherwise talks to a running Midnight network | Confirm devnet liveness (below), then dispatch to the `midnight-verify:sdk-tester` agent: it writes and runs an E2E script (raw SDK or testkit-js) against the live devnet and reports the observed result. |
| Non-executable step — prose-only explanation, a diagram, a conceptual aside with no command or code to run | Nothing to execute. Record `groundTruthResult: "n/a"` directly (see Recording results); no agent is dispatched for this step. |

**Devnet liveness rule.** Before dispatching any devnet-touching step — i.e.
before `sdk-tester` makes its devnet call — check liveness with the
`midnight-tooling:devnet-health` skill. **Reuse a running, healthy devnet;
never blindly restart it.** If devnet-health reports the stack is down, do
not start it yourself as a side effect of a health check — that decision
belongs to the Safety rule below: starting the devnet is a heavy action and
only happens through the harness's own permission prompt, and only when the
tutorial's step actually calls for it.

Each dispatched agent reports a raw observation of what it saw when it tried
the step's action — not a ready-made verdict. The `Confirmed` / `Refuted` /
`Inconclusive` vocabulary in `midnight-verify:verify-correctness` is
synthesized by the `/midnight-verify:verify` command's own orchestrator (the
main thread running that skill), which `persona-runner` never invokes here:
it dispatches `contract-writer`, `witness-verifier`, `sdk-tester`, and
`cli-tester` directly, bypassing that command's routing and synthesis step
entirely. So `persona-runner` reads each agent's reported observation itself
— e.g. "the contract compiled and the circuit executed, returning X",
"compilation failed with error Y", or "could not run: the devnet was down" —
and interprets that observation directly into `groundTruthResult` (see
Recording results for the exact mapping).

## Isolation

Each run, and each persona within a `--compare` sweep, gets its own scratch
workspace. Nothing the ground-truth channel does is ever written into, or
executed against, the user's project checkout.

Concrete scratch path pattern:

```
<session-scratchpad>/check-tutorial/<run-id>/<persona-slug>/
```

- `<session-scratchpad>` — the harness-provided, session-specific scratch
  directory (the same directory an agent is told to use for temporary files
  for the current session).
- `<run-id>` — `<tutorial-slug>-<timestamp>`, the same slug/timestamp pair
  used to name the final HTML report
  (`./tutorial-reports/<slug>-<persona-or-compare>-<timestamp>.html`), so a
  run's scratch state and its report can be correlated by eye.
- `<persona-slug>` — the persona's preset name (`student`, `expert`, ...) or
  a short slug derived from a freeform persona description. Single-run mode
  has exactly one persona-slug directory under the run-id; `--compare`
  fans out one per persona.

Everything the ground-truth channel produces for a persona/step — scaffolded
contract files, compiled output, witness scratch files, `node_modules`,
generated SDK scripts, intermediate report-data JSON — lives under that
persona's own subtree (e.g. `.../student/contracts/`, `.../student/sdk/`).
Nothing under one persona's directory is read or reused by another persona's
runner, even while they race in parallel during a `--compare` sweep — each
persona's ground-truth verdicts must be reached independently.

The **one deliberate exception** is the final HTML report itself, written by
design to `./tutorial-reports/...` inside the user's project (per the design
spec) — that is the skill's actual deliverable, not incidental working
state, and the only artifact the skill ever writes back into the project.

`persona-runner` (T8) receives its scratch path as an explicit argument at
dispatch time, built by the orchestrating SKILL (T9). It creates the
directory if it doesn't already exist and treats it as fully disposable —
nothing under it needs to survive past the run, and the skill never assumes
it is still there on a later invocation.

## Devnet serialization

The local devnet (`midnight-tooling:devnet`) is a single shared stack — one
node + indexer + proof server, not one per persona. A `--compare` sweep
dispatches multiple `persona-runner` agents in parallel, but they cannot all
touch the devnet at once: two personas racing to deploy/call/submit against
the same node would corrupt each other's ground-truth results (wrong
nonces, state one persona didn't cause, a contract address that belongs to a
different persona's walkthrough).

Serialization mechanism: a directory-based mutex held at the **run level**
— shared across every persona in the sweep, not per-persona:

```
<session-scratchpad>/check-tutorial/<run-id>/.devnet.lock/
```

- Before any devnet-*mutating* action (deploy, `callTx`/`submitCallTx`,
  wallet funding/transfer — anything `sdk-tester` does against the live
  network; plain `devnet-health` reads do **not** need the lock), a
  `persona-runner` attempts to acquire the lock. `mkdir` is atomic, so
  `mkdir .devnet.lock` either succeeds (lock acquired) or fails because the
  directory already exists (held by another persona).
- On success, write a small `holder` file inside it (persona slug, agent
  id, acquisition timestamp) for diagnosability, run the devnet-touching
  step, then remove the lock directory to release it.
- If the lock is already held, poll with a short backoff (a few seconds at
  a time) until it clears, rather than failing the step outright — a
  `--compare` sweep with a handful of personas is expected to see brief
  queuing here, not contention failures.
- Stale-lock recovery: if `holder`'s timestamp is older than a generous
  ceiling (long enough to cover a real deploy-and-observe cycle, e.g.
  several minutes), treat the lock as orphaned — its owner crashed or was
  interrupted — and reclaim it rather than deadlocking the rest of the
  sweep.

This keeps devnet-touching ground truth strictly one-persona-at-a-time
while leaving everything else in the sweep — the persona/knowledge-gate
channel, and non-devnet ground-truth checks (compile, `contract-writer`,
`witness-verifier`) — fully parallel.

## Safety

Run every command exactly as the ambient Claude Code permission mode
allows. Do not build a bespoke confirmation or `--yes` flow anywhere in
this pipeline. `persona-runner` and every `midnight-verify` agent it
dispatches to inherit and rely on the harness's own prompts for anything
that needs a human nod.

Heavy or irreversible actions — installing dependencies, starting
Docker/the devnet, deploying a contract on-chain — surface through the
harness's own permission prompts exactly as they would for any other tool
invocation. If a prompt blocks a parallel `--compare` run, that is expected
and correct: pause for it, do not route around it.

Consulting `midnight-tooling:devnet-health` is a read-only status check and
never itself triggers a heavy prompt; only an actual start/`docker compose
up` action — dispatched deliberately, and only when the tutorial's own step
calls for it — does.

Never suppress, auto-answer, or pre-empt a permission prompt on the agent's
behalf, in any persona or any channel. A declined prompt is a legitimate
outcome and should be recorded plainly (see Recording results) rather than
retried with an escalated flag.

## Recording results

Each dispatched agent (`contract-writer`, `witness-verifier`, `sdk-tester`,
`cli-tester`) — or the direct CLI check for a plain compile — returns a raw
observation of what happened, not a pre-labeled verdict. `persona-runner`
interprets that observation itself to set `groundTruthResult` (`pass | fail |
n/a`, exactly as defined in `report-schema.md`), using the mapping below:

| What was observed | `groundTruthResult` |
| --- | --- |
| Step had nothing verifiable (prose/conceptual only, per Ground-truth channel's "Non-executable step" row) — no agent dispatched | `n/a` |
| The step's action was attempted and succeeded, matching the tutorial's expected result — the contract compiled, the circuit executed and returned the expected value, the CLI command produced the documented output, or the deploy/call against devnet succeeded | `pass` |
| The step's action was attempted but errored, or ran and produced a result that contradicts what the tutorial documents — a compile error, a circuit that threw or returned the wrong value, a CLI command that failed against the tutorial's own claim, or a failed deploy/call | `fail` |
| The step's action could not be attempted because the environment blocked it — devnet unreachable, proof server unavailable, the CLI missing from `PATH` — rather than because the agent found anything wrong with the tutorial's own content | `n/a` |

A `fail` result must also emit an `error`-type finding (see below);
environment-blocked `n/a` results must say so plainly in the finding's
`detail` (see the note below the table).

`n/a` covers two different situations that must not be blurred together in a
finding's `detail`: (1) genuinely nothing to execute, and (2) something to
execute that the environment prevented from running. Both map to the same
`groundTruthResult`, but `detail` must say which one occurred — and for case
(2) specifically, name what blocked it (e.g. "devnet was unreachable;
`sdk-tester` could not attempt the deploy") — so a report reader doesn't
mistake "we couldn't check" for "the tutorial's happy path is broken."

Note on scope: `knowledge-gate.md` describes `n/a` in the finding-schema
table as applying "only to purely conceptual gaps with nothing to execute."
This document's three-value enum has no fourth option for "blocked by the
environment," so execution.md deliberately broadens `n/a` to also cover that
case rather than inventing a new enum value — the `detail`-field distinction
above is what keeps the two situations from being conflated in practice.

Whenever `groundTruthResult` resolves to `fail`, `persona-runner` must emit
(per `knowledge-gate.md` §4, row 1) a finding with `type: "error"`,
`axis: "none"`, and `severity: "show-stopper"` if the tutorial documents no
workaround for the failure, or `"major"` if it does — identically for every
persona walking that step, independent of any persona axis. This is the one
place the ground-truth and persona channels are required to meet: a broken
command overrides persona-specific judgement for that step.

`suggestedFix` on a `fail` finding should describe the concrete, minimal
correction the dispatched agent's evidence pointed to (a stale flag, a
version pin, a wrong path) — not just restate that the step doesn't work.

`pass` and `n/a` findings still let the persona channel run independently:
see `knowledge-gate.md` rows 2–5 for how a `pass`/`n/a` step resolves to
`smooth`, `assumed-knowledge`, or `blocker` based on the persona's gated
demands, not the ground truth.
