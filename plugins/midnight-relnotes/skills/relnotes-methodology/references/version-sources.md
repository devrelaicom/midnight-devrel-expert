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
- `version_source: crates:<crate>` → resolves the crate's current version:
  1. **cargo/crates.io first** — `cargo search <crate>`, gated on `command -v
     cargo`. Midnight's internal crates are largely unpublished, so this often
     returns nothing (e.g. `midnight-proof-server`, the one live `crates:*` item,
     is not on crates.io) and the Cargo.toml fallback takes over.
  2. **Cargo.toml fallback** — reads `version` from `source_path/Cargo.toml` on
     the `source_ref` branch of `repo` via `gh api`, following `version.workspace
     = true` into the workspace root's `[workspace.package] version` (or the
     dotted `[workspace] package.version`). Works with cargo absent entirely.
  3. If neither yields a version → `{"tracked": false}`, exactly like `ignored`.
     The resolver **never errors and never fabricates** a version.
  A single resolved version is run through the same stable/prerelease split as
  npm/gh, so a crate sitting on a prerelease (e.g. workspace `8.2.0-rc.1`) surfaces
  as a prerelease with no stable — not as stale.
- `version_source: ignored` → returns `{"tracked": false}` with empty versions;
  no npm/gh/cargo call is made. Unrecognised sources are treated the same way —
  they never fall through to a GitHub-release lookup.

`all_stable` (ascending) feeds gap detection in `scripts.staleness`. The
newest prerelease feeds the prerelease radar in `check` and `dashboard`.
`tracked: false` rows are labelled `untracked`/`ignored`, never flagged stale.
