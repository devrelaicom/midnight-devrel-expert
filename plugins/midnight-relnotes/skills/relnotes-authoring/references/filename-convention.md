# Filename convention

`docs/relnotes/<dir>/<file_prefix>-<version>.mdx`

- **dash scheme** (most items): dots become dashes.
  `midnight-js` + `4.1.1` → `midnight-js-4-1-1.mdx`.
- **dotted scheme** (compact toolchain): dots kept.
  `toolchain` + `0.31.0` → `toolchain-0.31.0.mdx`.

`file_prefix` is not always the dir name — the `compact` dir holds
`toolchain-*`, `compact-*`, and `minokawa-*`. Take `file_prefix` from the
manifest. Derive the exact name with `scripts.lib.version_to_filename`.
