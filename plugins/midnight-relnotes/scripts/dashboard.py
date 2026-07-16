"""Render an exhaustive relnote-status dashboard to Markdown and/or HTML."""
import json, os, argparse, html

COLS = ["Item", "Latest relnote", "Latest stable", "Behind", "Stale", "Prerelease"]

def _cells(r):
    # Untracked/ignored items (crates:* source, deprecated dirs) have no
    # meaningful stable/behind — label them rather than showing a misleading 0.
    if not r.get("tracked", True):
        label = r.get("tracked_label", "untracked")
        return [r["item"], r.get("latest_relnote") or "—", label, "—", label, r.get("prerelease") or "—"]
    return [r["item"], r.get("latest_relnote") or "—", r.get("latest_stable") or "—",
            str(r.get("behind", 0)), "yes" if r.get("stale") else "no", r.get("prerelease") or "—"]

def render_markdown(rows):
    out = ["# Release-note status", "", "| " + " | ".join(COLS) + " |",
           "|" + "|".join(["---"] * len(COLS)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(_cells(r)) + " |")
    return "\n".join(out) + "\n"

def render_html(rows):
    head = ("<!doctype html>\n<meta charset=utf-8>\n<title>Release-note status</title>\n"
            "<style>body{font-family:system-ui,sans-serif;margin:2rem}"
            "table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:.4rem .6rem}"
            ".stale{background:#fee}</style>\n<h1>Release-note status</h1>\n<table>\n<tr>"
            + "".join(f"<th>{c}</th>" for c in COLS) + "</tr>\n")
    body = ""
    for r in rows:
        cls = ' class="stale"' if r.get("tracked", True) and r.get("stale") else ""
        body += "<tr" + cls + ">" + "".join(f"<td>{html.escape(c)}</td>" for c in _cells(r)) + "</tr>\n"
    return head + body + "</table>\n"

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--format", choices=["md", "html", "both"], default="both")
    a = ap.parse_args(argv)
    rows = json.loads(a.rows)
    os.makedirs(a.out_dir, exist_ok=True)
    written = []
    if a.format in ("md", "both"):
        p = os.path.join(a.out_dir, "dashboard.md"); open(p, "w").write(render_markdown(rows)); written.append(p)
    if a.format in ("html", "both"):
        p = os.path.join(a.out_dir, "dashboard.html"); open(p, "w").write(render_html(rows)); written.append(p)
    print(json.dumps({"written": written}))

if __name__ == "__main__":
    main()
