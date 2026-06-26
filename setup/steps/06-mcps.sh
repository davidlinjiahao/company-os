#!/bin/bash
# Step 6: Install MCPs at User Level
# Fixes: T5/M1 (absolute uv path), M2 (correct executable names), M4 (use CLI not settings files), M5/M6 (vault auto-detect)

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "6/10" "MCP Configuration"

# Resolve absolute uv path (fixes T5, M1)
UV=$(resolve_uv)
info "Using uv at: $UV"

# Pre-install dependencies
info "Pre-installing MCP dependencies..."
"$UV" sync --directory "$REPO_DIR/mcps/notion-mcp" --quiet 2>/dev/null || true
"$UV" sync --directory "$REPO_DIR/mcps/obsidian-mcp" --quiet 2>/dev/null || true
"$UV" sync --directory "$REPO_DIR/mcps/plaud-mcp" --quiet 2>/dev/null || true

# Notion (shared team token from 1Password / env)
NOTION_TOKEN="${NOTION_TOKEN:-}"
if [[ -z "$NOTION_TOKEN" && -f "$HOME/.company-os.env" ]]; then
    NOTION_TOKEN=$(grep '^NOTION_TOKEN=' "$HOME/.company-os.env" | cut -d= -f2-)
fi
if [[ -z "$NOTION_TOKEN" ]]; then
    warn "No NOTION_TOKEN found — run step 4 (1Password) first, or export NOTION_TOKEN"
    STATUS[notion]="skipped"
else
    claude mcp remove notion 2>/dev/null || true
    claude mcp add -s user \
        -e NOTION_TOKEN="$NOTION_TOKEN" \
        -- notion "$UV" run --directory "$REPO_DIR/mcps/notion-mcp" notion-mcp
    ok "Notion MCP configured"
fi

# Obsidian (if selected)
if [[ "${USE_OBSIDIAN:-false}" == "true" ]]; then
    VAULT_PATH="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/ObsidianVault}"
    claude mcp remove obsidian 2>/dev/null || true
    claude mcp add -s user \
        -e VAULT_GIT_SYNC=true \
        -e OBSIDIAN_VAULT_PATH="$VAULT_PATH" \
        -- obsidian "$UV" run --directory "$REPO_DIR/mcps/obsidian-mcp" obsidian-mcp
    ok "Obsidian MCP configured (vault: $VAULT_PATH)"
else
    info "Obsidian MCP skipped (not selected)"
fi

# Plaud (if selected)
if [[ "${USE_PLAUD:-false}" == "true" ]]; then
    claude mcp remove plaud 2>/dev/null || true
    claude mcp add -s user \
        -- plaud "$UV" run --directory "$REPO_DIR/mcps/plaud-mcp" plaud-mcp
    ok "Plaud MCP configured"
else
    info "Plaud MCP skipped (not selected)"
fi

STATUS[mcps]="done"
