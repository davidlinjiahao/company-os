#!/bin/bash
# Step 7: Plaud Sync LaunchAgent
# Fixes: D1 (__REPO_DIR__ placeholder), D2 (daemon deployed as part of setup)

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "7/10" "Plaud Sync Daemon"

if [[ "${USE_PLAUD:-false}" != "true" ]]; then
    info "Skipped (Plaud not selected)"
    STATUS[daemon]="n/a"
    return 0 2>/dev/null || exit 0
fi

echo ""
echo "  Install plaud-sync background daemon?"
echo "  Syncs transcripts every 30 min, enriches with calendar, classifies for vault."
echo ""
read -rp "  (y/n) > " INSTALL_DAEMON

if [[ "$INSTALL_DAEMON" =~ ^[Yy] ]]; then
    bash "$REPO_DIR/mcps/plaud-mcp/daemon/install.sh"
    STATUS[daemon]="running"
else
    info "Skipped — run 'bash mcps/plaud-mcp/daemon/install.sh' later if you change your mind"
    STATUS[daemon]="skipped"
fi
