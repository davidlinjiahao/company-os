#!/bin/bash
# Verify Makefile works from new location
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAKEFILE_DIR="$REPO_DIR/upgrades/tools/researcher"
PASS=0
FAIL=0

echo "=== Makefile Tests ==="
echo ""

# 1. Makefile exists
if [ -f "$MAKEFILE_DIR/Makefile" ]; then
    echo "  PASS  Makefile exists at upgrades/tools/researcher/"
    PASS=$((PASS + 1))
else
    echo "  FAIL  Makefile missing at upgrades/tools/researcher/"
    FAIL=$((FAIL + 1))
    echo ""
    echo "────────────────────────"
    echo "  $PASS passed, $FAIL failed"
    exit 1
fi

# 2. make help succeeds
if cd "$MAKEFILE_DIR" && make help >/dev/null 2>&1; then
    echo "  PASS  make help succeeds"
    PASS=$((PASS + 1))
else
    echo "  FAIL  make help failed"
    FAIL=$((FAIL + 1))
fi

# 3. RESEARCHER variable doesn't reference old path
if grep -q 'cd tools/researcher' "$MAKEFILE_DIR/Makefile"; then
    echo "  FAIL  Makefile still references old 'cd tools/researcher' path"
    FAIL=$((FAIL + 1))
else
    echo "  PASS  No stale path in RESEARCHER variable"
    PASS=$((PASS + 1))
fi

echo ""
echo "────────────────────────"
echo "  $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
