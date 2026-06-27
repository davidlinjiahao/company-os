#!/bin/bash
# Plaud sync daemon: sync transcripts, enrich names, and gate for team vault
# Runs every 30 minutes via launchd
#
# All paths are relative to the company-os repo root.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
export HOME="${HOME:-$(dscl . -read /Users/$(whoami) NFSHomeDirectory | awk '{print $2}')}"

# Detect vault path from settings.local.json or use default
SETTINGS_LOCAL="$HOME/.claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ]; then
    VAULT_PATH=$(python3 -c "
import json, sys
try:
    d = json.load(open('$SETTINGS_LOCAL'))
    print(d.get('mcpServers',{}).get('obsidian',{}).get('env',{}).get('OBSIDIAN_VAULT_PATH',''))
except: pass
" 2>/dev/null)
fi
export OBSIDIAN_VAULT_PATH="${VAULT_PATH:-$HOME/Documents/ObsidianVault}"

LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"

PLAUD_MCP_DIR="$REPO_DIR/mcps/plaud-mcp"
SYNC_SCRIPT="$REPO_DIR/skills/sync/src/sync_plaud.py"

cd "$PLAUD_MCP_DIR" || {
    echo "$LOG_PREFIX ERROR: Could not cd to $PLAUD_MCP_DIR"
    exit 1
}

UV="$HOME/.local/bin/uv"
if [ ! -x "$UV" ]; then
    UV="$(command -v uv 2>/dev/null)"
fi

if [ ! -x "$UV" ]; then
    echo "$LOG_PREFIX ERROR: uv not found"
    exit 1
fi

# Step 1: Sync new Plaud transcripts to personal Obsidian
# Use --days 30 to catch any files that may have been missed during downtime
echo "$LOG_PREFIX Step 1: Syncing Plaud transcripts"
"$UV" run python3 -u "$SYNC_SCRIPT" --days 30 2>&1
echo "$LOG_PREFIX Step 1 done (exit=$?)"

# Step 2: Refresh placeholder titles (files synced before Plaud generated a title)
echo "$LOG_PREFIX Step 2: Refreshing placeholder titles"
"$UV" run python3 -u "$SYNC_SCRIPT" --refresh-titles 2>&1
echo "$LOG_PREFIX Step 2 done (exit=$?)"

# Step 3: Enrich transcript names with Google Calendar event titles
echo "$LOG_PREFIX Step 3: Enriching transcript names"
"$UV" run --extra enrich python3 -u "$PLAUD_MCP_DIR/enrich_names.py" --days 3 --apply 2>&1
echo "$LOG_PREFIX Step 3 done (exit=$?)"

# Step 4: Remove duplicates (old-format and plaud_id-based)
echo "$LOG_PREFIX Step 4: Cleaning up duplicates"
"$UV" run python3 -u "$SYNC_SCRIPT" --cleanup 2>&1
echo "$LOG_PREFIX Step 4 done (exit=$?)"

# Step 5: Classify + gate new transcripts for team vault
echo "$LOG_PREFIX Step 5: Running transcript gate"
"$UV" run python3 -u "$SCRIPT_DIR/transcript_gate.py" 2>&1
echo "$LOG_PREFIX Step 5 done (exit=$?)"

echo "$LOG_PREFIX All steps complete"
