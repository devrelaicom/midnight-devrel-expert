#!/usr/bin/env bash
# scripts/doctor.sh — quick sense check for midnight-relnotes. Never installs.
set -uo pipefail
TMP_FILE="$(mktemp "${TMPDIR:-/tmp}/relnotes-doctor.XXXXXX")"
echo "relnotes doctor: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$TMP_FILE"

check() { # check <bin> <version-args...>
  local name="$1"; shift
  if command -v "$name" >/dev/null 2>&1; then
    echo "OK      $name ($("$name" "$@" 2>&1 | head -1))"
  else
    echo "MISSING $name"; return 1
  fi
}

check git --version
check jq --version
check python3 --version
check npm --version
if command -v node >/dev/null 2>&1; then
  ver="$(node --version | tr -d 'v')"; major="${ver%%.*}"
  if [ "$major" -ge 22 ]; then echo "OK      node ($ver)"; else echo "MISSING node>=22 (found $ver)"; fi
else
  echo "MISSING node"
fi
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then echo "OK      gh (authenticated)"; else echo "MISSING gh-auth (run: gh auth login)"; fi
else
  echo "MISSING gh"
fi
if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && \
   git remote get-url origin 2>/dev/null | grep -q "midnight-docs"; then
  echo "OK      docs-checkout"
else
  echo "MISSING docs-checkout (run from inside a midnight-docs clone)"
fi
echo "install: node>=22 → https://nodejs.org ; gh → https://cli.github.com ; jq → your package manager"
echo "Full log: $TMP_FILE"
