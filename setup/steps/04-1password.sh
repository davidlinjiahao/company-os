#!/bin/bash
# Step 4: 1Password Service Account + Secret Injection
# Fixes: P1 (interactive prompt), D3 (transcript gate API key)

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "4/10" "1Password & Team Secrets"

SA_TOKEN_FILE="$HOME/.company-os-sa-token"

# Check for existing token
if [[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
    ok "OP_SERVICE_ACCOUNT_TOKEN already set"
elif [[ -f "$SA_TOKEN_FILE" ]]; then
    export OP_SERVICE_ACCOUNT_TOKEN="$(cat "$SA_TOKEN_FILE")"
    ok "Loaded service account token from $SA_TOKEN_FILE"
else
    echo ""
    info "1Password service account is used for team secrets."
    info "No 1Password desktop app needed — just the CLI + a token."
    echo ""
    echo "  A 1Password service account token is needed to pull team secrets."
    echo "  Ask a team lead for the token (starts with ops_...)."
    echo ""
    read -rsp "  Paste token (hidden): " SA_TOKEN_INPUT
    echo ""
    if [[ -z "$SA_TOKEN_INPUT" ]]; then
        warn "No token provided — skipping 1Password setup"
        warn "Re-run ./setup.sh after getting the token from your team"
        STATUS[onepassword]="skipped"
        STATUS[secrets]="skipped"
        return 0 2>/dev/null || exit 0
    else
        export OP_SERVICE_ACCOUNT_TOKEN="$SA_TOKEN_INPUT"
        echo "$SA_TOKEN_INPUT" > "$SA_TOKEN_FILE"
        chmod 600 "$SA_TOKEN_FILE"
        ok "Token saved to $SA_TOKEN_FILE (chmod 600)"
    fi
fi

# Verify the token works
if [[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
    if op vault list --format=json 2>/dev/null | python3 -c "import sys,json; vaults=json.load(sys.stdin); print(any(v['name']==sys.argv[1] for v in vaults))" "$OP_VAULT_NAME" 2>/dev/null | grep -q True; then
        ok "1Password service account verified (${OP_VAULT_NAME} vault accessible)"
        STATUS[onepassword]="done"
    else
        fail "Service account token doesn't have access to '${OP_VAULT_NAME}' vault"
        warn "Check with your team lead — the token may be expired or misconfigured"
        STATUS[onepassword]="error"
        STATUS[secrets]="skipped"
        return 0 2>/dev/null || exit 0
    fi
fi

# Pull secrets
if [[ "${STATUS[onepassword]:-}" == "done" ]]; then
    info "Pulling secrets from 1Password..."
    # Substitute YOUR_VAULT_NAME with the configured vault name before injecting
    ENV_TPL_RESOLVED=$(mktemp)
    trap 'rm -f "$ENV_TPL_RESOLVED"' RETURN
    OP_VAULT_ESCAPED=$(printf '%s\n' "$OP_VAULT_NAME" | sed 's/[&/\]/\\&/g')
    sed "s/YOUR_VAULT_NAME/${OP_VAULT_ESCAPED}/g" "$REPO_DIR/.env.tpl" > "$ENV_TPL_RESOLVED"
    op inject -i "$ENV_TPL_RESOLVED" -o "$HOME/.company-os.env" --force
    ok "Secrets written to ~/.company-os.env"

    # Transcript gate env (fixes D3)
    mkdir -p "$HOME/.claude/transcript_gate"
    op inject -i "$ENV_TPL_RESOLVED" -o "$HOME/.claude/transcript_gate/env" --force
    ok "Transcript gate API key written"

    SECRET_COUNT=$(grep -c '=' "$HOME/.company-os.env" 2>/dev/null || echo "0")
    STATUS[secrets]="$SECRET_COUNT keys"

    # Add source line to .zshrc
    ZSHRC="$HOME/.zshrc"
    SOURCE_LINE='source "$HOME/.company-os.env"'
    if [[ -f "$ZSHRC" ]] && grep -qF '.company-os.env' "$ZSHRC"; then
        ok "~/.zshrc already sources secrets"
    else
        echo "" >> "$ZSHRC"
        echo '# Company OS team secrets (pulled from 1Password)' >> "$ZSHRC"
        echo "$SOURCE_LINE" >> "$ZSHRC"
        ok "Added source line to ~/.zshrc"
    fi
fi
