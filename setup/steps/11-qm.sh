#!/bin/bash
# Optional: install the QM CLI so this repo can deploy a company agent.
# Never runs `qm up`. Cloud deploy is an explicit operator step (it bills).
#
# QM is https://github.com/yc-software/qm (MIT), consumed as the npm package
# @yc-software/qm pinned in package.json — the same pattern as a stock
# `qm init` deployment directory.

[[ -z "${REPO_DIR:-}" ]] && { source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/colors.sh"; source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/utils.sh"; REPO_DIR="$(detect_repo_dir)"; }

header "optional" "Company agent (qm)"

ensure_path

if [[ ! -f "$REPO_DIR/package.json" || ! -f "$REPO_DIR/qm.config.jsonc" ]]; then
    warn "qm scaffold missing — skip"
    STATUS[qm]="skipped"
    return 0 2>/dev/null || exit 0
fi

# Node 24+ is the package engine. Homebrew node is usually new enough.
if ! command -v node >/dev/null 2>&1; then
    warn "Node.js not on PATH — re-run after step 01-cli"
    STATUS[qm]="skipped"
    return 0 2>/dev/null || exit 0
fi
node_major=$(node -p "process.versions.node.split('.')[0]")
if [[ "$node_major" -lt 24 ]]; then
    warn "Node $node_major < 24 (qm requires Node 24+). brew install node && re-run."
    STATUS[qm]="skipped"
    return 0 2>/dev/null || exit 0
fi
ok "Node $(node -v)"

# Stamp the operator's slug into the official scaffold placeholders.
# `your-company` is the public-template default from `qm init --org your-company`.
slug="${COMPANY_SLUG:-your-company}"
if [[ "$slug" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] && [[ "$slug" != "your-company" ]]; then
    python3 - "$REPO_DIR" "$slug" "${QM_TARGET:-fly}" "${QM_REGION:-sjc}" "${QM_FLY_ORG:-personal}" <<'PY' || { warn "could not stamp qm config"; true; }
import json, pathlib, re, sys
root, slug, target, region, fly_org = sys.argv[1:6]
# package.json
pkg_path = pathlib.Path(root) / "package.json"
pkg = json.loads(pkg_path.read_text())
pkg["name"] = f"{slug}-qm-deployment"
pkg_path.write_text(json.dumps(pkg, indent=2) + "\n")
# slack description only — bot display name stays "qm"
manifest = pathlib.Path(root) / "slack-app-manifest.yml"
text = manifest.read_text()
text = re.sub(r"qm workspace agent for [^\n]+", f"qm workspace agent for {slug}", text, count=1)
manifest.write_text(text)
# qm.config.jsonc — replace the init placeholders, not arbitrary substrings
cfg_path = pathlib.Path(root) / "qm.config.jsonc"
cfg = cfg_path.read_text()
cfg = cfg.replace('"orgId": "your-company"', f'"orgId": "{slug}"')
cfg = cfg.replace('"appPrefix": "your-company"', f'"appPrefix": "{slug}"')
cfg = cfg.replace("https://your-company-portal.fly.dev", f"https://{slug}-portal.fly.dev")
cfg = cfg.replace('"S3_BUCKET": "your-company-data"', f'"S3_BUCKET": "{slug}-data"')
cfg = re.sub(r'"target": "(docker|fly|aws)"', f'"target": "{target}"', cfg, count=1)
cfg = re.sub(r'"region": "[a-z0-9]+"', f'"region": "{region}"', cfg, count=1)
cfg = re.sub(r'"flyOrg": "[^"]+"', f'"flyOrg": "{fly_org}"', cfg, count=1)
cfg_path.write_text(cfg)
print("stamped")
PY
    ok "qm config stamped for $slug"
else
    info "qm config left at placeholder orgId=your-company — edit qm.config.jsonc before deploy"
fi

cd "$REPO_DIR"
if [[ -f package-lock.json ]]; then
    npm ci --ignore-scripts >/dev/null || { warn "npm ci failed"; STATUS[qm]="error"; return 0 2>/dev/null || exit 0; }
else
    npm install --ignore-scripts >/dev/null || { warn "npm install failed"; STATUS[qm]="error"; return 0 2>/dev/null || exit 0; }
fi
ok "npm install @yc-software/qm"

if [[ ! -f "$REPO_DIR/.env" ]]; then
    info "no .env yet — run: cd $REPO_DIR && npm exec qm -- setup"
fi

if npm exec qm -- check >/dev/null 2>&1; then
    ok "qm check"
    STATUS[qm]="installed"
else
    warn "qm check needs secrets or provider login — run: npm exec qm -- setup"
    STATUS[qm]="installed-unchecked"
fi

info "Deploy is manual and bills your cloud: npm exec qm -- setup && npm exec qm -- up"
info "Guide: deployment.md  ·  upstream: https://github.com/yc-software/qm"
