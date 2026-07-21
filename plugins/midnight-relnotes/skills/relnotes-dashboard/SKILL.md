---
name: relnotes-dashboard
description: Load this skill when running /midnight-relnotes:dashboard — it is the authoritative source for the dashboard's two HTML styles (basic and the baked "full" design), the always-write-to-disk timestamping rule, and the format/style/sharing decision tree (Claude Web artifacts, agentbin, mdtohtml). Pairs with relnotes-methodology (data) and relnotes-doctor (preflight).
---

# relnotes Dashboard

How the release-note status dashboard is rendered, styled, saved, and shared.
`relnotes-methodology` owns the *data* (manifest, staleness, version resolution);
this skill owns the *presentation and delivery*.

## Rendering

Build the rows JSON — one object per item —
`[{item, latest_relnote, latest_stable, behind, stale, prerelease}]`, adding
`tracked:false` + `tracked_label` (`untracked`/`ignored`) for items with no
version feed. Then, from `${CLAUDE_PLUGIN_ROOT}`:

```
python3 -m scripts.dashboard --rows '<rows-json>' \
  --out-dir ${CLAUDE_PLUGIN_DATA}/dashboards \
  --format <md|html|both> --style <basic|full>
```

`--style` applies to HTML only. Each HTML run also writes a body-only
`*.artifact.html` companion (inline `<style>` + content, no `<!doctype>/head/body`)
for the Claude Web path. The script prints `{"written":[...], "stamp":..., "style":...}`.

## Always write to disk, timestamped

Regardless of whether or where anything is shared, the generated files ALWAYS
land under `${CLAUDE_PLUGIN_DATA}/dashboards/` with a filesystem-safe UTC stamp:
`dashboard-YYYYMMDD-HHMMSS.md` / `.html` / `.artifact.html`. Never write dashboard
artifacts into the docs project tree. Report the full path(s) at the end.

## The two HTML styles

**basic** — the plain table, plus a row tint by staleness so the eye lands on
what needs a note: **1 version behind → yellow**, **more than 1 behind → red**.
Current, untracked, and ignored rows stay neutral. Both tints are defined for
light and dark (`prefers-color-scheme`), so the table stays legible either way.

**full** — a baked-in custom **neo-brutalist** status board (spec below): thick
black frames, hard offset shadows, the Midnight-brand palette, heavy type. Readability
and scannability come first; the structure serves the severity read, never buries it.

## Full-style design spec (authoritative)

This is the source of truth for the full design. `frontend-design` was used
**at authoring time** to derive it; `scripts/dashboard.py` bakes the CSS and
template so every run is deterministic — do not re-derive per run. If you change
the design, change it here and in the renderer together.

**Concept: a Midnight-branded neo-brutalist status board.** A deliberate,
high-contrast neubrutalist treatment — thick black frames, hard offset shadows (no
blur), flat solid colour blocks in the Midnight-brand palette, heavy uppercase
display type. Bold *structure*, **confident but considered** *colour*: branded and
lively, yet still a serious release-notes tool, not a toy. The one job is severity
reading instantly. Neo-brutalism is a *named, intentional* style, not a
generated-UI default — so its signatures (hard shadows, chunky borders, solid
colour blocks) are wanted here even though a generic page would treat them as tells.

**Palette — balanced Midnight (single committed *light* theme).** Midnight's
brand carries the identity, used with hierarchy: the electric blue `#0000fe`
(`--ifm-color-primary`) is the **"current"** state, and the lime `#cbff46` accents
the date chip, on a soft cool field. Alert states are **confident but not neon**
(crimson / gold). Bold *structure*, considered *colour* — branded, not a toy, and
not washed-out grey either.
- field `--desk #edf0f7`, panel `--paper #ffffff`, ink `--ink #141414`,
  muted text `--soft #5b616b`, brand `--brand #0000fe`, lime `--lime #cbff46`
- signals (WCAG-AA): needs-a-note `--crit #d43a3f` (crimson, white text),
  one-behind `--warn #efa72b` (gold, **black** text), current `--ok #0000fe`
  (Midnight blue, white text), not-tracked `--gone #5b6472` (slate, white text)
- the date chip is lime with black text; the footer sits on the field in `--soft`.
  Frame `3px solid --ink`; hard shadows `6px 6px 0 --ink` (blocks) /
  `2–3px … 0 --ink` (badges); radius `8px`. **Never** a blurred shadow.

**Type — two roles, brand faces named first.** The stacks name Midnight's brand
faces first — **Urbanist** (sans) and **Geist Mono** (mono) — then fall back to a
heavy system sans and `SF Mono`, so the page stays self-contained (the brand fonts
are a nod, not a dependency; they generally will not load in an artifact). Sans at
weight 800–900, uppercase, tight tracking for the masthead / group bars / labels;
mono for every version number, count, and badge.

