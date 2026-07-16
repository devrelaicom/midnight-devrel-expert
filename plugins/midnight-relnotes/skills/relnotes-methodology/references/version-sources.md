# Resolving the latest stable published version

"Latest published" means latest **stable**, never the raw newest tag. New
GitHub releases are frequently prereleases (`-alpha`/`-beta`/`-rc`/`-pre`);
those never count as the current version.

Run `python3 -m scripts.latest_release '<item-json>'` — it returns
`{"stable", "prerelease", "all_stable", "tracked"}`. Under the hood:

- `version_source: npm:<pkg>` → `npm view <pkg> versions --json`; prereleases
  are detected by a `-` suffix and excluded from `stable`/`all_stable`. The
  npm `dist-tags.latest` is the stable pointer.
- `version_source: gh-release` → `gh release list --json tagName,isPrerelease,publishedAt`;
  a non-empty `tag_prefix` both **filters** the tag list to that stream (a
  monorepo like `midnightntwrk/compact` ships both `compact-v*` and
  `compactc-v*`, plus dev tags — the wrong stream must not leak in) and is then
  stripped. `isPrerelease=true` entries are excluded from stable.
- `version_source: crates:<crate>` or `ignored` → returns `{"tracked": false}`
  with empty versions; no npm/gh call is made. `crates:*` records where the
  crate lives (`repo` + `source_path` + `source_ref`) for a future resolver;
  today its staleness is not computed. Unrecognised sources are treated the same
  way — they never fall through to a GitHub-release lookup.

`all_stable` (ascending) feeds gap detection in `scripts.staleness`. The
newest prerelease feeds the prerelease radar in `check` and `dashboard`.
`tracked: false` rows are labelled `untracked`/`ignored`, never flagged stale.
