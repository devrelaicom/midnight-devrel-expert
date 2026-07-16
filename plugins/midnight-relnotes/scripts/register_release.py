# scripts/register_release.py
"""Prepend a release object to a DynamicList<Item>.js and demote prior LATEST."""
import json, sys

ANCHOR = "const releases = ["
LATEST = "status: 'LATEST'"

# JS LineTerminators are illegal inside a single-quoted string literal. Escape
# \n, \r, and U+2028/U+2029 — a CRLF- or U+2028-bearing note would otherwise
# emit a component that only fails at docs-site build time. Backslash first.
_LINE_SEP, _PARA_SEP = chr(0x2028), chr(0x2029)

def js_string(s: str) -> str:
    return "'" + (s.replace("\\", "\\\\").replace("'", "\\'")
                   .replace("\n", "\\n").replace("\r", "\\r")
                   .replace(_LINE_SEP, "\\u2028").replace(_PARA_SEP, "\\u2029")) + "'"

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
    if ANCHOR not in js_text:
        raise ValueError(f"anchor {ANCHOR!r} not found — is this a DynamicList component?")
    idx = js_text.index(ANCHOR) + len(ANCHOR)
    combined = js_text[:idx] + "\n" + render_release(rel) + js_text[idx:]
    # Only a new LATEST demotes a prior one. If the note being registered isn't
    # LATEST (e.g. a backport), leave existing statuses untouched.
    if rel.get("status") != "LATEST":
        return combined
    # combined now has the just-inserted LATEST first; demote the *next* one.
    first = combined.find(LATEST)
    second = combined.find(LATEST, first + 1)
    if second == -1:
        return combined  # no pre-existing LATEST to demote (first note for this component)
    return combined[:second] + "status: 'SUPPORTED'" + combined[second + len(LATEST):]

def main(argv=None):
    argv = argv or sys.argv[1:]
    path, rel = argv[0], json.loads(argv[1])
    open(path, "w").write(register(open(path).read(), rel))
    print(f"registered {rel['version']} in {path}")

if __name__ == "__main__":
    main()
