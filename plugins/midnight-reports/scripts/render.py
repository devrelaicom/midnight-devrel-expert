"""Pure HTML rendering: facts (report-data) + model prose (narrative) -> HTML.

render_report replaces every <!--MARKER--> in the template. The model's CI-noise
judgment enters via narrative['noise_checks'] and narrative['real_ci_blocked'].
"""
import html

_MARKERS = ["META", "LEDE", "KPIS", "METERS", "DISTRO", "THEMES",
            "OBSERVATIONS", "QUEUE", "TABLE", "WATCH", "FOOT"]
_REVIEW = {"APPROVED": ("good", "approved"), "CHANGES_REQUESTED": ("warn", "changes requested"),
           "REVIEW_REQUIRED": ("accent", "review required"), "NONE": ("", "no review")}
_REVIEW_SHORT = {"APPROVED": ("good", "approved"), "CHANGES_REQUESTED": ("warn", "changes req."),
                 "REVIEW_REQUIRED": ("accent", "review req."), "NONE": ("", "—")}
_QCLASS = {1: "p-merge", 2: "p-ci", 3: "p-review", 4: "p-author", 5: "p-bot"}

def esc(s):
    return html.escape("" if s is None else str(s), quote=True)

def _chip(cls, text):
    c = (" " + cls) if cls else ""
    return '<span class="chip%s">%s</span>' % (c, esc(text))

def _open(data):
    return [p for p in data["prs"] if p["state"] == "OPEN"]

def _real_fails(pr, noise):
    return [c for c in pr["failingChecks"] if c["conclusion"] != "PENDING" and c["name"] not in noise]

def _pending(pr):
    return [c for c in pr["failingChecks"] if c["conclusion"] == "PENDING"]

def render_meta(meta):
    gen = meta["generatedAt"][:10]
    return ('<div>Repo <strong>%s</strong></div>'
            '<div>Window <strong>%s → %s</strong></div>'
            '<div>Generated <strong>%s</strong></div>'
            '<button class="theme-toggle" id="themeBtn">◐ Toggle theme</button>'
            % (esc(meta["repo"]), esc(meta["since"]), esc(gen), esc(gen)))

def render_lede(narrative):
    summ = narrative.get("executive_summary") or []
    if isinstance(summ, str):
        summ = [summ]
    paras = "".join("<p>%s</p>" % esc(p) for p in summ)
    return ('<div class="eyebrow">The window in review</div>%s' % paras)

def render_kpis(data):
    t = data["meta"]["totals"]
    resolved = t["merged"] + t["closed"]
    rate = round(t["merged"] / resolved * 100) if resolved else 0
    open_h = len([p for p in _open(data) if p["authorType"] == "human"])
    open_b = t["open"] - open_h
    needs = len([p for p in _open(data) if str(p["blockedOn"]).startswith("maintainer")])
    tiles = [("Open", t["open"], "var(--good)", "<b>%d</b> human · <b>%d</b> bot" % (open_h, open_b)),
             ("Merged", t["merged"], "var(--accent)", "%d%% of resolved PRs landed" % rate),
             ("Closed unmerged", t["closed"], "var(--ink-3)", "superseded / duplicates"),
             ("Needs a maintainer", needs, "var(--warning)", "review, merge or triage")]
    return "\n".join(
        '<div class="tile"><span class="stripe" style="background:%s"></span>'
        '<div class="k-label">%s</div><div class="k-num">%d</div>'
        '<div class="k-sub">%s</div></div>' % (stripe, esc(label), num, sub)
        for label, num, stripe, sub in tiles)

