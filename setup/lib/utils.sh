#!/bin/bash
# Shared utilities for setup scripts

# Ensure core system paths are available (fixes T1, T2, T3, T5)
ensure_path() {
    export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$HOME/.local/bin:$PATH"
    export PATH="$PATH:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null)" || true
}

# Find absolute path to uv (fixes T5, M1)
resolve_uv() {
    local uv_path
    uv_path=$(command -v uv 2>/dev/null || echo "")
    if [[ -z "$uv_path" ]]; then
        for p in /opt/homebrew/bin/uv "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
            [[ -x "$p" ]] && { echo "$p"; return; }
        done
        echo "uv"  # fallback
    else
        echo "$uv_path"
    fi
}

# Create symlink with backup (from v1 pattern)
safe_symlink() {
    local target="$1"
    local link="$2"

    if [[ -L "$link" && "$(readlink "$link")" == "$target" ]]; then
        return 0  # already correct
    fi

    # Backup existing file/link
    if [[ -e "$link" || -L "$link" ]]; then
        mv "$link" "${link}.bak.$(date +%s)"
    fi

    ln -sf "$target" "$link"
}

# Auto-detect REPO_DIR from any script location
detect_repo_dir() {
    local script_path="${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}"
    local script_dir
    script_dir="$(cd "$(dirname "$script_path")" && pwd)"

    # Walk up to find CLAUDE.md (repo root marker)
    local dir="$script_dir"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/CLAUDE.md" && -d "$dir/mcps" ]]; then
            echo "$dir"
            return
        fi
        dir="$(dirname "$dir")"
    done

    # Fallback: assume setup/ is one level below repo root
    echo "$(cd "$script_dir/.." && pwd)"
}
