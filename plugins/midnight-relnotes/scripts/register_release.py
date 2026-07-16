# scripts/register_release.py
"""Prepend a release object to a DynamicList<Item>.js and demote prior LATEST."""
import json, sys

ANCHOR = "const releases = ["

def js_string(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"

def render_release(rel: dict) -> str:
    lines = ["  {",
             f"    version: {js_string(rel['version'])},",
             f"    status: {js_string(rel['status'])},",
             f"    date: {js_string(rel['date'])},",
             f"    summary: {js_string(rel['summary'])},",
             "    details: ["]
    for d in rel["details"]:
        lines.append(f"      {js_string(d)},")
    lines.append("    ],")
    lines.append("    artifacts: [")
    for a in rel["artifacts"]:
        lines.append("      { name: %s, url: %s }," % (js_string(a["name"]), js_string(a["url"])))
    lines.append("    ],")
    lines.append(f"    link: {js_string(rel['link'])},")
    lines.append("  },")
    return "\n".join(lines)

def register(js_text: str, rel: dict) -> str:
    idx = js_text.index(ANCHOR) + len(ANCHOR)
    demoted = js_text[:idx] + "\n" + render_release(rel) + js_text[idx:]
    # demote the FIRST pre-existing LATEST, which is now the second LATEST in the string
    first = demoted.index("status: 'LATEST'")
    second = demoted.find("status: 'LATEST'", first + 1)
    if second == -1:
        return demoted  # no pre-existing LATEST to demote (first note for this component)
    return demoted[:second] + "status: 'SUPPORTED'" + demoted[second + len("status: 'LATEST'"):]

def main(argv=None):
    argv = argv or sys.argv[1:]
    path, rel = argv[0], json.loads(argv[1])
    open(path, "w").write(register(open(path).read(), rel))
    print(f"registered {rel['version']} in {path}")

if __name__ == "__main__":
    main()
