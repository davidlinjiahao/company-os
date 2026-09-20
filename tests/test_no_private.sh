#!/usr/bin/env bash
# Fail if tracked files contain company, personal, or secret material.
# This repo is a public template.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
PASS=0
FAIL=0

check_no() {
    local pattern="$1"
    local description="$2"
    local matches
    matches=$(git ls-files -z | xargs -0 grep -lE "$pattern" 2>/dev/null || true)
    # allow this test file to mention the rule, not the payload
    matches=$(printf '%s\n' "$matches" | grep -v '^tests/test_no_private.sh$' || true)
    if [ -z "$matches" ]; then
        echo "  PASS  no $description"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  found $description in:"
        echo "$matches" | sed 's/^/         /'
        FAIL=$((FAIL + 1))
    fi
}

echo "=== No private / company-specific material in tracked files ==="
echo ""

check_no '/Users/david' 'home-directory paths'
check_no 'jiahao' 'personal handle'
check_no 'aligned\.company' 'a private company email domain'
check_no 'aligned-portal' 'a private portal hostname'
check_no 'aligned-sandboxes' 'a private sandbox app'
check_no 'aligned-data' 'a private object-storage bucket'
check_no 'w76geopd' 'a private database cluster id'
check_no 'sk-ant-[A-Za-z0-9_-]{8,}' 'Anthropic-shaped live key'
check_no 'ghp_[A-Za-z0-9]{20,}' 'GitHub PAT'
check_no 'github_pat_[A-Za-z0-9_]{20,}' 'GitHub fine-grained PAT'
check_no 'BEGIN (OPENSSH|RSA|EC) PRIVATE KEY' 'private key block'

# Former company name, assembled so this file is not itself a hit.
_ab="abun""dance"
check_no "$_ab" 'former company name'

echo ""
echo "Forbidden tracked paths:"
for p in \
    mcps/vault-mcp/users.json \
    mcps/vault-mcp/team.json \
    mcps/vault-mcp/emails.json \
    .env \
    company-os.config.sh \
    skills/onboard/
do
    if git ls-files --error-unmatch "$p" >/dev/null 2>&1; then
        echo "  FAIL  $p is tracked"
        FAIL=$((FAIL + 1))
    else
        echo "  PASS  $p not tracked"
        PASS=$((PASS + 1))
    fi
done

echo ""
echo "────────────────────────"
echo "  $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
