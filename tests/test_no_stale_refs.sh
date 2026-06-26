#!/bin/bash
# Grep entire repo for stale references to old paths
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0

# Search active files only (exclude upgrades/ playbook docs and .git/)
check_no_ref() {
    local pattern="$1"
    local description="$2"
    # Search all tracked files except those under upgrades/ and tests/ (tests contain the patterns they check for)
    local matches
    matches=$(cd "$REPO_DIR" && git ls-files | grep -v '^upgrades/' | grep -v '^tests/' | xargs grep -l "$pattern" 2>/dev/null || true)
    if [ -z "$matches" ]; then
        echo "  PASS  No active references to $description"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  Found references to $description in:"
        echo "$matches" | sed 's/^/         /'
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Stale Reference Tests ==="
echo ""

check_no_ref 'daemons/' "daemons/ (old daemon location)"
check_no_ref 'configs/' "configs/ (deleted — inlined into .env.tpl)"
check_no_ref 'ross-abundance-' "ross-abundance-* (renamed to upgrades/)"
check_no_ref 'abundance-company' "abundance-company (old org name)"
check_no_ref 'abundance\.company' "abundance.company (private workspace domain)"
check_no_ref 'scripts/setup' "scripts/setup.sh (promoted to root)"

# Check for root-level hooks/ learnings/ tools/ references in active files
# These patterns need word boundary care — we want "hooks/" at start of path, not "upgrades/hooks/"
echo ""
echo "Old root-level directory references:"

for old_dir in hooks learnings tools; do
    matches=$(cd "$REPO_DIR" && git ls-files | grep -v '^upgrades/' | grep -v '^tests/' | xargs grep -En "\"${old_dir}/|'${old_dir}/| ${old_dir}/|^${old_dir}/" 2>/dev/null | grep -v "upgrades/${old_dir}" | grep -v '├──\|└──\|│' || true)
    if [ -z "$matches" ]; then
        echo "  PASS  No active references to root ${old_dir}/"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  Found references to root ${old_dir}/:"
        echo "$matches" | head -5 | sed 's/^/         /'
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "────────────────────────"
echo "  $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
