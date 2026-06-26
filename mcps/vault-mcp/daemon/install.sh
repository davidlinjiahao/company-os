#!/bin/bash
# Install the vault-mcp LaunchAgent
# Starts vault-mcp server + ngrok tunnel on boot, keeps them alive.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_TEMPLATE="$SCRIPT_DIR/com.company-os.vault-mcp.plist.template"
PLIST_DEST="$HOME/Library/LaunchAgents/com.company-os.vault-mcp.plist"

echo "=== Installing vault-mcp daemon ==="

# 1. Check prerequisites
echo "1. Checking prerequisites..."

if ! command -v bun &>/dev/null; then
    echo "   ERROR: bun not found. Install with: brew install oven-sh/bun/bun"
    exit 1
fi
echo "   ✓ bun"

if ! command -v ngrok &>/dev/null; then
    echo "   ERROR: ngrok not found. Install with: brew install ngrok"
    exit 1
fi
echo "   ✓ ngrok"

if [[ ! -f "$HOME/.cache/qmd/index.sqlite" ]]; then
    echo "   ERROR: qmd index not found. Run 'qmd index' first."
    exit 1
fi
echo "   ✓ qmd index"

# Check for users.json
USERS_FILE="$SCRIPT_DIR/../users.json"
if [[ ! -f "$USERS_FILE" ]] && [[ ! -f "$HOME/vault-mcp/users.json" ]]; then
    echo "   ERROR: No users.json found."
    echo "   Create ~/vault-mcp/users.json with token -> name pairs."
    echo "   See mcps/vault-mcp/users.example.json for the format."
    exit 1
fi
echo "   ✓ users.json"

# 2. Unload old agent if exists
if launchctl list | grep -q "com.company-os.vault-mcp" 2>/dev/null; then
    echo "2. Unloading existing vault-mcp agent..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# 3. Kill any running vault-mcp processes
echo "3. Stopping existing processes..."
lsof -ti :3131 2>/dev/null | xargs kill 2>/dev/null || true
pkill -f "ngrok.*vault.*ngrok" 2>/dev/null || true
sleep 1

# 4. Generate plist from template
echo "4. Installing LaunchAgent..."
REPO_DIR="$(cd "$SCRIPT_DIR" && git rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "$REPO_DIR" ]]; then
    echo "   ERROR: Not inside a git repository. Run from the company-os checkout."
    exit 1
fi
sed -e "s|__REPO_DIR__|$REPO_DIR|g" -e "s|__HOME__|$HOME|g" "$PLIST_TEMPLATE" > "$PLIST_DEST"

EXPECTED_RUN_SH="$REPO_DIR/mcps/vault-mcp/daemon/run.sh"
if [[ ! -f "$EXPECTED_RUN_SH" ]]; then
    echo "   ERROR: run.sh not found at $EXPECTED_RUN_SH"
    echo "   REPO_DIR resolved to: $REPO_DIR — is this correct?"
    rm -f "$PLIST_DEST"
    exit 1
fi

# 5. Load
echo "5. Loading LaunchAgent..."
launchctl load "$PLIST_DEST"

# 6. Wait for server to be healthy
echo "6. Waiting for server health check (up to 15s)..."
HEALTHY=false
for i in {1..15}; do
    if curl -sf http://localhost:3131/health &>/dev/null; then
        HEALTHY=true
        break
    fi
    sleep 1
done

if $HEALTHY; then
    echo ""
    echo "=== Installed successfully ==="
    echo "  Plist:   $PLIST_DEST"
    echo "  Runner:  $SCRIPT_DIR/run.sh"
    echo "  Server:  mcps/vault-mcp/server.ts (port 3131)"
    echo "  Tunnel:  configured via VAULT_NGROK_DOMAIN"
    echo "  Log:     ~/Library/Logs/company-os-vault-mcp.log"
    echo ""
    echo "  Starts on boot, auto-restarts on crash."
    echo ""
    echo "  Operations:"
    echo "    Status:    launchctl list | grep vault-mcp"
    echo "    Health:    curl http://localhost:3131/health"
    echo "    Logs:      tail -f ~/Library/Logs/company-os-vault-mcp.log"
    echo "    Stop:      launchctl unload $PLIST_DEST"
    echo "    Restart:   launchctl unload $PLIST_DEST && launchctl load $PLIST_DEST"
    echo "    Reinstall: bash $SCRIPT_DIR/install.sh"
else
    echo ""
    echo "ERROR: Server not healthy after 15s"
    echo "  Check log: tail -50 ~/Library/Logs/company-os-vault-mcp.log"
    echo "  Check process: launchctl list | grep vault-mcp"
    echo "  Check port: lsof -i :3131"
    exit 1
fi
