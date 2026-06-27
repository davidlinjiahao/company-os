#!/usr/bin/env bash
# Deploy decide-app: sync repos + trigger Vercel deploy
# Usage: ./scripts/deploy.sh [commit message]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DECIDE_APP_DIR="${DECIDE_APP_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
COMPANY_OS_DIR="${COMPANY_OS_DIR:-$(cd "$SCRIPT_DIR/../../../.." && pwd)}"
SUBDIRECTORY="skills/decide/decision-app"
DEPLOY_HOOK="${VERCEL_DEPLOY_HOOK:?Set VERCEL_DEPLOY_HOOK env var (Vercel deploy hook URL)}"

echo "=== Syncing decide-app → company-os ==="
rsync -av --delete \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='.vercel' \
  "$DECIDE_APP_DIR/" "$COMPANY_OS_DIR/$SUBDIRECTORY/"

echo ""
echo "=== Pushing decide-app ==="
cd "$DECIDE_APP_DIR"
git push origin main 2>&1 || echo "(decide-app already up to date)"

echo ""
echo "=== Pushing company-os ==="
cd "$COMPANY_OS_DIR"
if git diff --quiet "$SUBDIRECTORY/" 2>/dev/null && git diff --cached --quiet "$SUBDIRECTORY/" 2>/dev/null; then
  echo "(no changes to commit)"
else
  git add "$SUBDIRECTORY/"
  MSG="${1:-sync decide-app to company-os}"
  git commit -m "$MSG

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
fi
git push origin main 2>&1 || echo "(company-os already up to date)"

# Wait for GitHub to process the push before triggering deploy
echo ""
echo "=== Waiting 3s for GitHub to process push ==="
sleep 3

# Verify the push landed by checking remote HEAD matches local
LOCAL_SHA=$(git rev-parse HEAD)
REMOTE_SHA=$(git ls-remote origin HEAD | cut -f1)
if [ "$LOCAL_SHA" != "$REMOTE_SHA" ]; then
  echo "WARNING: Remote HEAD ($REMOTE_SHA) != local HEAD ($LOCAL_SHA)"
  echo "Waiting 5 more seconds..."
  sleep 5
fi

echo ""
echo "=== Triggering Vercel deploy ==="
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$DEPLOY_HOOK")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
  echo "Deploy triggered successfully (HTTP $HTTP_STATUS)"
  echo "Local commit: $LOCAL_SHA"
  echo "Check: # Check your Vercel dashboard"
else
  echo "Deploy hook returned HTTP $HTTP_STATUS — falling back to CLI deploy"
  vercel --prod --yes 2>&1
fi

echo ""
echo "=== Done ==="