def render_meters(data, narrative):
    o = _open(data)
    approved = len([p for p in o if p["reviewDecision"] == "APPROVED"])
    review_req = len([p for p in o if p["reviewDecision"] == "REVIEW_REQUIRED"])
    changes = len([p for p in o if p["reviewDecision"] == "CHANGES_REQUESTED"])
    real_blocked = len(narrative.get("real_ci_blocked") or [])
    rows = [(approved, "Approved · ready to merge", "var(--good)"),
            (review_req, "Awaiting first review", "var(--accent)"),
            (changes, "Changes requested", "var(--warning)"),
            (real_blocked, "CI blocked (real)", "var(--critical)")]
    return "\n".join(
        '<div class="meter"><span class="dot" style="background:%s"></span>'
        '<div><div class="m-num">%d</div><div class="m-label">%s</div></div></div>'
        % (c, n, esc(l)) for n, l, c in rows)

def render_distro(data):
    t = data["meta"]["totals"]
    total = t["total"] or 1
    segs = [("Merged", t["merged"], "var(--accent)"), ("Open", t["open"], "var(--good)"),
            ("Closed", t["closed"], "var(--ink-3)")]
    bar = "".join(
        '<div class="seg" style="flex:%s;background:%s" title="%s: %d">%s</div>'
        % (n or 0.001, c, esc(l), n, (n if n else "")) for l, n, c in segs)
    leg = "".join(
        '<span><i style="background:%s"></i>%s — <b class="mono">%d</b> (%d%%)</span>'
        % (c, esc(l), n, round(n / total * 100)) for l, n, c in segs)
    return '<div class="bar">%s</div><div class="legend">%s</div>' % (bar, leg)

def render_themes(narrative):
    out = []
    for th in narrative.get("themes") or []:
        prs = "".join('<a class="prref">#%d</a>' % n for n in th.get("prs") or [])
        out.append('<div class="theme"><div class="t-hd"><span class="t-name">%s</span>'
                   '<span class="t-count">%s PRs</span></div><p>%s</p>'
                   '<div class="t-prs">%s</div></div>'
                   % (esc(th["name"]), esc(th.get("count", "")), esc(th.get("blurb", "")), prs))
    return "\n".join(out)

def render_observations(narrative):
    out = []
    for ob in narrative.get("observations") or []:
        kind = ob.get("kind", "note")
        meta = " ".join("#%d" % n for n in ob.get("meta_prs") or [])
        out.append('<div class="insight %s"><span class="i-tag">%s</span>'
                   '<h3>%s</h3><p>%s</p><div class="i-meta">%s</div></div>'
                   % (esc(kind), esc(ob.get("tag", "")), esc(ob.get("title", "")),
                      ob.get("body_html", ""), esc(meta)))
    return "\n".join(out)

def _ci_chip_full(pr, noise):
    real = _real_fails(pr, noise)
    pend = _pending(pr)
    if real:
        return _chip("crit", "CI: " + ", ".join(c["name"] for c in real))
    if pend:
        return _chip("warn", "CI pending: " + ", ".join(c["name"] for c in pend))
    return _chip("good", "CI green")

def render_queue(data, narrative):
    noise = set(narrative.get("noise_checks") or [])
    out = []
    for p in sorted(_open(data), key=lambda x: x["priority"]):
        cls = _QCLASS.get(p["priority"], "p-review")
        rc, rt = _REVIEW.get(p["reviewDecision"], ("", ""))
        author = ("\U0001f916 " if p["authorType"] == "bot" else "") + p["author"]
        foot = (_chip("", author) + _chip(rc, rt) + _ci_chip_full(p, noise)
                + _chip("", "blocked on: " + str(p["blockedOn"]))
                + _chip("", "age %dd · idle %dd" % (p["ageDays"], p["idleDays"])))
        out.append('<div class="qcard %s"><div class="q-top">'
                   '<span class="q-num"><a href="%s" target="_blank" rel="noopener">#%d</a></span>'
                   '<span class="q-action">%s</span></div>'
                   '<div class="q-title"><a href="%s" target="_blank" rel="noopener">%s</a></div>'
                   '<div class="q-foot">%s</div></div>'
                   % (cls, esc(p["url"]), p["number"], esc(p["action"]),
                      esc(p["url"]), esc(p["title"]), foot))
    return "\n".join(out)

