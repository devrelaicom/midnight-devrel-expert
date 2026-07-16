---
name: docs-drift-methodology
description: Rubrics for the /update-drifted-docs pipeline — active-repo criteria, docs→repo reference rules, drift semantics, and the heuristic severity tiers. Read by the command and its dispatched mapping/claim agents.
---

# Docs-Drift Methodology

## Active repo (stage 1)
A `midnightntwrk` repo is included when ALL hold: not archived; not empty; default-branch
HEAD commit within the window (default 6 months); top-level tree is more than a README or
the standard scaffold set (`.envrc`, `.github`, `CHANGELOG.md`, `CODEOWNERS`,
`CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md`, `renovate.json`).
Always additionally include `LFDT-Minokawa/compact`.

## Mapping read-pass (stage 2, for dispatched agents)
For each page, record (a) Midnight technologies/tools it covers (human-readable names like
"Compact compiler (compactc)", "Midnight Node", "Indexer") and (b) specific
`midnightntwrk/*` repositories it references, as full GitHub URLs. Ignore `_`-prefixed files.
`build_map.py` turns these into `linked` (explicit URL, repo must exist in the repo list) and
`inferred` (component→repo rules).

## Drift semantics (stage 3)
A page is drifted when its last git-modified time predates the last-published time of any repo
it maps to. Last-published = latest release `published_at`, else default-branch HEAD
`committedDate`. Release-backed drift is higher confidence than push-backed.

## Severity tiers (post-classification)
Severity = blast radius if the claim is stale/wrong (NOT probability of being wrong).
- **high** — code-exact facts a developer copies verbatim. Two kinds:
  - *unconditional* (always high): type expressions, imports/packages, `pragma`, error/status codes, CLI flags, ZKIR opcodes, and named security primitives (persistentHash / transientHash / persistentCommit / transientCommit, `disclose(...)`).
  - *contextual* (high only when an inline code marker — a backtick span, call syntax, a snake_case/camelCase identifier, `@midnight-ntwrk`, or an opening generic like `<T` — co-occurs in the same claim): signatures / `returns`, keywords / operators, and bare security words (witness, nullifier, sealed, bare `disclose`, "publicly visible"). Without a code marker these fall through to medium/low.
  Wrong → build breaks or security impact.
- **medium** — specific behaviour of a named construct (has a code token but not a verbatim signature).
- **low** — conceptual/architectural prose with no code-exactness. A claim outside the four verified domains (compact/sdk/zkir/witness) also caps at low unless an unconditional-high signal fired.
