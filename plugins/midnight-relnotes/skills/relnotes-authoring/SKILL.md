---
name: relnotes-authoring
description: Load this skill when writing a Midnight release note file. It carries the current relnote structure (the eight standard sections), the filename convention, the frontmatter shape, and how to register a note in its DynamicList component. Use it alongside relnotes-writing (voice).
---

# relnotes Authoring

Structure, naming, and registration for a Midnight release note. Pair with
`relnotes-writing` for voice.

## The note is two files

1. The `.mdx` detail page under `docs/relnotes/<dir>/`.
2. An edit to `src/components/DynamicList<Item>.js` — see
   `references/dynamiclist-registration.md`. A note that skips the JS edit
   never shows in the docs UI.

## Structure

Follow `references/template-full.mdx` exactly. The eight standard sections,
in order: High-level summary, Audience, Summary of updates, New features,
Breaking changes, Bug fixes and quality improvements, Known issues, Links and
references. Annotated real examples of each are in `references/section-catalog.md`.

## Filename

See `references/filename-convention.md`. Derive it with
`python3 -c "from scripts import lib; print(lib.version_to_filename('<prefix>','<version>','<scheme>'))"`.

## Validate before committing

`python3 -m scripts.validate_relnote '<args-json>'` checks filename,
frontmatter, required sections, and that the version is registered in the
DynamicList component.
