import re
import scripts.render as rd

DATA = {
    "meta": {"repo": "o/n", "since": "2026-07-02", "generatedAt": "2026-07-16T00:00:00+00:00",
             "totals": {"total": 3, "open": 2, "merged": 1, "closed": 0, "human": 2, "bot": 1}},
    "checkFailureRates": [{"name": "Vercel", "failed": 2, "total": 2, "rate": 1.0}],
    "prs": [
        {"number": 9, "title": "Add <thing> & stuff", "url": "https://x/9", "state": "OPEN",
         "isDraft": False, "baseRefName": "main", "author": "alice", "authorType": "human",
         "reviewDecision": "REVIEW_REQUIRED", "additions": 5, "deletions": 1, "changedFiles": 2,
         "failingChecks": [{"name": "Vercel", "conclusion": "FAILURE"}], "ciStatusRaw": "failing",
         "humanComments": 1, "reviews": [], "ageDays": 3, "idleDays": 0,
         "blockedOn": "maintainer", "priority": 3, "action": "Needs a maintainer review"},
        {"number": 8, "title": "CI fix", "url": "https://x/8", "state": "OPEN",
         "isDraft": False, "baseRefName": "main", "author": "app/bot", "authorType": "bot",
         "reviewDecision": "REVIEW_REQUIRED",
         "additions": 2, "deletions": 2, "changedFiles": 1,
         "failingChecks": [{"name": "deploy", "conclusion": "FAILURE"}], "ciStatusRaw": "failing",
         "humanComments": 0, "reviews": [], "ageDays": 9, "idleDays": 0,
         "blockedOn": "author (CI)", "priority": 2, "action": "Fix failing CI checks"},
    ],
}
NARR = {
    "executive_summary": ["Solid two weeks.", "One CI signal is noise."],
    "themes": [{"name": "Docs", "count": 2, "blurb": "New pages", "prs": [9]}],
    "observations": [{"tag": "CI signal", "kind": "caution", "title": "Vercel is noise",
                      "body_html": "Fails on <b>2/2</b> PRs.", "meta_prs": [9]}],
    "watch_items": [{"severity": "warn", "title": "Watch this", "desc_html": "Do the <i>thing</i>."}],
    "noise_checks": ["Vercel"],
    "real_ci_blocked": [8],
}
TEMPLATE = ("<html><body><div id=meta><!--META--></div><div id=lede><!--LEDE--></div>"
            "<div id=kpis><!--KPIS--></div><div id=meters><!--METERS--></div>"
            "<div id=distro><!--DISTRO--></div><div id=themes><!--THEMES--></div>"
            "<div id=obs><!--OBSERVATIONS--></div><div id=queue><!--QUEUE--></div>"
            "<table><tbody><!--TABLE--></tbody></table><div id=watch><!--WATCH--></div>"
            "<footer><!--FOOT--></footer></body></html>")

def test_esc_escapes_html():
    assert rd.esc("a & <b>") == "a &amp; &lt;b&gt;"

def test_render_report_replaces_all_markers():
    out = rd.render_report(TEMPLATE, DATA, NARR)
    assert "<!--" not in out               # every marker consumed
    assert "Add &lt;thing&gt; &amp; stuff" in out   # title escaped
    assert "o/n" in out                    # meta repo present

def test_noise_and_real_ci_blocked_reflected():
    out = rd.render_report(TEMPLATE, DATA, NARR)
    # PR 9's only failing check is Vercel (noise) -> shown green + noise marker, not "fail"
    assert "Ⓥ" in out                 # circled V noise marker for PR 9
    # meters "CI blocked (real)" count comes from real_ci_blocked -> 1
    assert re.search(r'm-num">1<', out)

def test_narrative_sections_present():
    out = rd.render_report(TEMPLATE, DATA, NARR)
    assert "Solid two weeks." in out
    assert "New pages" in out
    assert "Vercel is noise" in out
    assert "Watch this" in out
