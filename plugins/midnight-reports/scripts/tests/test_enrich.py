from datetime import datetime, timezone
import scripts.enrich as en

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)

def check(name, conclusion=None, status="COMPLETED"):
    return {"__typename": "CheckRun", "name": name, "status": status, "conclusion": conclusion}

def ctx(name, state):
    return {"__typename": "StatusContext", "context": name, "state": state}

def pr(number, state="OPEN", author="alice", is_bot=False, review="REVIEW_REQUIRED",
       rollup=None, comments=None, reviews=None, created="2026-07-10T00:00:00Z",
       updated="2026-07-15T00:00:00Z"):
    return {"number": number, "title": "t%d" % number, "url": "u%d" % number, "state": state,
            "isDraft": False, "baseRefName": "main",
            "author": {"login": author, "is_bot": is_bot}, "createdAt": created,
            "updatedAt": updated, "closedAt": None, "mergedAt": None, "reviewDecision": review,
            "additions": 5, "deletions": 1, "changedFiles": 2, "labels": [{"name": "x"}],
            "statusCheckRollup": rollup or [], "comments": comments or [], "reviews": reviews or []}

def test_bot_detection():
    assert en.is_bot_author({"login": "app/dependabot", "is_bot": True}) is True
    assert en.is_bot_author({"login": "app/renovate"}) is True
    assert en.is_bot_author({"login": "alice"}) is False
    assert en.is_bot_commenter("vercel") is True
    assert en.is_bot_commenter("github-actions") is True
    assert en.is_bot_commenter("CLAassistant") is True
    assert en.is_bot_commenter("alice") is False
    assert en.is_bot_commenter("declan") is False
    assert en.is_bot_commenter("sinclair") is False

def test_failing_checks_and_status():
    roll = [check("build", "SUCCESS"), ctx("Vercel", "FAILURE"),
            check("deploy", "FAILURE"), check("lint", None, status="IN_PROGRESS")]
    fails = en.failing_checks(roll)
    names = {f["name"]: f["conclusion"] for f in fails}
    assert names["Vercel"] == "FAILURE"
    assert names["deploy"] == "FAILURE"
    assert names["lint"] == "PENDING"
    assert "build" not in names
    assert en.ci_status_raw(roll) == "failing"
    assert en.ci_status_raw([check("a", "SUCCESS"), check("b", "SKIPPED")]) == "passing"
    assert en.ci_status_raw([]) == "none"

def test_failure_rates_are_facts_only():
    prs = [pr(1, rollup=[ctx("Vercel", "FAILURE"), check("build", "SUCCESS")]),
           pr(2, rollup=[ctx("Vercel", "FAILURE"), check("build", "FAILURE")])]
    rates = en.check_failure_rates(prs)
    row = {r["name"]: r for r in rates}
    assert row["Vercel"] == {"name": "Vercel", "failed": 2, "total": 2, "rate": 1.0}
    assert row["build"]["failed"] == 1 and row["build"]["total"] == 2
    assert rates[0]["name"] == "Vercel"  # sorted by rate desc

def test_enrich_strips_bot_discussion_and_computes_ages():
    p = pr(7, comments=[{"author": {"login": "vercel"}}, {"author": {"login": "bob"}}],
           reviews=[{"author": {"login": "github-actions"}, "state": "COMMENTED", "submittedAt": "2026-07-11T00:00:00Z"},
                    {"author": {"login": "carol"}, "state": "APPROVED", "submittedAt": "2026-07-12T00:00:00Z"}],
           created="2026-07-06T00:00:00Z", updated="2026-07-14T00:00:00Z")
    r = en.enrich_pr(p, NOW)
    assert r["humanComments"] == 1
    assert [rv["who"] for rv in r["reviews"]] == ["carol"]
    assert r["ageDays"] == 10 and r["idleDays"] == 2
    assert r["authorType"] == "human"

def test_mechanical_priority_orders_queue():
    approved = en.enrich_pr(pr(1, review="APPROVED"), NOW)
    cifail = en.enrich_pr(pr(2, rollup=[check("deploy", "FAILURE")]), NOW)
    changes = en.enrich_pr(pr(3, review="CHANGES_REQUESTED"), NOW)
    assert approved["priority"] == 1 and approved["blockedOn"] == "maintainer"
    assert cifail["priority"] == 2 and "CI" in cifail["blockedOn"]
    assert changes["priority"] == 4 and changes["blockedOn"] == "author"

def test_build_report_data_totals():
    prs = [pr(1, state="OPEN"), pr(2, state="MERGED"), pr(3, state="CLOSED"),
           pr(4, state="OPEN", author="app/dependabot", is_bot=True)]
    data = en.build_report_data(prs, "o/n", "2026-07-02", NOW)
    t = data["meta"]["totals"]
    assert t == {"total": 4, "open": 2, "merged": 1, "closed": 1, "human": 3, "bot": 1}
    assert [p["number"] for p in data["prs"]] == [4, 3, 2, 1]  # sorted desc
    assert data["meta"]["repo"] == "o/n" and data["meta"]["since"] == "2026-07-02"
