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
- **high** — code-exact facts a developer copies verbatim: signatures, type expressions,
  imports/packages, keywords/operators/pragma, error/status codes, CLI flags, ZKIR opcodes,
  security primitives. Wrong → build breaks or security impact.
- **medium** — specific behaviour of a named construct, not a verbatim signature.
- **low** — conceptual/architectural prose with no code-exactness.
