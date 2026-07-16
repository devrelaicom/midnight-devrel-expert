---
name: relnotes-writing
description: Load this skill when writing the prose of a Midnight release note. It carries the voice the current relnotes are written in — cool, factual, past-tense change descriptions, inline code on every identifier — and the full set of anti-AI-trope patterns to avoid. Pair with relnotes-authoring (structure/naming/registration). Produce note prose directly; never output planning notes, voice commentary, or a verification section.
---

# relnotes Writing

The voice for Midnight release-note prose. It matches the register the current
`docs/relnotes/` notes are written in — cool, precise, factual, author-invisible.
Load `relnotes-authoring` for the structure, filename, and DynamicList
registration; this skill governs the words inside those sections.

## Core instruction

Produce the requested note prose directly. No preamble ("here's a draft"), no
sign-off, no explanation of voice choices, no verification section. Match the
exemplars below; they are the north star.

## Quick reference

| Dimension | Setting |
|---|---|
| Tone | Cool, precise, factual. Quiet authority from the content, not the writer. Zero hype, zero exclamation marks. |
| Person | Author invisible (no "I", no "we"-as-authors). Name the component as the actor ("Ledger now exposes…", "Midnight.js warns when…"). |
| Change descriptions | Past tense, plain verbs: "Added…", "Fixed…", "Renamed…", "Removed…", "Hardened…", "Exposed…". |
| Specificity | High. Name the API, the flag, the file, the version — in inline code. State the WHY for breaking changes. |
| Migration | Every breaking change carries a `**Migration**:` line with exact steps. |
| Sentence length | Varied to the material. No padding, no chopping for effect. |
| Spelling / mechanics | Match the surrounding midnight-docs notes (US spelling, e.g. "behavior", "serialization"). Do NOT impose Commonwealth spelling or closed em-dashes — those are personal-site rules and do not apply here. |
| Emoji | None. |

## Exemplars (drawn from the current notes)

**High-level summary (Ledger 8.1.0):**
Ledger 8.1.0 is a minor release that delivers storage layer improvements and enhanced wallet functionality. The release includes fixes to the `storage-core` subsystem addressing race conditions, deadlocks, and memory management, and exposes finer-grained control and event contents through WASM bindings for wallet developers.

**Summary-of-updates bullets (Midnight.js 4.1.1):**
- Renamed `IndexerFormattedError.cause` to `.errors` for ES2022 `Error.cause` compatibility.
- Applied full password policy to signing key and private state export operations.
- Added qanet support via NIGHT/DUST faucet flow in `testkit-js`.

**Breaking change with migration (Midnight.js 4.1.1):**
### Rename `IndexerFormattedError.cause` to `.errors`

The ES2022 `Error.cause` slot is contractually a single underlying error, not a collection. Shadowing it with an array of GraphQL errors broke Node's `util.inspect` causal chain, Sentry grouping, and structured loggers. This release renames the property to `.errors` to avoid the conflict.

**Migration**: Replace all references to `IndexerFormattedError.cause` with `.errors`.

**Bug fix (Ledger 8.1.0):**
### Race condition in `force_as_arc`

Fixed a race condition in `force_as_arc` that could cause deadlocks under concurrent access. This also resolves the lock ordering violation that could trigger the same deadlock from a different code path.

## Voice markers — actively use

- **Name the component as the actor.** "Ledger now exposes…", "The `indexer-public-data-provider` now uses structured error types."
- **Ground every claim.** Each bullet traces to a real PR, commit, or release-body line. If you cannot ground it, drop it — never invent a change.
- **State the WHY on breaking changes.** Explain the reason before the migration, as the exemplar does.
- **Inline code on every identifier.** API names, flags, package names, file names, version numbers.
- **Plain honesty in Known issues.** Either "No critical known issues exist at release time." or a factual list. Do not inflate or hide.

## Anti-voice — never produce

These patterns are banned in release-note prose. Rewrite any sentence containing them.

**Word choice:**
- Magic adverbs: "quietly", "deeply", "fundamentally", "remarkably", "seamlessly", "truly", "undeniably".
- Overused verbs: "delve", "leverage" (verb), "streamline", "harness" (verb), "facilitate", "foster", "empower", "navigate" (metaphorical), "unlock", "supercharge".
- Dodge verbs for "is": "serves as", "stands as", "represents", "underscores", "speaks volumes".
- Decorative nouns: "tapestry", "landscape", "paradigm", "synergy", "ecosystem" (decorative), "journey", "realm".
- AI-tell fillers: "it's worth noting", "importantly", "notably", "interestingly", "let's dive in", "here's the thing", "here's the kicker", "in the realm of", "in today's fast-paced world".
- Corporate: "move the needle", "low-hanging fruit", "best-in-class", "value proposition", "double down".
- Hype: "game-changing", "revolutionary", "groundbreaking", "next-level", "unprecedented", "powerful" (as filler), "incredible", "this changes everything".
- Setup labels: "The key insight:", "Here's what matters:", "The reality is:", "Simply put:", "In short:".
- Signposted conclusions: "In conclusion", "To sum up", "In summary", "As we've seen", "The bottom line".
- Stacking connectors: "Moreover", "Furthermore", "Additionally", "In addition", "What's more", "That being said".
- Textbook: "It is important to note", "It should be noted that", "As previously mentioned", "the aforementioned".
- Vague attribution: "experts argue", "research shows" (uncited), "studies have demonstrated".

**Structures:**
- Negative parallelism / reframe pivots: "It's not X, it's Y"; "not because X but because Y"; "The question isn't X. The question is Y."; "Not X. Not Y. Just Z." (A factual "never" guarantee — "the sync never silently fails" — is fine; only rhetorical reframes are banned.)
- Self-posed rhetorical question answered on the next line.
- Artificial rule-of-three ("faster, better, stronger"). Real factual counts ("three fixes", "four new APIs") are fine.
- Anaphora abuse (repeated identical sentence openings for effect).
- "-ing" tack-ons: "highlighting its importance", "reflecting broader trends", "underscoring the shift".
- Marketing closers: "Key Takeaways" panels, CTA closers ("Ready to upgrade?"), "What This Means For You".
- Manufactured urgency; grandiose stakes inflation; short punchy fragments as standalone paragraphs for emphasis.
- Exclamation marks. Zero.

## Internal checks (never output)

Silently, before delivering: scan for any banned phrase or structure above and rewrite it; confirm every breaking change has a `**Migration**:` line; confirm every claim is grounded in a real source; confirm inline code is on every identifier and version; confirm the spelling matches the surrounding US-spelling notes; confirm the tone reads cool and factual, not warm, hyped, or generated. Never add a verification section or mention these checks.
