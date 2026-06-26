#!/bin/bash
# Step 5: Symlink Skills + Clean Stale Hooks
# Fixes: H1, H2, H3 (stale hook cleanup)

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "5/10" "Symlink Skills"

mkdir -p "$HOME/.claude"

SKILLS_LINK="$HOME/.claude/skills"
SKILLS_TARGET="$REPO_DIR/skills"

if [[ -L "$SKILLS_LINK" && "$(readlink "$SKILLS_LINK")" == "$SKILLS_TARGET" ]]; then
    ok "Skills already linked"
else
    safe_symlink "$SKILLS_TARGET" "$SKILLS_LINK"
    ok "Skills linked: ~/.claude/skills → $SKILLS_TARGET"
fi

# Count skills
SKILL_COUNT=$(find "$SKILLS_TARGET" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ')
STATUS[skills]="$SKILL_COUNT commands"

# Clean stale hook scripts (fixes H1, H2, H3)
for script in rebuild-session-index.sh quality-gates.sh; do
    if [[ -f "$HOME/.claude/scripts/$script" ]]; then
        rm -f "$HOME/.claude/scripts/$script"
        info "Removed stale hook: $script"
    fi
done
