# Build a Midnight Counter

A short walkthrough that scaffolds a tiny Compact contract exposing a
single on-chain counter, then compiles it.

## Step 1: Install the Compact CLI

Make sure the Compact CLI is installed and on your `PATH`:

```bash
compact --version
```

You should see a version string printed back, e.g. `compact 0.5.1`. If the
command isn't found, install the CLI before continuing.

## Step 2: Create your project folder

Make a fresh working directory for this tutorial and move into it:

```bash
mkdir counter-tutorial
cd counter-tutorial
```

Everything in the rest of this guide happens inside `counter-tutorial/`.

## Step 3: Write the counter contract

Here's the full contract. The `ledger` block declares the contract's
on-chain state — a `Counter` field called `round_count` that lives on the
blockchain and can only be changed from inside the contract. Read through it
before moving on:

```compact
pragma language_version >= 0.13;

import CompactStandardLibrary;

export ledger round_count: Counter;

witness getRoundBonus(): Uint<16>;

export circuit increment(): [] {
  const bonus = getRoundBonus();
  round_count.increment(1 + (bonus as Uint<64>));
}
```

A `circuit` is a callable entry point — the exported function outside
callers invoke to change the ledger's state. The `increment` circuit above
bumps `round_count` by one plus a small bonus each time it's called.

Before moving on, implement the `getRoundBonus` witness yourself and wire it
into the project so the circuit above has something to call.

## Step 4: Compile the contract

With the contract written, compile it to check that everything is in
order:

```bash
compact compile counter.compact build
```

This produces the compiled circuits and TypeScript bindings in the `build/`
directory.

## Step 5: Next steps

From here you can wire the compiled contract up to a witness
implementation and deploy it to a local devnet — a throwaway local
Midnight test network. Congratulations on writing your first Midnight
counter contract!

<!--
PLANTED ISSUES (for the check-tutorial fixture smoke test — not part of the
tutorial itself). Exactly two, and only two:

1. Undefined dead-end concept, Step 3 ("Write the counter contract"): the
   contract declares `witness getRoundBonus(): Uint<16>;`, and the step then
   instructs the reader to "implement the `getRoundBonus` witness yourself"
   with no explanation of what a witness is, no example implementation, and
   no link anywhere else in the tutorial. A `domain-knowledge: none` persona
   (e.g. the `student` preset) cannot tell what a witness is or what code to
   write — a genuine dead end, no documented path forward — show-stopper. A
   `domain-knowledge: strong` persona (e.g. the `expert` preset) already
   knows the term and how to implement it, and proceeds smoothly.

   Note: "ledger" and "circuit" also appear in this step but are NOT planted
   issues — both are glossed inline on first use ("the `ledger` block
   declares the contract's on-chain state..."; "a `circuit` is a callable
   entry point...") specifically so a `domain-knowledge: none` reader is not
   gated on them. Only "witness" is left undefined.

2. Broken command, Step 4 ("Compile the contract"): `compact compile
   counter.compact build` fails for every persona. Step 3 never instructs
   the reader to save the shown contract to a file — there is no
   `counter.compact` (or any other file) anywhere on disk at this point in a
   fresh `counter-tutorial/` directory — so the compile command fails
   deterministically with a "no such file or directory" error, regardless of
   the reader's domain knowledge, tooling skill, or experience level.
-->
