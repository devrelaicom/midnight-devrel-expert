#!/usr/bin/env bash
# scripts/change_harvest.sh <repo> <from_tag> <to_tag> — condensed change inventory. Read-only.
set -uo pipefail
REPO="$1"; FROM="$2"; TO="$3"
echo "### Release body ($TO)"
gh release view "$TO" --repo "$REPO" --json body --jq '.body' 2>/dev/null | head -80
echo ""
echo "### Merged PRs in $FROM..$TO"
gh api "repos/$REPO/compare/$FROM...$TO" --jq \
  '.commits[].commit.message | split("\n")[0]' 2>/dev/null | grep -iE 'merge pull request|\(#[0-9]+\)' | head -60
echo ""
echo "### Commit subjects in $FROM..$TO"
gh api "repos/$REPO/compare/$FROM...$TO" --jq '.commits[].commit.message | split("\n")[0]' 2>/dev/null | head -80
