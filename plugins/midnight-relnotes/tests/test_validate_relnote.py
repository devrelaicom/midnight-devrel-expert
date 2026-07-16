import scripts.validate_relnote as val

GOOD_MDX = """---
title: Midnight.js v4.1.1 release notes
description: "notes"
displayed_sidebar: sidebar
---

## High-level summary
x
## Audience
x
## Summary of updates
x
## New features
x
## Breaking changes
x
## Bug fixes and quality improvements
x
## Known issues
x
## Links and references
x
"""

GOOD_JS = "link: '/relnotes/midnight-js/midnight-js-4-1-1', version: '4.1.1',"

def test_valid_note_has_no_problems():
    probs = val.validate(GOOD_MDX, "midnight-js-4-1-1.mdx", "midnight-js", "4.1.1", "dash", GOOD_JS)
    assert probs == []

def test_bad_filename_flagged():
    probs = val.validate(GOOD_MDX, "midnight-js-4.1.1.mdx", "midnight-js", "4.1.1", "dash", GOOD_JS)
    assert any("filename" in p for p in probs)

def test_missing_section_flagged():
    mdx = GOOD_MDX.replace("## Known issues\nx\n", "")
    probs = val.validate(mdx, "midnight-js-4-1-1.mdx", "midnight-js", "4.1.1", "dash", GOOD_JS)
    assert any("Known issues" in p for p in probs)

def test_unregistered_version_flagged():
    probs = val.validate(GOOD_MDX, "midnight-js-4-1-1.mdx", "midnight-js", "4.1.1", "dash", "no registration here")
    assert any("DynamicList" in p for p in probs)

def test_shorter_version_not_falsely_registered():
    # only 4.1.10 is registered; validating 4.1.1 must be flagged, not falsely matched
    js = "version: '4.1.10', link: '/relnotes/midnight-js/midnight-js-4-1-10',"
    probs = val.validate(GOOD_MDX, "midnight-js-4-1-1.mdx", "midnight-js", "4.1.1", "dash", js)
    assert any("DynamicList" in p for p in probs)
