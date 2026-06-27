#!/bin/bash
# vault-mcp daemon runner
# Starts the Bun MCP server + ngrok tunnel, keeps them running together.
# Designed to be called by launchd — exits if either process dies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_MCP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"

export HOME="${HOME:-$(dscl . -read /Users/$(whoami) NFSHomeDirectory | awk '{print $2}')}"
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.bun/bin:$PATH"

NGROK_DOMAIN="${VAULT_NGROK_DOMAIN:-vault.example.ngrok.dev}"
PORT=3131

# Google OAuth config (optional — needed for OAuth flow, not for legacy tokens)
if [[ -z "${GOOGLE_CLIENT_ID:-}" ]] || [[ -z "${GOOGLE_CLIENT_SECRET:-}" ]]; then
    echo "$LOG_PREFIX WARNING: GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET not set — Google OAuth disabled"
    echo "$LOG_PREFIX Legacy bearer token auth from users.json will still work"
fi

# Check emails.json (optional — needed for OAuth flow)
if [[ ! -f "$VAULT_MCP_DIR/emails.json" ]]; then
    echo "$LOG_PREFIX WARNING: emails.json not found — Google OAuth disabled"
fi

# Ensure users.json exists (optional — symlink from ~/vault-mcp/users.json)
USERS_FILE="$VAULT_MCP_DIR/users.json"
if [[ ! -f "$USERS_FILE" ]]; then
    if [[ -f "$HOME/vault-mcp/users.json" ]]; then
        ln -sf "$HOME/vault-mcp/users.json" "$USERS_FILE"
        echo "$LOG_PREFIX Symlinked users.json from ~/vault-mcp/"
    else
        echo "$LOG_PREFIX WARNING: No users.json found — legacy token auth disabled"
    fi
fi

# Ensure node_modules exist
if [[ ! -d "$VAULT_MCP_DIR/node_modules" ]]; then
    echo "$LOG_PREFIX Installing dependencies..."
    cd "$VAULT_MCP_DIR" && bun install
fi

# Check qmd index exists
if [[ ! -f "$HOME/.cache/qmd/index.sqlite" ]]; then
    echo "$LOG_PREFIX ERROR: qmd index not found at ~/.cache/qmd/index.sqlite"
    echo "$LOG_PREFIX Run 'qmd index' first to build the search index."
    exit 1
fi

# Kill any existing vault-mcp or ngrok processes on our port
lsof -ti :$PORT 2>/dev/null | xargs kill 2>/dev/null || true
pkill -f "ngrok.*$NGROK_DOMAIN" 2>/dev/null || true
sleep 1

echo "$LOG_PREFIX Starting vault-mcp server on port $PORT..."
cd "$VAULT_MCP_DIR"
VAULT_NGROK_DOMAIN="$NGROK_DOMAIN" \
  GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID:-}" \
  GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET:-}" \
  GOOGLE_WORKSPACE_DOMAIN="${GOOGLE_WORKSPACE_DOMAIN:-}" \
  bun run server.ts &
SERVER_PID=$!

# Wait for server to start
for i in {1..10}; do
    if lsof -i :$PORT 2>/dev/null | grep -q LISTEN; then
        echo "$LOG_PREFIX Server started (PID $SERVER_PID)"
        break
    fi
    sleep 1
done

if ! lsof -i :$PORT 2>/dev/null | grep -q LISTEN; then
    echo "$LOG_PREFIX ERROR: Server failed to start after 10s"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo "$LOG_PREFIX Starting ngrok tunnel ($NGROK_DOMAIN -> localhost:$PORT)..."
ngrok http --domain="$NGROK_DOMAIN" $PORT --log=stdout &
NGROK_PID=$!

sleep 3
echo "$LOG_PREFIX ngrok started (PID $NGROK_PID)"
echo "$LOG_PREFIX Vault MCP running at https://$NGROK_DOMAIN/mcp"

# Wait for either process to exit — if one dies, kill the other and exit
# launchd will restart us via KeepAlive
# Note: macOS ships bash 3.2 which lacks `wait -n`. Poll instead.
while kill -0 $SERVER_PID 2>/dev/null && kill -0 $NGROK_PID 2>/dev/null; do
    sleep 5
done

echo "$LOG_PREFIX A process exited. Cleaning up..."
kill $SERVER_PID 2>/dev/null || true
kill $NGROK_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true
wait $NGROK_PID 2>/dev/null || true
echo "$LOG_PREFIX Exiting (launchd will restart)"
exit 1
