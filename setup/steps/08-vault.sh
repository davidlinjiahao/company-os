#!/bin/bash
# Step 8: Vault MCP Team Configuration

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "8/10" "Vault MCP"

if [[ -z "${VAULT_NGROK_DOMAIN:-}" ]]; then
    info "No VAULT_NGROK_DOMAIN configured — skipping vault MCP"
    STATUS[vault]="skipped"
else
    echo ""
    echo "  Vault MCP auth method:"
    echo "    1) Google OAuth (recommended — sign in with your company Google account)"
    echo "    2) Legacy bearer token"
    echo ""
    read -rp "  > " AUTH_METHOD

    if [[ "$AUTH_METHOD" == "2" ]]; then
        # Legacy token flow
        TEAM_JSON="$REPO_DIR/mcps/vault-mcp/team.json"
        if [[ -f "$TEAM_JSON" ]]; then
            echo ""
            echo "  Who are you on the team?"
            python3 -c "import json,sys; [print(f'    {i+1}) {k}') for i,k in enumerate(json.load(open(sys.argv[1])).keys())]" "$TEAM_JSON"
            echo ""
            read -rp "  > " TEAM_NUM

            TEAM_NAME=$(python3 -c "import json,sys; keys=list(json.load(open(sys.argv[1])).keys()); print(keys[int(sys.argv[2])-1])" "$TEAM_JSON" "$TEAM_NUM" 2>/dev/null)

            if [[ -n "$TEAM_NAME" ]]; then
                VAULT_TOKEN=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$TEAM_JSON" "$TEAM_NAME")

                claude mcp remove vault 2>/dev/null || true
                claude mcp add --transport http -s user \
                    --header "Authorization: Bearer $VAULT_TOKEN" \
                    -- vault "https://${VAULT_NGROK_DOMAIN}/mcp"

                ok "Vault MCP configured with legacy token (logged in as $TEAM_NAME)"
                STATUS[vault]="$TEAM_NAME"
            else
                fail "Invalid selection — skipping vault MCP"
                STATUS[vault]="skipped"
            fi
        else
            fail "team.json not found at $TEAM_JSON"
            STATUS[vault]="error"
        fi
    else
        # Google OAuth flow — no token needed, Claude Code handles auth automatically
        claude mcp remove vault 2>/dev/null || true
        claude mcp add --transport http -s user \
            -- vault "https://${VAULT_NGROK_DOMAIN}/mcp"

        ok "Vault MCP configured with Google OAuth"
        info "You'll be prompted to sign in with your company Google account on first use"
        STATUS[vault]="oauth"
    fi
fi
