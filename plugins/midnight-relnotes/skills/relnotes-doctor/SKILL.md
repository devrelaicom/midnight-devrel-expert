---
name: relnotes-doctor
description: This skill should be used when the user asks to "check my relnotes tooling", "run relnotes doctor", or when another midnight-relnotes command needs a fast preflight before running. Checks for authenticated gh, git, node >=22, jq, python3, npm, and that the cwd is a midnight-docs checkout. Reports gaps with install hints. Never installs anything. For a full environment check, point the user at midnight-expert's doctor.
---

# relnotes Doctor

Quick sense check for the tools and runtime `midnight-relnotes` needs. Never
installs anything — only reports gaps and the command the user would run.

## Running the check

Run `${CLAUDE_PLUGIN_ROOT}/scripts/doctor.sh` via Bash. Relay its summary
lines directly. If every line is `OK`, say so plainly. If anything is
`MISSING`, list exactly which and the install hint printed, then stop — do
not install anything, and do not offer to.

## What it checks

| Check | Why |
|---|---|
| `git` | Worktrees, branches, commits |
| `gh` (authenticated) | Release/PR/commit lookups and PR creation |
| `node` >=22 | The relnotes' own Node.js floor |
| `jq` | JSON parsing in the shells |
| `python3` | The deterministic cores |
| `npm` | npm dist-tag/version lookups |
| `cargo` (optional) | crates.io lookups for `crates:*` items; absence is fine — the Cargo.toml fallback covers it, so this never fails the run |
| docs-checkout | Commands must run from inside a `midnight-docs` clone |

## Scope

This is a fast preflight, nothing more. For a full Midnight environment
audit, direct the user to the `midnight-expert` plugin's doctor command.
