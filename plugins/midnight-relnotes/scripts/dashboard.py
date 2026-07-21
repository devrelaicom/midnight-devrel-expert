"""Render an exhaustive relnote-status dashboard to Markdown and/or HTML.

Two HTML styles:
  * basic  — the plain table, with row tints by staleness (1 behind -> yellow,
             >1 behind -> red; current/untracked/ignored stay neutral). Legible
             in light and dark.
  * full   — a baked-in custom neo-brutalist status board in the Midnight-brand
             palette: thick black frames, hard offset shadows, heavy type. Brand
             identity is carried by the electric blue #0000fe ("current") and the
             lime #cbff46 date chip, on a soft cool field; alert states are
             confident but not neon (crimson / gold). Severity reads first
             (colour-blocked scoreboard, colour-coded group blocks, per-row status
             badges that carry their own text). No gradients, no blur/glow, no
             side stripe. Single committed light theme, self-contained (inline
             CSS, no external assets). The design spec is authoritative in the
             relnotes-dashboard skill; this renderer bakes it so runs are
             deterministic.
"""
import json, os, argparse, html, re
from collections import Counter
from . import lib

COLS = ["Item", "Latest relnote", "Latest stable", "Behind", "Stale", "Prerelease"]

# ---- shared row classification ------------------------------------------
def _tracked(r):
    return r.get("tracked", True)

def _behind(r):
    return r.get("behind", 0) or 0

def _severity(r):
    """crit (>1 behind) | warn (1 behind) | current (0 behind) | untracked."""
    if not _tracked(r):
        return "untracked"
    b = _behind(r)
    if b > 1:
        return "crit"
    if b == 1:
        return "warn"
    return "current"

# Severity → group. Groups are ordered most-urgent first; the group header
# carries the count. _COLOR maps a severity to its neo-brutalist colour class
# (shared by the scoreboard blocks, group bars, and per-row badges).
_GROUPS = [("crit", "Needs a note"), ("warn", "One behind"),
           ("current", "Current"), ("untracked", "Not tracked")]
_COLOR = {"crit": "crit", "warn": "warn", "current": "ok", "untracked": "gone"}

def _cells(r):
    # Untracked/ignored items (crates:* that did not resolve, deprecated dirs)
    # have no meaningful stable/behind — label them rather than show a misleading 0.
    if not _tracked(r):
        label = r.get("tracked_label", "untracked")
        return [r["item"], r.get("latest_relnote") or "—", label, "—", label, r.get("prerelease") or "—"]
    return [r["item"], r.get("latest_relnote") or "—", r.get("latest_stable") or "—",
            str(_behind(r)), "yes" if r.get("stale") else "no", r.get("prerelease") or "—"]

