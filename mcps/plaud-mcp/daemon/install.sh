#!/bin/bash
# Install the plaud-sync LaunchAgent
# Run from anywhere — paths are derived from this script's location.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_TEMPLATE="$SCRIPT_DIR/com.company-os.plaud-sync.plist.template"
PLIST_DEST="$HOME/Library/LaunchAgents/com.company-os.plaud-sync.plist"
GATE_DIR="$HOME/.claude/transcript_gate"

echo "=== Installing plaud-sync daemon ==="

# 1. Create data directories
echo "1. Creating transcript gate directories..."
mkdir -p "$GATE_DIR/staging"

# 2. Check for API key
if [ ! -f "$GATE_DIR/env" ]; then
    echo ""
    echo "   WARNING: No API key found at $GATE_DIR/env"
    echo "   The transcript gate (Step 3) needs an Anthropic API key."
    echo "   Create it with:"
    echo "     echo 'ANTHROPIC_API_KEY=sk-ant-...' > $GATE_DIR/env"
    echo ""
fi

# Check for vault submit credentials (team members only)
if ! grep -q "VAULT_SUBMIT_URL" "$GATE_DIR/env" 2>/dev/null; then
    echo ""
    echo "   For remote transcript submission to the team vault:"
    echo "   Add these to $GATE_DIR/env:"
    echo "     VAULT_SUBMIT_URL=https://<your-vault-domain>/submit"
    echo "     VAULT_SUBMIT_TOKEN=<your-vault-token-from-users.json>"
    echo ""
fi

# 3. Unload old agent if exists
if launchctl list | grep -q "com.company-os.plaud-sync" 2>/dev/null; then
    echo "2. Unloading existing plaud-sync agent..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi
if launchctl list | grep -q "com.company-os.plaud-enrich" 2>/dev/null; then
    echo "   Unloading old plaud-enrich agent..."
    launchctl unload "$HOME/Library/LaunchAgents/com.company-os.plaud-enrich.plist" 2>/dev/null || true
fi

# 4. Generate plist from template
echo "3. Installing LaunchAgent..."
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
sed -e "s|__REPO_DIR__|$REPO_DIR|g" -e "s|__HOME__|$HOME|g" "$PLIST_TEMPLATE" > "$PLIST_DEST"

# 5. Load
echo "4. Loading LaunchAgent..."
launchctl load "$PLIST_DEST"

# 6. Verify
if launchctl list | grep -q "com.company-os.plaud-sync"; then
    echo ""
    echo "=== Installed successfully ==="
    echo "  Plist:   $PLIST_DEST"
    echo "  Runner:  $SCRIPT_DIR/run.sh"
    echo "  Gate:    $SCRIPT_DIR/transcript_gate.py"
    echo "  Data:    $GATE_DIR/"
    echo "  Log:     ~/Library/Logs/company-os-plaud-sync.log"
    echo ""
    echo "  Runs every 30 minutes. To run now:"
    echo "    bash $SCRIPT_DIR/run.sh"
else
    echo "ERROR: LaunchAgent failed to load"
    exit 1
fi