def render_table(data, narrative):
    noise = set(narrative.get("noise_checks") or [])
    dash = '<span style="color:var(--ink-3)">—</span>'
    rows = []
    for p in data["prs"]:
        real = _real_fails(p, noise)
        pend = _pending(p)
        if real:
            ci = _chip("crit", "fail")
        elif pend:
            ci = _chip("warn", "pending")
        elif p["ciStatusRaw"] == "passing" or p["failingChecks"]:
            ci = _chip("good", "green")
        else:
            ci = _chip("", "—")
        vnote = ""
        if p["state"] == "OPEN" and any(c["name"] in noise for c in p["failingChecks"]):
            vnote = (' <span title="systemic check failing repo-wide (noise)"'
                     ' style="color:var(--ink-3)">Ⓥ</span>')
        rc, rt = _REVIEW_SHORT.get(p["reviewDecision"], ("", "—"))
        text = esc(("%d %s %s" % (p["number"], p["title"], p["author"])).lower())
        draft = " · draft" if p["isDraft"] else ""
        botspan = ' <span class="bot">bot</span>' if p["authorType"] == "bot" else ""
        files = "%d file%s" % (p["changedFiles"], "" if p["changedFiles"] == 1 else "s")
        review_cell = _chip(rc, rt) if p["state"] == "OPEN" else dash
        ci_cell = (ci + vnote) if p["state"] == "OPEN" else dash
        rows.append(
            '<tr data-state="%s" data-author="%s" data-text="%s">'
            '<td class="c-num"><a href="%s" target="_blank" rel="noopener">#%d</a></td>'
            '<td class="c-title"><div class="t-main">%s</div>'
            '<div class="t-sub">%s · %s</div></td>'
            '<td class="c-author">%s%s</td>'
            '<td><span class="state-pill s-%s"><span class="sq"></span>%s%s</span></td>'
            '<td>%s</td><td>%s</td>'
            '<td class="num"><span class="diff-add">+%d</span> <span class="diff-del">−%d</span></td>'
            '<td class="num">%dd / %dd</td>'
            '<td class="num">%d\U0001f4ac %d✓</td></tr>'
            % (p["state"], p["authorType"], text, esc(p["url"]), p["number"],
               esc(p["title"]), esc(p["baseRefName"]), files, esc(p["author"]), botspan,
               p["state"], p["state"].lower(), draft, review_cell, ci_cell,
               p["additions"], p["deletions"], p["ageDays"], p["idleDays"],
               p["humanComments"], len(p["reviews"])))
    return "\n".join(rows)

def render_watch(narrative):
    out = []
    for w in narrative.get("watch_items") or []:
        out.append('<div class="witem %s"><div class="w-sev"></div><div class="w-body">'
                   '<div class="w-title">%s</div><div class="w-desc">%s</div></div></div>'
                   % (esc(w.get("severity", "info")), esc(w.get("title", "")), w.get("desc_html", "")))
    return "\n".join(out)

def render_foot(data):
    t = data["meta"]["totals"]
    return ('%d PRs · %d open · %d merged · %d closed'
            % (t["total"], t["open"], t["merged"], t["closed"]))

def render_report(template, data, narrative):
    frag = {
        "META": render_meta(data["meta"]), "LEDE": render_lede(narrative),
        "KPIS": render_kpis(data), "METERS": render_meters(data, narrative),
        "DISTRO": render_distro(data), "THEMES": render_themes(narrative),
        "OBSERVATIONS": render_observations(narrative), "QUEUE": render_queue(data, narrative),
        "TABLE": render_table(data, narrative), "WATCH": render_watch(narrative),
        "FOOT": render_foot(data),
    }
    out = template
    for k in _MARKERS:
        out = out.replace("<!--%s-->" % k, frag[k])
    return out
