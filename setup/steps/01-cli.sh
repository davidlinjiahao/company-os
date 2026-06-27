#!/bin/bash
# Step 1: CLI Dependencies
# Fixes: I1 (no anthropic CLI), I2 (bun --trust), P2 (HOMEBREW_NO_AUTO_UPDATE)

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "1/10" "CLI Dependencies"

# Homebrew (prerequisite — can't install for them)
if command -v brew &>/dev/null; then
    ok "Homebrew"
else
    fail "Homebrew not found"
    echo "    Install it first: https://brew.sh"
    echo "    Then re-run ./setup.sh"
    exit 1
fi

# Suppress auto-update for faster installs (fixes P2)
export HOMEBREW_NO_AUTO_UPDATE=1

# git
if command -v git &>/dev/null; then
    ok "git"
else
    info "Installing git..."
    brew install git
    ok "git"
fi

# Python 3.10+
if python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
    ok "Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
else
    info "Installing Python 3.12..."
    brew install python@3.12
    ok "Python 3.12"
fi

# uv
if command -v uv &>/dev/null; then
    ok "uv"
else
    info "Installing uv..."
    brew install uv
    if command -v uv &>/dev/null; then
        ok "uv"
    else
        fail "uv installed but not on PATH. Restart your terminal and re-run ./setup.sh"
        exit 1
    fi
fi

# Node.js + npm
if command -v npm &>/dev/null; then
    ok "Node.js + npm"
else
    info "Installing Node.js..."
    brew install node
    ok "Node.js + npm"
fi

# Bun
if command -v bun &>/dev/null; then
    ok "Bun"
else
    info "Installing Bun..."
    brew install oven-sh/bun/bun
    ok "Bun"
fi

# Claude Code
if command -v claude &>/dev/null; then
    ok "Claude Code $(claude --version 2>/dev/null || echo '')"
else
    info "Installing Claude Code..."
    npm install -g @anthropic-ai/claude-code
    ok "Claude Code"
fi

# qmd (fixes I2: --trust flag for postinstalls)
if command -v qmd &>/dev/null; then
    ok "qmd"
else
    info "Installing qmd..."
    bun install -g --trust github:tobi/qmd
    ok "qmd"
fi

# GitHub CLI
if command -v gh &>/dev/null; then
    ok "GitHub CLI (gh)"
else
    info "Installing GitHub CLI..."
    brew install gh
    ok "GitHub CLI (gh)"
fi

# 1Password CLI (fixes P2: --cask with HOMEBREW_NO_AUTO_UPDATE)
if command -v op &>/dev/null; then
    ok "1Password CLI"
else
    info "Installing 1Password CLI..."
    brew install --cask 1password-cli
    ok "1Password CLI"
fi

STATUS[cli]="done"
