#!/bin/bash
# Step 2: GitHub SSH Key

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "2/10" "GitHub SSH Key"

SSH_KEY="$HOME/.ssh/id_ed25519"

if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    ok "SSH already works with GitHub"
    STATUS[ssh]="done"
else
    # Generate key if missing
    if [[ ! -f "$SSH_KEY" ]]; then
        info "Generating SSH key..."
        mkdir -p "$HOME/.ssh"
        ssh-keygen -t ed25519 -C "company-os-setup" -f "$SSH_KEY" -N ""
        ok "SSH key generated"
    else
        ok "SSH key exists at $SSH_KEY"
    fi

    # Ensure ssh-agent has the key (macOS keychain)
    eval "$(ssh-agent -s)" &>/dev/null
    ssh-add --apple-use-keychain "$SSH_KEY" 2>/dev/null || ssh-add "$SSH_KEY" 2>/dev/null

    # Add to GitHub via gh CLI
    if command -v gh &>/dev/null && gh auth status &>/dev/null; then
        MACHINE_NAME=$(scutil --get ComputerName 2>/dev/null || hostname)
        gh ssh-key add "$SSH_KEY.pub" --title "$MACHINE_NAME (company-os setup)" 2>/dev/null && \
            ok "SSH key added to GitHub" || \
            ok "SSH key already on GitHub"
    else
        warn "gh not authenticated — add your SSH key to GitHub manually:"
        echo "    cat $SSH_KEY.pub"
        echo "    → https://github.com/settings/keys"
    fi

    # Switch this repo's remote from HTTPS to SSH
    CURRENT_REMOTE=$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null || echo "")
    if [[ "$CURRENT_REMOTE" == https://* ]]; then
        git -C "$REPO_DIR" remote set-url origin "git@github.com:${GITHUB_ORG}/${GITHUB_REPO}.git"
        ok "Git remote switched from HTTPS → SSH"
    fi

    STATUS[ssh]="done"
fi
