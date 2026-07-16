# midnight-relnotes

Detect stale Midnight release notes and generate on-voice release-note PRs from
inside a `midnight-docs` checkout.

## Commands

| Command | What it does |
|---|---|
| `/midnight-relnotes:check [items]` | Report stale notes; flag items >1 version behind; surface prereleases |
| `/midnight-relnotes:generate <spec>` | Author note(s) on a `relnote/*` worktree, one commit each, offer PR |
| `/midnight-relnotes:dashboard` | Exhaustive status dashboard (MD/HTML) under the plugin data dir |
| `/midnight-relnotes:doctor` | Quick tool/runtime sense check |

## Requirements

Authenticated `gh`, `git`, `node >=22`, `jq`, `python3`, `npm`, and a
`midnight-docs` checkout. Run `/midnight-relnotes:doctor` to verify.

## Notes

- "Latest published" means latest **stable** (npm dist-tags / non-prerelease GH release).
- A release note is two files: the `.mdx` and its `DynamicList<Item>.js` registration.
- All plugin artifacts live under the plugin data dir, never in the docs tree.
