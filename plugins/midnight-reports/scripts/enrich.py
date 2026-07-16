"""Pure PR enrichment: facts only. Deciding which failing checks are 'noise' is the model's job."""
from . import lib

_BOT_COMMENTERS = ("vercel", "github-actions", "coderabbit", "cla")
_FAILURE = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "STARTUP_FAILURE", "ACTION_REQUIRED"}
_PENDING = {"PENDING", "EXPECTED", ""}
_REVIEW_ORDER = {"APPROVED", "CHANGES_REQUESTED", "REVIEW_REQUIRED", "NONE"}

def is_bot_author(author):
    a = author or {}
    return bool(a.get("is_bot")) or str(a.get("login", "")).startswith("app/")

def is_bot_commenter(login):
    l = (login or "").lower()
    return l.startswith("app/") or any(b in l for b in _BOT_COMMENTERS)

def _name(it):
    return it.get("name") or it.get("context") or "?"

def _conclusion(it):
    return (it.get("conclusion") or it.get("state") or "").upper()

def _incomplete(it):
    return (it.get("status") or "COMPLETED").upper() != "COMPLETED"

def _is_failure(it):
    return _conclusion(it) in _FAILURE

def _is_pending(it):
    if _is_failure(it):
        return False
    return _incomplete(it) or _conclusion(it) in _PENDING

def failing_checks(rollup):
    out = []
    for it in rollup or []:
        if _is_failure(it):
            out.append({"name": _name(it), "conclusion": _conclusion(it)})
        elif _is_pending(it):
            out.append({"name": _name(it), "conclusion": "PENDING"})
    return out

def ci_status_raw(rollup):
    items = rollup or []
    if not items:
        return "none"
    if any(_is_failure(it) for it in items):
        return "failing"
    if any(_is_pending(it) for it in items):
        return "pending"
    if {_conclusion(it) for it in items} <= {"SUCCESS", "NEUTRAL", "SKIPPED", ""}:
        return "passing"
    return "mixed"

def check_failure_rates(open_prs):
    tally = {}
    for pr in open_prs:
        for it in pr.get("statusCheckRollup") or []:
            rec = tally.setdefault(_name(it), [0, 0])
            rec[1] += 1
            if _is_failure(it):
                rec[0] += 1
    rows = [{"name": n, "failed": f, "total": t, "rate": round(f / t, 3) if t else 0.0}
            for n, (f, t) in tally.items()]
    return sorted(rows, key=lambda r: (r["rate"], r["failed"]), reverse=True)

def _mechanical_triage(pr, author_type, fails):
    if pr["state"] != "OPEN":
        return {"blockedOn": "", "priority": 99, "action": ""}
    hard = [c for c in fails if c["conclusion"] != "PENDING"]
    rd = pr.get("reviewDecision") or "NONE"
    if hard:
        return {"blockedOn": "author (CI)", "priority": 2, "action": "Fix failing CI checks"}
    if rd == "APPROVED":
        return {"blockedOn": "maintainer", "priority": 1, "action": "Approved - ready to merge"}
    if rd == "CHANGES_REQUESTED":
        return {"blockedOn": "author", "priority": 4, "action": "Author to address review feedback"}
    if author_type == "bot":
        return {"blockedOn": "maintainer", "priority": 5, "action": "Dependency bump - review & merge"}
    if rd == "REVIEW_REQUIRED":
        return {"blockedOn": "maintainer", "priority": 3, "action": "Needs a maintainer review"}
    return {"blockedOn": "maintainer", "priority": 6, "action": "Triage"}

def enrich_pr(pr, now):
    author = pr.get("author") or {}
    atype = "bot" if is_bot_author(author) else "human"
    fails = failing_checks(pr.get("statusCheckRollup"))
    human_comments = [c for c in (pr.get("comments") or [])
                      if not is_bot_commenter((c.get("author") or {}).get("login", ""))]
    reviews = [{"who": (r.get("author") or {}).get("login", ""), "state": r.get("state"),
                "at": (r.get("submittedAt") or "")[:10]}
               for r in (pr.get("reviews") or [])
               if not is_bot_commenter((r.get("author") or {}).get("login", ""))]
    rec = {
        "number": pr["number"], "title": pr.get("title", ""), "url": pr.get("url", ""),
        "state": pr["state"], "isDraft": bool(pr.get("isDraft")),
        "baseRefName": pr.get("baseRefName", ""),
        "author": author.get("login", ""), "authorType": atype,
        "createdAt": pr.get("createdAt"), "updatedAt": pr.get("updatedAt"),
        "closedAt": pr.get("closedAt"), "mergedAt": pr.get("mergedAt"),
        "reviewDecision": pr.get("reviewDecision") or "NONE",
        "additions": pr.get("additions", 0), "deletions": pr.get("deletions", 0),
        "changedFiles": pr.get("changedFiles", 0),
        "labels": [l.get("name") for l in (pr.get("labels") or [])],
        "failingChecks": fails, "ciStatusRaw": ci_status_raw(pr.get("statusCheckRollup")),
        "humanComments": len(human_comments), "reviews": reviews,
        "ageDays": lib.days_between(pr["createdAt"], now) if pr.get("createdAt") else 0,
        "idleDays": lib.days_between(pr["updatedAt"], now) if pr.get("updatedAt") else 0,
    }
    rec.update(_mechanical_triage(pr, atype, fails))
    return rec

def build_report_data(raw_prs, repo, since, now):
    prs = [enrich_pr(p, now) for p in raw_prs]
    open_raw = [p for p in raw_prs if p["state"] == "OPEN"]
    def n_state(s):
        return len([p for p in prs if p["state"] == s])
    meta = {
        "repo": repo, "since": since, "generatedAt": lib.iso_now(),
        "totals": {
            "total": len(prs), "open": n_state("OPEN"), "merged": n_state("MERGED"),
            "closed": n_state("CLOSED"),
            "human": len([p for p in prs if p["authorType"] == "human"]),
            "bot": len([p for p in prs if p["authorType"] == "bot"]),
        },
    }
    return {"meta": meta, "checkFailureRates": check_failure_rates(open_raw),
            "prs": sorted(prs, key=lambda p: p["number"], reverse=True)}
