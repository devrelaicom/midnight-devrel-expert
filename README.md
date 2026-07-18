# midnight-devrel-expert

A marketplace of [Claude Code plugins](https://docs.anthropic.com/en/docs/claude-code/plugins) for Midnight developer-relations and ecosystem maintenance — tools that keep the Midnight developer experience honest as the codebase moves underneath it.

## Plugins

| Plugin | What it does |
|---|---|
| [`midnight-docs-drift`](./plugins/midnight-docs-drift) | Detects `midnightntwrk/midnight-docs` pages that have drifted behind the repos they document, then drives an interactive extract → classify → severity-rank → verify → fix → PR pipeline over the stale claims (via `/update-drifted-docs`). |
| [`gha`](./plugins/gha) | Full-lifecycle GitHub Actions tooling: create workflows via a guided brainstorm, lint + security-review them, SHA-pin and maintain actions, run locally, and trigger/monitor runs on GitHub — all from Claude Code. |
| [`midnight-reports`](./plugins/midnight-reports) | Generates self-contained HTML pull-request activity reports for any GitHub repo (`/midnight-reports:pr <repo> [timeframe]`): metrics dashboard, action queue, and narrative commentary, published as an Artifact, with an optional paste-ready Slack summary. |
| [`midnight-tutorial-checker`](./plugins/midnight-tutorial-checker) | Walks a Midnight tutorial as a configurable reader persona, executes its verifiable steps against the real toolchain, and reports where — and for which kind of reader — the tutorial breaks down (`/midnight-tutorial-checker:check-tutorial <source>`), as an HTML report plus a chat summary. |

## Layout

```
.claude-plugin/marketplace.json   # marketplace manifest
plugins/<name>/                    # one self-contained plugin per directory
  .claude-plugin/plugin.json
  commands/  skills/  scripts/  tests/  README.md
docs/                              # design specs + implementation plans
```

## Install

Add the marketplace and install a plugin from inside Claude Code:

```
/plugin marketplace add devrelaicom/midnight-devrel-expert
/plugin install midnight-docs-drift@midnight-devrel-expert
/plugin install gha@midnight-devrel-expert
/plugin install midnight-tutorial-checker@midnight-devrel-expert
```

`midnight-docs-drift` soft-depends on the [`midnight-fact-check`](https://github.com/devrelaicom/midnight-expert) and [`midnight-verify`](https://github.com/devrelaicom/midnight-expert) plugins (from the `midnight-expert` marketplace) for claim extraction, classification, and verification, and expects `gh` authenticated with org read access.

## Adding Python tests to your plugin

CI runs one shared runner (`scripts/ci/run-python-tests.sh`) that discovers and runs Python
tests for every plugin. There is no per-plugin workflow to set up. To opt in:

1. Put importable code in `plugins/<name>/scripts/` as a package (add an empty `scripts/__init__.py`).
2. Put tests in `plugins/<name>/scripts/tests/` (with an empty `__init__.py`) or
   `plugins/<name>/tests/`, named `test_*.py`, importing your code via the `scripts` package
   (e.g. `import scripts.mymodule as m`).
3. That is all. The runner does `cd plugins/<name> && python3 -m pytest` for any plugin containing
   `test_*.py`, so `import scripts.*` resolves and each plugin's tests run isolated from siblings.

Run them all locally the same way CI does:

```
bash scripts/ci/run-python-tests.sh
```

## License

MIT — see [LICENSE](./LICENSE).