**Layout — summary before detail.**
1. **Masthead block**: a heavy uppercase title (`RELEASE NOTES STATUS`), a black
   date pill, and a one-line lede (`N components tracked. X need a note now.`).
2. **Scoreboard**: four colour-blocks (crimson / gold / Midnight blue / slate),
   each a big mono count + label — the at-a-glance severity summary.
3. **Severity groups**: one framed block per severity, most-urgent first, with a
   colour-coded header bar (`Needs a note` / `One behind` / `Current` /
   `Not tracked`) carrying its count. Rows: component (with a `pre <version>`
   outline sticker when a prerelease is in flight), version (`noted → latest` when
   behind, plain latest when current), and a colour-coded status **badge**.
4. A mono footer with the generated UTC stamp.

**Signature — the colour-blocked scoreboard + badges.** Severity is a colour block
you read before any text: the scoreboard up top, the group header bars, and a
per-row badge whose **text always names the state** (`3 behind` / `1 behind` /
`current` / `not tracked` / `ignored`), so colour is never the only signal.

**Quality floor.** Bold but disciplined: **no gradients, no blur/glow, no
glassmorphism, no side/left accent stripe, no animation.** Every fill carries
readable text at WCAG-AA (white on the deep fills, black on gold); body ≥16px,
line-height 1.5, ≥16px container padding, tabular-nums, responsive to mobile.
Self-contained (inline CSS, no external assets).

**Guardrails** (keep passing all of these): hard **offset** shadows only, never
blurred/diffuse · thick **black structural** frames, never a one-sided colour
accent stripe · flat colour fills, **no gradients** · **confident, not neon**
alert tones (and not washed-out grey) · Midnight blue = "current", lime = a small
accent · status **colour + text**, never colour alone · AA-readable text on every
fill · two font families (heavy sans + mono; brand faces named first with a system
fallback) · plain copy (no buzzwords, no rhetorical-question hero).

### Precedence over `artifact-design`

When the full HTML is published as a **Claude Web artifact**, follow the
`artifact-design` skill's HTML guidance (self-contained, responsive, favicon,
theme mechanics) **except where it contradicts this spec — this dashboard skill
wins**. Concretely: keep the **single committed light neo-brutalist theme** (do
*not* add a dark variant or a dual-theme toggle, even though artifact-design
defaults to theme-aware), and keep this palette, the thick-frame/hard-shadow
treatment, the layout, and the colour-block severity encoding. Publish the
`*.artifact.html` fragment (body-only, already self-contained); pass a favicon
emoji (e.g. `🌒`).

## Sharing flow

**Default HTML share target is Claude Web artifacts.** Detect the optional tools
up front in one call — do NOT probe them individually with Bash:

```
${CLAUDE_PLUGIN_ROOT}/scripts/tool_probe.sh
# -> {"agentbin":true|false,"mdtohtml":true|false,"cargo":true|false}
```

Then ask the questions below with `AskUserQuestion`. You MAY consolidate them into
a single `AskUserQuestion` call (multiple questions) as long as the per-format
semantics are preserved.

1. **Format (always).** HTML, Markdown, or both? **If no response arrives within a
   reasonable window, default to both.**
2. **Style (only if HTML is being generated).** Basic or Full?
3. **HTML sharing** (only if HTML is being generated) — default target Claude Web:
   - `agentbin` available → **Claude Web / agentbin / neither**.
   - `agentbin` absent → **Claude Web / neither** (Claude Web is the default).
4. **Markdown sharing** (only if Markdown is being generated) — options depend on
   `mdtohtml` and `agentbin`:
   - both available → **Claude Web / agentbin / neither**.
   - only `agentbin` → **agentbin / neither**.
   - only `mdtohtml` → **Claude Web / neither**.
   - neither → **no share offered** (disk only).

### Executing each share choice

- **HTML → Claude Web**: publish the `*.artifact.html` fragment as an artifact
  (see the precedence note above; favicon `🌒`).
- **HTML → agentbin**: upload the standalone `*.html`; return the URL.
- **Markdown → Claude Web**: convert the `.md` to HTML with `mdtohtml` **first**,
  then publish that HTML as the artifact.
- **Markdown → agentbin**: upload the **raw `.md`** directly — agentbin renders
  Markdown automatically; do **not** pre-convert with `mdtohtml`.
- **neither**: nothing is uploaded; the on-disk paths are the deliverable.

When both formats were generated, the HTML and Markdown share prompts are
independent per the rules above. Whatever the choices, the timestamped files are
already on disk — always report their full paths.
