#!/bin/bash
# Verify all referenced paths exist in the repo
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0

check() {
    if [ -e "$REPO_DIR/$1" ]; then
        echo "  PASS  $1"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $1"
        FAIL=$((FAIL + 1))
    fi
}

check_executable() {
    if [ -x "$REPO_DIR/$1" ]; then
        echo "  PASS  $1 (executable)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $1 (not executable or missing)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Path Existence Tests ==="
echo ""

echo "Core files:"
check "setup.sh"
check_executable "setup.sh"
check ".env.tpl"
check "CLAUDE.md"
check "README.md"
check ".claude/settings.json"

echo ""
echo "Setup directory structure:"
check "setup/init.sh"
check_executable "setup/init.sh"
check "setup/verify.sh"
check_executable "setup/verify.sh"
check "setup/lib/colors.sh"
check "setup/lib/utils.sh"
for step in 01-cli 02-ssh 03-apps 04-1password 05-skills 06-mcps 07-daemon 08-vault 09-verify 10-summary 11-qm; do
    check "setup/steps/${step}.sh"
done
check_executable "setup/steps/11-qm.sh"

echo ""
echo "QM deployment (official scaffold, no org secrets):"
check "package.json"
check "qm.config.jsonc"
check ".env.example"
check "deployment.md"
check "AGENTS.md"
check "slack-app-manifest.yml"
check "sandbox/skills/greet/SKILL.md"
check ".codex/skills/deploy-qm/SKILL.md"
check ".codex/skills/company-os-deploy/SKILL.md"
check ".codex/skills/company-os-deploy/references/channels.md"

echo ""
echo "Hook paths from settings.json:"
if grep -qE 'upgrades/hooks/' "$REPO_DIR/.claude/settings.json" 2>/dev/null; then
    for hook_path in $(grep -oE 'upgrades/hooks/[a-z_-]+\.sh' "$REPO_DIR/.claude/settings.json"); do
        check "$hook_path"
    done
else
    echo "  PASS  no hook scripts referenced (upgrades/ is not part of this template)"
    PASS=$((PASS + 1))
fi

echo ""
echo "Vault MCP daemon:"
check "mcps/vault-mcp/daemon/run.sh"
check "mcps/vault-mcp/daemon/install.sh"
check "mcps/vault-mcp/daemon/com.company-os.vault-mcp.plist.template"

echo ""
echo "Vault MCP daemon paths resolve correctly:"
DAEMON_DIR="$REPO_DIR/mcps/vault-mcp/daemon"
RESOLVED="$(cd "$DAEMON_DIR/../../.." && pwd)"
if [ "$RESOLVED" = "$REPO_DIR" ]; then
    echo "  PASS  run.sh REPO_DIR resolves to repo root"
    PASS=$((PASS + 1))
else
    echo "  FAIL  run.sh REPO_DIR resolves to $RESOLVED (expected $REPO_DIR)"
    FAIL=$((FAIL + 1))
fi

if grep -q 'SCRIPT_DIR/../users.json' "$DAEMON_DIR/install.sh"; then
    echo "  PASS  install.sh USERS_FILE points to ../users.json"
    PASS=$((PASS + 1))
else
    echo "  FAIL  install.sh USERS_FILE path incorrect"
    FAIL=$((FAIL + 1))
fi

# Check plist template uses __REPO_DIR__ (not hardcoded path)
if grep -q '__REPO_DIR__/mcps/vault-mcp/daemon/run.sh' "$DAEMON_DIR/com.company-os.vault-mcp.plist.template"; then
    echo "  PASS  plist template uses __REPO_DIR__ placeholder"
    PASS=$((PASS + 1))
else
    echo "  FAIL  plist template missing __REPO_DIR__ placeholder"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "MCPs:"
check "mcps/notion-mcp"
check "mcps/obsidian-mcp"
check "mcps/plaud-mcp"
check "mcps/vault-mcp"

echo ""
echo "Skills (each must have SKILL.md):"
for dir in "$REPO_DIR"/skills/*/; do
    skill=$(basename "$dir")
    rel="skills/$skill/SKILL.md"
    if git -C "$REPO_DIR" check-ignore -q "skills/$skill" 2>/dev/null; then
        echo "  SKIP  $rel (gitignored — not part of the public template)"
        continue
    fi
    check "$rel"
done

echo ""
echo "────────────────────────"
echo "  $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
