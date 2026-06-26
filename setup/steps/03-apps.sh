#!/bin/bash
# Step 3: Desktop Apps (interactive selection)
# Fixes: U3 (Plaud non-blocking)

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "3/10" "Desktop Apps"

echo ""
echo "  Which tools do you use? (enter numbers separated by spaces, or 'all')"
echo "    1) Obsidian      — Note-taking app"
echo "    2) Plaud Desktop — Meeting recorder (macOS)"
echo ""
read -rp "  > " APP_SELECTION

USE_OBSIDIAN=false
USE_PLAUD=false

if [[ "$APP_SELECTION" == "all" ]]; then
    USE_OBSIDIAN=true
    USE_PLAUD=true
else
    for num in $APP_SELECTION; do
        case "$num" in
            1) USE_OBSIDIAN=true ;;
            2) USE_PLAUD=true ;;
        esac
    done
fi

# Export for later steps
export USE_OBSIDIAN USE_PLAUD

# Obsidian
OBSIDIAN_VAULT_PATH=""
if $USE_OBSIDIAN; then
    if [[ ! -d "/Applications/Obsidian.app" ]]; then
        info "Installing Obsidian..."
        brew install --cask obsidian
    fi
    ok "Obsidian installed"

    # Auto-detect vault path (fixes M5, M6)
    for candidate in "$HOME/Documents/ObsidianVault" "$HOME/ObsidianVault"; do
        if [[ -d "$candidate/.obsidian" ]]; then
            OBSIDIAN_VAULT_PATH="$candidate"
            break
        fi
    done

    if [[ -z "$OBSIDIAN_VAULT_PATH" ]]; then
        # Search broader (fixes M6)
        FOUND_VAULTS=$(find "$HOME" -maxdepth 3 -name ".obsidian" -type d 2>/dev/null \
            | grep -v '/Library/' | grep -v '/node_modules/' | grep -v '/.Trash/' \
            | sed 's|/.obsidian$||' || true)

        if [[ -n "$FOUND_VAULTS" ]]; then
            echo ""
            echo "  Found Obsidian vault(s):"
            local i=1
            while IFS= read -r vault; do
                echo "    $i) $vault"
                i=$((i + 1))
            done <<< "$FOUND_VAULTS"
            echo ""
            read -rp "  Select vault number (or type a path): " VAULT_CHOICE
            if [[ "$VAULT_CHOICE" =~ ^[0-9]+$ ]]; then
                OBSIDIAN_VAULT_PATH=$(echo "$FOUND_VAULTS" | sed -n "${VAULT_CHOICE}p")
            else
                OBSIDIAN_VAULT_PATH="$VAULT_CHOICE"
            fi
        else
            echo ""
            read -rp "  No vault found. Enter your vault path: " OBSIDIAN_VAULT_PATH
        fi
    fi

    if [[ -d "$OBSIDIAN_VAULT_PATH" ]]; then
        ok "Vault found at $OBSIDIAN_VAULT_PATH"
    else
        warn "Path doesn't exist yet — Obsidian MCP will fail until the vault is created"
    fi
    STATUS[obsidian]="enabled"
else
    STATUS[obsidian]="disabled"
fi
export OBSIDIAN_VAULT_PATH

# Plaud Desktop (fixes U3: non-blocking)
if $USE_PLAUD; then
    if [[ ! -d "/Applications/Plaud.app" ]]; then
        info "Installing Plaud Desktop..."
        brew install --cask plaud 2>/dev/null || {
            warn "Plaud not available via brew — install manually from https://plaud.ai"
        }
    fi

    if lsof -i :9229 2>/dev/null | grep -q LISTEN; then
        ok "Plaud Desktop connected (CDP port 9229)"
    else
        warn "Plaud Desktop not running on port 9229"
        info "Open Plaud Desktop and sign in — the MCP will work once it's running"
    fi
    STATUS[plaud]="enabled"
else
    STATUS[plaud]="disabled"
fi
