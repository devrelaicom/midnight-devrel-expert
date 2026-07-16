"""CLI: fetch PRs via gh (facts only) and build the HTML report.

Subcommands:
  fetch  --repo owner/name --since YYYY-MM-DD [--limit N] --out report-data.json
  build  --data report-data.json --narrative narrative.json --template template.html --out report.html
"""
import argparse, json, subprocess, sys
from datetime import datetime, timezone
from . import lib, enrich, render

_FIELDS = ("number,title,state,isDraft,author,createdAt,updatedAt,closedAt,mergedAt,"
           "url,labels,baseRefName,additions,deletions,changedFiles,reviewDecision,"
           "comments,reviews,statusCheckRollup")

def _gh_fetch(repo, since, limit):
    search = "updated:>=%s" % since
    proc = subprocess.run(
        ["gh", "pr", "list", "--repo", repo, "--search", search, "--state", "all",
         "--limit", str(limit), "--json", _FIELDS],
        capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)

def cmd_fetch(a):
    repo = lib.parse_repo(a.repo)
    raw = _gh_fetch(repo, a.since, a.limit)
    now = datetime.now(timezone.utc)
    data = enrich.build_report_data(raw, repo, a.since, now)
    with open(a.out, "w") as fh:
        json.dump(data, fh, indent=2)
    print("%d PRs -> %s" % (len(data["prs"]), a.out))

def cmd_build(a):
    data = json.load(open(a.data))
    narrative = json.load(open(a.narrative))
    template = open(a.template).read()
    html = render.render_report(template, data, narrative)
    with open(a.out, "w") as fh:
        fh.write(html)
    print("report -> %s (%d bytes)" % (a.out, len(html)))

def main(argv=None):
    ap = argparse.ArgumentParser(prog="pr_report")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--repo", required=True)
    f.add_argument("--since", required=True, help="ISO date YYYY-MM-DD")
    f.add_argument("--limit", type=int, default=200)
    f.add_argument("--out", required=True)
    f.set_defaults(func=cmd_fetch)
    b = sub.add_parser("build")
    b.add_argument("--data", required=True)
    b.add_argument("--narrative", required=True)
    b.add_argument("--template", required=True)
    b.add_argument("--out", required=True)
    b.set_defaults(func=cmd_build)
    a = ap.parse_args(argv)
    a.func(a)

if __name__ == "__main__":
    main()
