#!/usr/bin/env bash
# scripts/tool_probe.sh — report availability of the optional sharing/build tools
# the dashboard flow can use, as a single JSON object. One call instead of three
# `command -v` round-trips.
#
#   agentbin  — upload a report and get a shareable URL (HTML or raw Markdown)
#   mdtohtml  — convert Markdown to standalone HTML (for the Claude Web path)
#   cargo     — crates.io version resolution for crates:* items (informational)
#
# Output: {"agentbin":true,"mdtohtml":false,"cargo":true}
set -u
have() { if command -v "$1" >/dev/null 2>&1; then printf true; else printf false; fi; }
printf '{"agentbin":%s,"mdtohtml":%s,"cargo":%s}\n' \
  "$(have agentbin)" "$(have mdtohtml)" "$(have cargo)"
