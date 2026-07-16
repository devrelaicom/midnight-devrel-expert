"""Structural lint for a release note + its DynamicList registration."""
import json, sys
from . import lib

REQUIRED_SECTIONS = [
    "## High-level summary", "## Audience", "## Summary of updates",
    "## Breaking changes", "## Known issues", "## Links and references",
]

def validate(mdx_text, filename, file_prefix, version, scheme, dynamiclist_text):
    problems = []
    expected = lib.version_to_filename(file_prefix, version, scheme) + ".mdx"
    if filename != expected:
        problems.append(f"filename {filename!r} should be {expected!r}")
    for key in ("title:", "displayed_sidebar:"):
        if key not in mdx_text:
            problems.append(f"frontmatter missing {key!r}")
    for section in REQUIRED_SECTIONS:
        if section not in mdx_text:
            problems.append(f"missing required section {section!r}")
    if version not in dynamiclist_text:
        problems.append(f"version {version!r} not registered in DynamicList component")
    return problems

def main(argv=None):
    argv = argv or sys.argv[1:]
    args = json.loads(argv[0])  # {mdx_text, filename, file_prefix, version, scheme, dynamiclist_text}
    probs = validate(**args)
    print(json.dumps({"ok": not probs, "problems": probs}))
    sys.exit(0 if not probs else 1)

if __name__ == "__main__":
    main()
