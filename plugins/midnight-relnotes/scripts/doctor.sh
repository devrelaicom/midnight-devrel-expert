#!/usr/bin/env bash
# scripts/doctor.sh — quick sense check for midnight-relnotes. Never installs.
set -uo pipefail
echo "relnotes doctor: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
status=0  # becomes 1 if anything is MISSING, so callers can gate on the exit code

check() { # check <bin> <version-args...>
  local name="$1"; shift
  if command -v "$name" >/dev/null 2>&1; then
    echo "OK      $name ($("$name" "$@" 2>&1 | head -1))"
  else
    echo "MISSING $name"; status=1
  fi
}

check git --version
check jq --version
check python3 --version
check npm --version
if command -v node >/dev/null 2>&1; then
  ver="$(node --version | tr -d 'v')"; major="${ver%%.*}"
  if [ "$major" -ge 22 ]; then echo "OK      node ($ver)"; else echo "MISSING node>=22 (found $ver)"; status=1; fi
else
  echo "MISSING node"; status=1
fi
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then echo "OK      gh (authenticated)"; else echo "MISSING gh-auth (run: gh auth login)"; status=1; fi
else
  echo "MISSING gh"; status=1
fi
if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && \
   git remote get-url origin 2>/dev/null | grep -q "midnight-docs"; then
  echo "OK      docs-checkout"
else
  echo "MISSING docs-checkout (run from inside a midnight-docs clone)"; status=1
fi
echo "install: node>=22 → https://nodejs.org ; gh → https://cli.github.com ; jq → your package manager"
exit "$status"
