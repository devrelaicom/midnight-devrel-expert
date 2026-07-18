# Midnight concept library

Lookup table used by the knowledge-gate procedure
(`skills/check-tutorial/references/knowledge-gate.md`, Section 3, "Gate
against the persona") to decide whether a Midnight/Compact term counts as
assumed knowledge for a given persona. For each `domain-knowledge`-tagged
demand, look the term up here rather than deciding from first principles —
and the same table also serves `tooling`-tagged demands (e.g. Devnet,
Compact CLI, `compact compile`), each marked with its own `Primary axis`
below.

- **Primary axis** — which of the five axes in
  `skills/check-tutorial/personas/_axes.md` this term is judged against,
  following the axis rule-of-thumb (blockchain/crypto/ZK concepts ->
  `domain-knowledge`; CLI/tool/environment requirements -> `tooling`).
- **Beginner-safe?** — `no` means a persona with `domain-knowledge: none`
  will **not** know this term unless the tutorial defines or links it on
  first use. Every term below is Midnight- or Compact-specific jargon, so
  every row is `no`; the column exists so a future addition that turns out
  to be genuinely common knowledge (e.g. "wallet", "transaction") can be
  marked `yes` without changing the table shape. If the persona's
  `domain-knowledge` is `some`, treat only the ZK/Midnight-specific terms
  (everything in this table) as still gated — `some` already assumes
  foundational terms like "wallet" or "smart contract", which are
  intentionally *not* listed here because they are not Midnight-specific.

| Concept | Plain definition | Primary axis | Beginner-safe? |
| --- | --- | --- | --- |
| Witness | A private input value the prover supplies to a circuit. Declared in Compact as `witness name(): Type;` and implemented separately in TypeScript. Private by default — used only to generate the ZK proof — but a contract may deliberately reveal it on-chain via `disclose()` (selective disclosure); an undisclosed witness value never appears in the public transcript. | domain-knowledge | no |
| `disclose()` | Compact stdlib function, `disclose(value: T): T`, that marks a witness-derived (private) value as safe to become public. Required before a witness-tainted value is written to the ledger, returned from an exported circuit, or passed to another contract; values produced by `persistentCommit`/`transientCommit` are exempt because commitments already clear witness taint. | domain-knowledge | no |
| Circuit | An exported or local Compact function whose logic the compiler turns into an arithmetic constraint system — a directed acyclic graph of addition/multiplication gates over a finite field — that a ZK proof is generated against. Refers to this mathematical constraint system, not an electrical circuit. | domain-knowledge | no |
| Ledger | The on-chain state of a Compact contract, declared field-by-field (e.g. `export ledger x: Type;`), holding types such as `Field`, `Counter`, `Map`, `Set`, `List`, or `MerkleTree`. Every ledger operation is publicly visible on-chain except `MerkleTree`/`HistoricMerkleTree` insert operations, which hash the leaf value (via `leaf_hash`, built on `persistentHash`) before storing it. | domain-knowledge | no |
| DUST | A shielded network resource — implemented on-ledger as a `TokenType::Dust` variant, but non-transferable and usable only for fees, unlike tradeable tokens such as NIGHT. Generated over time from NIGHT UTXOs registered for dust generation; its value is proportional to the registered NIGHT balance and decays once that NIGHT is spent. Called tDUST on testnet. | domain-knowledge | no |
| NIGHT | Midnight's native utility token, held as UTXOs on the ledger with the zero token color (`nativeToken()`); used to generate DUST. NIGHT's tokenomics design also underpins staking and governance, though in the current ledger implementation staking is carried out via the cNIGHT/Ariadne bridge rather than native NIGHT UTXOs directly, and on-chain treasury governance is not yet live. Called tNIGHT on testnet. | domain-knowledge | no |
| Proof server | A service — a Docker container (`midnightntwrk/proof-server`), default port 6300 — that generates the zero-knowledge proofs for Midnight transactions at runtime. Distinct from the Compact compiler, which produces the ZK circuits the proof server proves against. | domain-knowledge | no |
| Devnet | A local Midnight development network: a Docker Compose stack running a node, an indexer, and a proof server together, for local testing without touching testnet/mainnet. Managed via generate/start/stop/status/health operations. | tooling | no |
| Compact | Midnight's statically and strongly typed smart-contract programming language (`.compact` source files). Idiomatically opens with a `pragma language_version` declaration (a convention, not a parser-enforced requirement) and compiles to ZK circuits plus TypeScript bindings. | domain-knowledge | no |
| ZK proof | A zero-knowledge proof lets a prover show they know values satisfying a set of constraints without revealing the values themselves. Midnight uses ZK-SNARKs (Zero-Knowledge, Succinct, Non-interactive, Argument of Knowledge) to validate that a transaction follows contract rules without exposing private state. | domain-knowledge | no |
| Nullifier | A deterministic value derived from a secret (via `persistentHash` over a domain-separated vector) that lets the chain detect and block a repeated action — e.g. a double-spend or double-vote — without revealing which secret produced it. Stored publicly in a `Set<Bytes<32>>` ledger field; reuse is caught by a membership check. | domain-knowledge | no |
| Commitment | A cryptographic value produced by `persistentCommit`/`transientCommit` that hides an input value behind randomness while binding the committer to it, so the value can be revealed later and checked against the commitment (commit-reveal schemes, sealed bids). | domain-knowledge | no |
| Shielded vs. unshielded | Two token models on Midnight's ledger. Shielded tokens use zswap UTXOs (`ShieldedCoinInfo`) with ZK proofs to hide sender, recipient, and value. Unshielded tokens use the same UTXO ledger model but keep balances and transfers fully visible on-chain. | domain-knowledge | no |
| Compact CLI | The command-line tool (`compact`, typically `~/.local/bin/compact`) that manages the Compact compiler toolchain: installing/updating compiler versions, formatting and fixing up source files, and invoking compilation. Distinct from the Compact compiler binary (`compactc.bin`), which the CLI manages and invokes. | tooling | no |
| `compact compile` | The Compact CLI subcommand that invokes the compiler on a source file (`compact compile <source> <target-dir>`), producing ZK circuits and TypeScript bindings. `--skip-zk` skips proving-key generation for faster iteration; a `+VERSION` prefix pins a specific installed compiler version. | tooling | no |

## Sources

Every definition above was sourced from an installed Midnight skill, not
from model memory, per the global constraint on this reference file.

| Concept | Source skill(s) |
| --- | --- |
| Witness | `core-concepts:zero-knowledge` ("Key Concepts: Witness"), `compact-core:compact-language-ref` (witness declaration syntax) |
| `disclose()` | `compact-core:compact-language-ref` (stdlib functions table), `core-concepts:zero-knowledge` (disclose() note), `core-concepts:privacy-patterns` |
| Circuit | `core-concepts:zero-knowledge` ("Circuit Mental Model"), `compact-core:compact-language-ref` |
| Ledger | `compact-core:compact-ledger` |
| DUST | `compact-core:compact-tokens` ("NIGHT & DUST") |
| NIGHT | `compact-core:compact-tokens` ("NIGHT & DUST") |
| Proof server | `midnight-tooling:proof-server` |
| Devnet | `midnight-tooling:devnet`, `midnight-tooling:proof-server` (local-development cross-reference) |
| Compact | `compact-core:compact-language-ref`, `midnight-tooling:compact-cli` (terminology table) |
| ZK proof | `core-concepts:zero-knowledge` |
| Nullifier | `core-concepts:privacy-patterns` ("Pattern 2: Nullifier Construction") |
| Commitment | `core-concepts:privacy-patterns` ("Pattern 1: Commitment Schemes") |
| Shielded vs. unshielded | `compact-core:compact-tokens` |
| Compact CLI | `midnight-tooling:compact-cli` |
| `compact compile` | `midnight-tooling:compact-cli` |

All 15 rows were subsequently fact-checked against primary source (compiler,
ledger, and CLI/docs repos) via `midnight-fact-check:fast-check`'s
source-investigator pipeline. Five rows (Witness, Ledger, DUST, NIGHT,
Compact) were corrected in place following that check — see
`.superpowers/sdd/task-6-report.md` for the full verification log.
