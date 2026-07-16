# midnight-devrel-expert

A marketplace of [Claude Code plugins](https://docs.anthropic.com/en/docs/claude-code/plugins) for Midnight developer-relations and ecosystem maintenance — tools that keep the Midnight developer experience honest as the codebase moves underneath it.

## Plugins

| Plugin | What it does |
|---|---|
| [`midnight-docs-drift`](./plugins/midnight-docs-drift) | Detects `midnightntwrk/midnight-docs` pages that have drifted behind the repos they document, then drives an interactive extract → classify → severity-rank → verify → fix → PR pipeline over the stale claims (via `/update-drifted-docs`). |

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
```

`midnight-docs-drift` soft-depends on the [`midnight-fact-check`](https://github.com/devrelaicom/midnight-expert) and [`midnight-verify`](https://github.com/devrelaicom/midnight-expert) plugins (from the `midnight-expert` marketplace) for claim extraction, classification, and verification, and expects `gh` authenticated with org read access.

## License

MIT — see [LICENSE](./LICENSE).
