#!/bin/bash
# Company OS — Modular Setup Entrypoint
# Usage: ./setup/init.sh [--verify]
#
# Runs all setup steps in order, or just verification with --verify.

set -euo pipefail

SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SETUP_DIR/.." && pwd)"
export REPO_DIR SETUP_DIR

# Source company config
CONFIG_FILE="$REPO_DIR/company-os.config.sh"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Copy company-os.config.example.sh → company-os.config.sh and fill in your values."
    exit 1
fi
source "$CONFIG_FILE"
export COMPANY_NAME COMPANY_SLUG GITHUB_ORG GITHUB_REPO OP_VAULT_NAME VAULT_NGROK_DOMAIN VAULT_COLLECTIONS

# Bootstrap PATH before anything else (fixes T1, T2, T3)
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$HOME/.local/bin:$PATH"
export PATH="$PATH:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null)" || true

# Source shared libraries
source "$SETUP_DIR/lib/colors.sh"
source "$SETUP_DIR/lib/utils.sh"

# --verify mode: run only health checks
if [[ "${1:-}" == "--verify" ]]; then
    source "$SETUP_DIR/steps/09-verify.sh"
    exit $?
fi

# Track what was installed/configured for summary
declare -A STATUS
export STATUS

echo ""
echo -e "${BOLD}Company OS Setup${RESET}"
echo -e "${DIM}────────────────────────────────────${RESET}"

# Run each step in order
source "$SETUP_DIR/steps/01-cli.sh"
source "$SETUP_DIR/steps/02-ssh.sh"
source "$SETUP_DIR/steps/03-apps.sh"
source "$SETUP_DIR/steps/04-1password.sh"
source "$SETUP_DIR/steps/05-skills.sh"
source "$SETUP_DIR/steps/06-mcps.sh"
source "$SETUP_DIR/steps/07-daemon.sh"
source "$SETUP_DIR/steps/08-vault.sh"
source "$SETUP_DIR/steps/09-verify.sh" || true  # don't fail setup on verify issues
source "$SETUP_DIR/steps/10-summary.sh"
