# Resolving the latest stable published version

"Latest published" means latest **stable**, never the raw newest tag. New
GitHub releases are frequently prereleases (`-alpha`/`-beta`/`-rc`/`-pre`);
those never count as the current version.

Run `python3 -m scripts.latest_release '<item-json>'` — it returns
`{"stable", "prerelease", "all_stable"}`. Under the hood:

- `version_source: npm:<pkg>` → `npm view <pkg> versions --json`; prereleases
  are detected by a `-` suffix and excluded from `stable`/`all_stable`. The
  npm `dist-tags.latest` is the stable pointer.
- `version_source: gh-release` → `gh release list --json tagName,isPrerelease,publishedAt`;
  `tag_prefix` is stripped; `isPrerelease=true` entries are excluded from stable.

`all_stable` (ascending) feeds gap detection in `scripts.staleness`. The
newest prerelease feeds the prerelease radar in `check` and `dashboard`.
