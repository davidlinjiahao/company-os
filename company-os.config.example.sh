# company-os.config.example.sh
# Copy to company-os.config.sh and fill in your values.

COMPANY_NAME="Your Company"
COMPANY_SLUG="your-company"           # lowercase, used in plist labels, file paths
COMPANY_DESCRIPTION="What your company does"
TEAM_MEMBERS="Alice,Bob,Carol"
TEAM_TECH_STACK="Python, TypeScript"

# GitHub
GITHUB_ORG="your-org"
GITHUB_REPO="company-os"

# 1Password (optional — skip step if empty)
OP_VAULT_NAME="Your Company"

# Vault MCP (optional — skip step if empty)
VAULT_NGROK_DOMAIN=""                 # e.g. "vault.yourco.ngrok.dev"
VAULT_COLLECTIONS="team-vault"          # comma-separated, must match qmd index

# Decision app
DECIDE_APP_TITLE="Decide"

# Company agent (qm) — optional. setup.sh installs the CLI; it never deploys.
# Fill these, then from the repo root: npm exec qm -- setup && npm exec qm -- up
# Slug becomes Fly app prefix and portal hostname (<slug>-portal.fly.dev).
# It must be a lowercase DNS label, globally unique on Fly.
QM_TARGET="fly"                 # fly | aws | docker
QM_REGION="sjc"
QM_FLY_ORG="personal"           # Fly organization slug (Fly's default is "personal")
