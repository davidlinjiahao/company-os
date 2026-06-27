#!/bin/bash
# Step 9: Health Checks (can run standalone: bash setup/steps/09-verify.sh)
# Fixes: M3 (clear message about restarting)

# Standalone mode: bootstrap if not sourced from init.sh
if [[ -z "${REPO_DIR:-}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$SCRIPT_DIR/../lib/colors.sh"
    source "$SCRIPT_DIR/../lib/utils.sh"
    REPO_DIR="$(detect_repo_dir)"
    ensure_path
fi

header "9/10" "Verification"

VERIFY_PASS=0
VERIFY_FAIL=0

verify_check() {
    local name="$1"
    local result="$2"
    if [[ "$result" == "PASS" ]]; then
        ok "$name"
        VERIFY_PASS=$((VERIFY_PASS + 1))
    else
        fail "$name — $result"
        VERIFY_FAIL=$((VERIFY_FAIL + 1))
    fi
}

# Check CLI tools
for tool in brew git python3 uv npm bun claude qmd gh op; do
    if command -v "$tool" &>/dev/null; then
        verify_check "$tool" "PASS"
    else
        verify_check "$tool" "not found"
    fi
done

# Check SSH
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    verify_check "GitHub SSH" "PASS"
else
    verify_check "GitHub SSH" "not authenticated"
fi

# Check skills symlink
if [[ -L "$HOME/.claude/skills" && -d "$HOME/.claude/skills" ]]; then
    verify_check "Skills symlink" "PASS"
else
    verify_check "Skills symlink" "not linked"
fi

# Check MCP configs exist (via claude mcp list)
if command -v claude &>/dev/null; then
    MCP_LIST=$(claude mcp list 2>/dev/null || echo "")
    for mcp_name in notion obsidian plaud vault; do
        if echo "$MCP_LIST" | grep -qi "$mcp_name"; then
            verify_check "MCP: $mcp_name" "PASS"
        else
            verify_check "MCP: $mcp_name" "not configured"
        fi
    done
fi

echo ""
echo -e "  ${BOLD}$VERIFY_PASS passed, $VERIFY_FAIL failed${RESET}"

if [[ $VERIFY_FAIL -gt 0 ]]; then
    return 1 2>/dev/null || exit 1
fi
