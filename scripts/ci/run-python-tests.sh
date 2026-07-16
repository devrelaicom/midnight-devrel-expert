#!/usr/bin/env bash
# run-python-tests.sh - One shared runner for the whole marketplace.
# Runs pytest from each plugin root that contains test_*.py, so `import scripts.*`
# resolves and each plugin's tests run isolated from its siblings. A plugin opts in
# simply by adding test_*.py (see README "Adding Python tests to your plugin").
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGINS_DIR="$ROOT/plugins"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2; exit 1
fi
if ! python3 -m pytest --version >/dev/null 2>&1; then
  echo "pytest not installed (pip install pytest)" >&2; exit 1
fi

any=0; failed=0; summary=()
for plugin in "$PLUGINS_DIR"/*/; do
  name="$(basename "$plugin")"
  if find "$plugin" -name 'test_*.py' -not -path '*/node_modules/*' -print -quit | grep -q .; then
    any=1
    echo "==> pytest: $name"
    if ( cd "$plugin" && python3 -m pytest -q --ignore=node_modules ); then
      summary+=("$name: PASS")
    else
      summary+=("$name: FAIL"); failed=1
    fi
  fi
done

echo ""
echo "== Python test summary =="
if [ "$any" = 0 ]; then
  echo "No plugin Python tests found."
  exit 0
fi
for line in "${summary[@]}"; do echo "  $line"; done
if [ "$failed" = 0 ]; then echo "All plugin Python tests passed."; else echo "Some plugin Python tests FAILED."; fi
exit "$failed"