# ---- Markdown -----------------------------------------------------------
def render_markdown(rows):
    out = ["# Release-note status", "", "| " + " | ".join(COLS) + " |",
           "|" + "|".join(["---"] * len(COLS)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(_cells(r)) + " |")
    return "\n".join(out) + "\n"

# ---- HTML: basic --------------------------------------------------------
_BASIC_STYLE = """<style>
:root{color-scheme:light dark}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:2rem;color:#14151a;background:#fff}
h1{font-size:1.4rem;margin:0 0 1rem}
table{border-collapse:collapse;font-size:.95rem}
td,th{border:1px solid rgba(128,128,128,.35);padding:.4rem .65rem;text-align:left}
th{background:rgba(128,128,128,.12)}
/* Row tints by staleness. 1 behind -> yellow, >1 behind -> red. */
tr.warn td{background:#fdeeb8}
tr.crit td{background:#f7c9cd}
@media (prefers-color-scheme:dark){
  body{color:#e6e8ef;background:#14151a}
  th{background:rgba(200,205,225,.10)}
  tr.warn td{background:#4d3f0e}
  tr.crit td{background:#4d1a20}
}
</style>"""

def _basic_content(rows):
    parts = ["<h1>Release-note status</h1>", "<table>",
             "<tr>" + "".join(f"<th>{c}</th>" for c in COLS) + "</tr>"]
    for r in rows:
        sev = _severity(r)
        cls = f' class="{sev}"' if sev in ("warn", "crit") else ""
        parts.append("<tr" + cls + ">" + "".join(f"<td>{html.escape(c)}</td>" for c in _cells(r)) + "</tr>")
    parts.append("</table>")
    return "\n".join(parts)

# ---- HTML: full (baked neo-brutalist status board) ----------------------
# A deliberate neo-brutalist treatment (requested): thick black frames, hard
# offset shadows (no blur), flat solid colour blocks in the Midnight-brand
# palette (electric blue = "current", lime accent, confident crimson/gold alerts),
# heavy type. Severity still reads first — a colour-blocked scoreboard, colour-
# coded group blocks, and per-row badges that each carry their own text (colour
# is never the only signal). No gradients, no blur/glow, no glassmorphism, no
# side stripe. Every fill carries AA-readable text (white on deep, black on gold).
_FULL_STYLE = """<style>
:root{
  /* Midnight Network, balanced: brand identity carried by Midnight's electric
     blue (#0000fe, from --ifm-color-primary) for the "current" state and the
     lime accent (#cbff46) on the date chip, on a soft cool field. Alert states
     are confident but not neon (crimson / gold). White text on the deep fills,
     black on gold. Brand faces named first (Urbanist / Geist Mono), system fallback. */
  --brand:#0000fe; --lime:#cbff46; --desk:#edf0f7; --paper:#ffffff; --ink:#141414; --soft:#5b616b;
  --crit:#d43a3f; --warn:#efa72b; --ok:#0000fe; --gone:#5b6472;
  --bd:3px solid var(--ink); --sh:6px 6px 0 var(--ink); --sh-sm:3px 3px 0 var(--ink); --r:8px;
  --sans:"Urbanist",system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:"Geist Mono","SF Mono",ui-monospace,"JetBrains Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--desk);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased}
.page{max-width:880px;margin:0 auto;padding:2.2rem 1.25rem 3rem}
/* Masthead block */
.masthead{background:var(--paper);border:var(--bd);border-radius:var(--r);box-shadow:var(--sh);padding:1.5rem 1.6rem}
.mast-top{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap}
.title{margin:0;font-size:clamp(1.9rem,6vw,3rem);font-weight:900;line-height:.95;
  letter-spacing:-.02em;text-transform:uppercase}
.stamp{font-family:var(--mono);font-size:.78rem;font-weight:700;background:var(--lime);color:var(--ink);
  border:2px solid var(--ink);padding:.4rem .55rem;border-radius:5px;white-space:nowrap}
.lede{margin:.9rem 0 0;font-size:1.05rem;font-weight:600}
/* Scoreboard — bold colour-blocked severity counts (the at-a-glance summary) */
.scoreboard{display:grid;grid-template-columns:repeat(4,1fr);gap:.85rem;margin-top:1.35rem}
.score{border:var(--bd);border-radius:6px;box-shadow:var(--sh-sm);padding:.7rem .8rem;color:var(--paper)}
.score b{display:block;font-family:var(--mono);font-size:2.1rem;font-weight:800;line-height:1;font-variant-numeric:tabular-nums}
.score span{display:block;margin-top:.3rem;font-size:.66rem;font-weight:800;letter-spacing:.03em;text-transform:uppercase}
.score.crit{background:var(--crit)} .score.warn{background:var(--warn)}
.score.ok{background:var(--ok)} .score.gone{background:var(--gone)}
/* Severity groups — each a framed block with a colour-coded header bar */
.group{margin-top:1.6rem;background:var(--paper);border:var(--bd);border-radius:var(--r);
  box-shadow:var(--sh);overflow:hidden}
.gbar{display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.6rem 1rem;
  border-bottom:var(--bd);color:var(--paper);font-weight:900;text-transform:uppercase;letter-spacing:.02em;font-size:.95rem}
.gbar .n{font-family:var(--mono);font-weight:800}
.gbar.crit{background:var(--crit)} .gbar.warn{background:var(--warn)}
.gbar.ok{background:var(--ok)} .gbar.gone{background:var(--gone)}
/* gold "one behind" fill wants black text (AA); the rest carry white */
.score.warn,.gbar.warn,.badge.warn{color:var(--ink)}
.row{display:grid;grid-template-columns:1fr auto;align-items:center;gap:.4rem 1rem;
  padding:.75rem 1rem;border-bottom:2px solid var(--ink)}
.row:last-child{border-bottom:0}
.cmp{font-weight:800;font-size:1.02rem}
.pre{display:inline-block;font-family:var(--mono);font-size:.68rem;font-weight:700;text-transform:uppercase;
  border:2px solid var(--ink);border-radius:4px;padding:.02rem .3rem;margin-left:.45rem;vertical-align:middle}
.ver{margin-top:.2rem;font-family:var(--mono);font-size:.85rem;font-weight:600}
.ver .arw{padding:0 .15rem}
.ver .to{font-weight:800}
.badge{justify-self:end;font-family:var(--mono);font-weight:800;font-size:.74rem;text-transform:uppercase;
  color:var(--paper);border:2px solid var(--ink);border-radius:5px;box-shadow:2px 2px 0 var(--ink);
  padding:.32rem .55rem;white-space:nowrap}
.badge.crit{background:var(--crit)} .badge.warn{background:var(--warn)}
.badge.ok{background:var(--ok)} .badge.gone{background:var(--gone)}
.foot{margin-top:1.7rem;font-family:var(--mono);font-size:.78rem;font-weight:700;color:var(--soft)}
@media (max-width:620px){
  .scoreboard{grid-template-columns:repeat(2,1fr)}
  .row{grid-template-columns:1fr}
  .badge{justify-self:start;margin-top:.35rem}
}
</style>"""

def _full_row(r):
    esc = html.escape
    sev = _severity(r)
    pre = r.get("prerelease")
    pre_html = f'<span class="pre">pre {esc(pre)}</span>' if pre else ""
    if not _tracked(r):
        ver = f'last noted {esc(r.get("latest_relnote") or "—")}'
        lbl = r.get("tracked_label") or "untracked"
        word = "not tracked" if lbl == "untracked" else lbl
    elif _behind(r) > 0:
        ver = (f'{esc(r.get("latest_relnote") or "—")}'
               f'<span class="arw">&rarr;</span><span class="to">{esc(r.get("latest_stable") or "—")}</span>')
        b = _behind(r)
        word = "1 behind" if b == 1 else f"{b} behind"
    else:
        ver = f'<span class="to">{esc(r.get("latest_stable") or r.get("latest_relnote") or "—")}</span>'
        word = "current"
    return (f'<div class="row">'
            f'<div><span class="cmp">{esc(str(r.get("item", "—")))}</span>{pre_html}'
            f'<div class="ver">{ver}</div></div>'
            f'<span class="badge {_COLOR[sev]}">{esc(word)}</span>'
            f'</div>')

def _fmt_stamp(stamp):
    """`20260721-162954` -> ('2026-07-21', 'Generated 2026-07-21 16:29 UTC')."""
    if not stamp:
        return (None, None)
    m = re.match(r"(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})\d{2}$", stamp)
    if not m:
        return (stamp, f"Generated {stamp}")
    y, mo, d, h, mi = m.groups()
    return (f"{y}-{mo}-{d}", f"Generated {y}-{mo}-{d} {h}:{mi} UTC")

def _lede(s):
    total = s["total"]
    if not total:
        return "No components tracked."
    if s["crit"]:
        n = s["crit"]
        tail = f'{n} need{"s" if n == 1 else ""} a note now.'
    elif s["warn"]:
        n = s["warn"]
        tail = f'{n} {"is" if n == 1 else "are"} one version behind.'
    else:
        tail = "all caught up."
    return f'{total} components tracked. {tail}'

def _full_content(rows, stamp=None):
    esc = html.escape
    buckets = {sev: [] for sev, _ in _GROUPS}
    for r in rows:
        buckets[_severity(r)].append(r)
    buckets["crit"].sort(key=lambda r: (-_behind(r), str(r.get("item", ""))))
    for k in ("warn", "current", "untracked"):
        buckets[k].sort(key=lambda r: str(r.get("item", "")))
    groups = []
    for sev, label in _GROUPS:
        g = buckets[sev]
        if not g:
            continue
        groups.append(
            f'<section class="group">'
            f'<div class="gbar {_COLOR[sev]}"><span>{label}</span><span class="n">{len(g)}</span></div>'
            + "".join(_full_row(r) for r in g) + '</section>')
    s = _summary(rows)
    date_str, foot = _fmt_stamp(stamp)
    scoreboard = "".join(
        f'<div class="score {cc}"><b>{s[key]}</b><span>{lbl}</span></div>'
        for key, cc, lbl in (("crit", "crit", "Needs a note"), ("warn", "warn", "One behind"),
                             ("current", "ok", "Current"), ("untracked", "gone", "Not tracked")))
    stamp_html = f'<div class="stamp">{esc(date_str)}</div>' if date_str else ""
    footer = esc(foot) if foot else esc(f"{s['total']} components tracked")
    return (
        '<div class="page">'
        '<header class="masthead">'
        f'<div class="mast-top"><h1 class="title">Release notes status</h1>{stamp_html}</div>'
        f'<p class="lede">{esc(_lede(s))}</p>'
        f'<div class="scoreboard">{scoreboard}</div>'
        '</header>'
        + "".join(groups) +
        f'<footer class="foot">{footer}</footer>'
        '</div>')

def _summary(rows):
    sev = Counter(_severity(r) for r in rows)
    return {"total": len(rows), "crit": sev["crit"], "warn": sev["warn"],
            "current": sev["current"], "untracked": sev["untracked"],
            "pre": sum(1 for r in rows if r.get("prerelease"))}

# ---- HTML assembly ------------------------------------------------------
_FAVICON = ('<link rel="icon" href="data:image/svg+xml,'
            "<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22>"
            "<text y=%22.9em%22 font-size=%2290%22>%F0%9F%8C%92</text></svg>\">")

def _style(style):
    return _FULL_STYLE if style == "full" else _BASIC_STYLE

def _content(rows, style, stamp=None):
    return _full_content(rows, stamp) if style == "full" else _basic_content(rows)

def render_html(rows, style="basic", stamp=None):
    """Complete, self-contained HTML document (what lands on disk / agentbin)."""
    return ("<!doctype html>\n<html lang=en>\n<head>\n<meta charset=utf-8>\n"
            '<meta name=viewport content="width=device-width,initial-scale=1">\n'
            "<title>Release-note status</title>\n" + _FAVICON + "\n"
            + _style(style) + "\n</head>\n<body>\n"
            + _content(rows, style, stamp) + "\n</body>\n</html>\n")

def render_html_fragment(rows, style="basic", stamp=None):
    """Body-only fragment (inline <style> + content, no doctype/head/body) for
    publishing as a Claude Web artifact — the artifact runtime supplies the
    document skeleton. Still fully self-contained: inline CSS, no external assets."""
    return _style(style) + "\n" + _content(rows, style, stamp) + "\n"

# ---- thin I/O shell -----------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--format", choices=["md", "html", "both"], default="both")
    ap.add_argument("--style", choices=["basic", "full"], default="basic",
                    help="HTML style; ignored for markdown")
    ap.add_argument("--stamp", default=None, help="override UTC stamp (mainly for tests)")
    a = ap.parse_args(argv)
    rows = json.loads(a.rows)
    os.makedirs(a.out_dir, exist_ok=True)
    stamp = a.stamp or lib.stamp_utc()  # filesystem-safe UTC: YYYYMMDD-HHMMSS
    written = []
    if a.format in ("md", "both"):
        p = os.path.join(a.out_dir, f"dashboard-{stamp}.md")
        with open(p, "w") as fh:
            fh.write(render_markdown(rows))
        written.append(p)
    if a.format in ("html", "both"):
        p = os.path.join(a.out_dir, f"dashboard-{stamp}.html")
        with open(p, "w") as fh:
            fh.write(render_html(rows, a.style, stamp))
        written.append(p)
        # Body-only companion for Claude Web artifact publishing (no wrapper).
        pa = os.path.join(a.out_dir, f"dashboard-{stamp}.artifact.html")
        with open(pa, "w") as fh:
            fh.write(render_html_fragment(rows, a.style, stamp))
        written.append(pa)
    print(json.dumps({"written": written, "stamp": stamp, "style": a.style}))

if __name__ == "__main__":
    main()
