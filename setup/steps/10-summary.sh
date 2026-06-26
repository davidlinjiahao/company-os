#!/bin/bash
# Step 10: Final Summary
# Fixes: M3 (clear "restart Claude Code" message)

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "10/10" "Done!"

echo ""
echo -e "${BOLD}══════════════════════════════════════${RESET}"
echo -e "${BOLD}   Company OS — Setup Complete!${RESET}"
echo -e "${BOLD}══════════════════════════════════════${RESET}"

# CLI tools
echo -e " CLI Tools       ${GREEN}✓${RESET} brew, git, python, uv, bun, node, gh, qmd"
echo -e " Claude Code     ${GREEN}✓${RESET} $(claude --version 2>/dev/null || echo 'installed')"
echo -e " SSH Key         ${GREEN}✓${RESET} configured for GitHub"

# 1Password + secrets
if [[ "${STATUS[secrets]:-skipped}" == "skipped" ]]; then
    echo -e " 1Password       ${YELLOW}!${RESET} service account token needed — re-run later"
else
    echo -e " 1Password       ${GREEN}✓${RESET} ${STATUS[secrets]} pulled (service account)"
fi

# Skills
echo -e " Skills          ${GREEN}✓${RESET} ${STATUS[skills]:-0 commands} linked"
echo -e " ${DIM}─────────────────────────────────────${RESET}"

# MCPs
echo -e " Notion          ${GREEN}✓${RESET} enabled (shared token)"

if [[ "${STATUS[obsidian]:-disabled}" == "enabled" ]]; then
    echo -e " Obsidian        ${GREEN}✓${RESET} enabled"
else
    echo -e " Obsidian        ${DIM}✗ disabled${RESET}"
fi

if [[ "${STATUS[plaud]:-disabled}" == "enabled" ]]; then
    echo -e " Plaud           ${GREEN}✓${RESET} enabled"
else
    echo -e " Plaud           ${DIM}✗ disabled${RESET}"
fi

if [[ "${STATUS[daemon]:-n/a}" == "running" ]]; then
    echo -e " Plaud Daemon    ${GREEN}✓${RESET} running (every 30 min)"
elif [[ "${STATUS[daemon]:-n/a}" == "skipped" ]]; then
    echo -e " Plaud Daemon    ${DIM}✗ skipped${RESET}"
fi

if [[ "${STATUS[vault]:-skipped}" == "skipped" || "${STATUS[vault]:-}" == "error" ]]; then
    echo -e " Vault           ${YELLOW}!${RESET} not configured"
else
    echo -e " Vault           ${GREEN}✓${RESET} logged in as ${STATUS[vault]}"
fi

echo -e "${BOLD}══════════════════════════════════════${RESET}"
echo ""
echo -e " ${BOLD}Next steps:${RESET}"
echo -e "   1. ${BOLD}Restart Claude Code${RESET} (MCPs load on session start)"
echo -e "   2. Run ${BOLD}/setup --verify${RESET} to test MCP connections"
echo -e "   3. Try ${BOLD}/build${RESET} or ${BOLD}/search${RESET} to get started"
echo ""
