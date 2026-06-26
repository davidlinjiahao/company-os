#!/bin/bash
# Validate each setup step file has valid bash syntax and structure
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0

echo "=== Setup Steps Validation ==="
echo ""

# 1. All expected step files exist
echo "Step files exist:"
EXPECTED_STEPS="01-cli 02-ssh 03-apps 04-1password 05-skills 06-mcps 07-daemon 08-vault 09-verify 10-summary"
for step in $EXPECTED_STEPS; do
    if [ -f "$REPO_DIR/setup/steps/${step}.sh" ]; then
        echo "  PASS  ${step}.sh"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  ${step}.sh missing"
        FAIL=$((FAIL + 1))
    fi
done

# 2. All step files have valid bash syntax
echo ""
echo "Bash syntax:"
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

# 3. Lib files exist and have valid syntax
echo ""
echo "Lib files:"
for lib in colors utils; do
    lib_path="$REPO_DIR/setup/lib/${lib}.sh"
    if [ -f "$lib_path" ] && bash -n "$lib_path" 2>/dev/null; then
        echo "  PASS  ${lib}.sh"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  ${lib}.sh (missing or invalid)"
        FAIL=$((FAIL + 1))
    fi
done

# 4. init.sh and verify.sh exist and are executable
echo ""
echo "Entrypoints:"
for entry in init verify; do
    entry_path="$REPO_DIR/setup/${entry}.sh"
    if [ -x "$entry_path" ]; then
        echo "  PASS  ${entry}.sh (executable)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  ${entry}.sh (not executable or missing)"
        FAIL=$((FAIL + 1))
    fi
done

# 5. 06-mcps.sh uses resolve_uv (not bare uv)
echo ""
echo "MCP script uses absolute uv:"
if grep -q 'resolve_uv' "$REPO_DIR/setup/steps/06-mcps.sh"; then
    echo "  PASS  06-mcps.sh calls resolve_uv()"
    PASS=$((PASS + 1))
else
    echo "  FAIL  06-mcps.sh doesn't call resolve_uv()"
    FAIL=$((FAIL + 1))
fi

# 6. 06-mcps.sh uses correct executable name (notion-mcp, not notion-enhanced-mcp)
if grep -q 'notion-mcp' "$REPO_DIR/setup/steps/06-mcps.sh" && ! grep -q 'notion-enhanced-mcp' "$REPO_DIR/setup/steps/06-mcps.sh"; then
    echo "  PASS  06-mcps.sh uses correct notion-mcp executable"
    PASS=$((PASS + 1))
else
    echo "  FAIL  06-mcps.sh uses wrong executable name"
    FAIL=$((FAIL + 1))
fi

# 7. No bare 'uv' in MCP add commands (should use $UV or absolute path)
if grep -E 'claude mcp add.*-- \w+ uv ' "$REPO_DIR/setup/steps/06-mcps.sh" | grep -v '\$UV' | grep -q .; then
    echo "  FAIL  06-mcps.sh uses bare 'uv' in MCP commands"
    FAIL=$((FAIL + 1))
else
    echo "  PASS  06-mcps.sh uses \$UV variable (absolute path)"
    PASS=$((PASS + 1))
fi

echo ""
echo "────────────────────────"
echo "  $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
