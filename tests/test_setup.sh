#!/bin/bash
# Dry-run validation of setup scripts
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0

echo "=== Setup Script Tests ==="
echo ""

# 1. Root setup.sh valid syntax
echo "Syntax check:"
if bash -n "$REPO_DIR/setup.sh" 2>/dev/null; then
    echo "  PASS  setup.sh is valid bash"
    PASS=$((PASS + 1))
else
    echo "  FAIL  setup.sh has syntax errors"
    FAIL=$((FAIL + 1))
fi

# 2. setup/init.sh valid syntax
if bash -n "$REPO_DIR/setup/init.sh" 2>/dev/null; then
    echo "  PASS  setup/init.sh is valid bash"
    PASS=$((PASS + 1))
else
    echo "  FAIL  setup/init.sh has syntax errors"
    FAIL=$((FAIL + 1))
fi

# 3. All step files have valid syntax
echo ""
echo "Step script syntax:"
for step in "$REPO_DIR"/setup/steps/*.sh; do
    name=$(basename "$step")
    if bash -n "$step" 2>/dev/null; then
        echo "  PASS  $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $name has syntax errors"
        FAIL=$((FAIL + 1))
    fi
done

# 4. Lib files have valid syntax
echo ""
echo "Lib script syntax:"
for lib in "$REPO_DIR"/setup/lib/*.sh; do
    name=$(basename "$lib")
    if bash -n "$lib" 2>/dev/null; then
        echo "  PASS  $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $name has syntax errors"
        FAIL=$((FAIL + 1))
    fi
done

# 5. setup.sh is a thin wrapper that delegates to setup/init.sh
echo ""
echo "Thin wrapper check:"
if grep -q 'setup/init.sh' "$REPO_DIR/setup.sh"; then
    echo "  PASS  setup.sh delegates to setup/init.sh"
    PASS=$((PASS + 1))
else
    echo "  FAIL  setup.sh doesn't reference setup/init.sh"
    FAIL=$((FAIL + 1))
fi

# 6. No stale configs/ or scripts/ references in setup files
echo ""
echo "Stale references:"
SETUP_FILES=$(find "$REPO_DIR/setup" -name "*.sh" -type f)
if echo "$SETUP_FILES" | xargs grep -l 'configs/' 2>/dev/null | grep -q .; then
    echo "  FAIL  setup/ files still reference configs/"
    FAIL=$((FAIL + 1))
else
    echo "  PASS  No stale configs/ reference in setup/"
    PASS=$((PASS + 1))
fi

# 7. .env.tpl exists (referenced by 04-1password.sh)
if [ -f "$REPO_DIR/.env.tpl" ]; then
    echo "  PASS  .env.tpl exists"
    PASS=$((PASS + 1))
else
    echo "  FAIL  .env.tpl missing"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "────────────────────────"
echo "  $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
