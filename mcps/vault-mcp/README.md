# vault-mcp

Team knowledge vault access via Claude Code. Exposes the Obsidian vault over HTTPS using a Bun MCP server + ngrok tunnel.

## Two Tools

| Tool | What it does |
|------|-------------|
| `vault_search` | BM25 keyword search — returns titles + snippets |
| `vault_read` | Read full document by `collection/path` |

## For Teammates (one command)

Your team admin sends you a personalized command via Slack DM:

```bash
claude mcp add --transport http \
  --header "Authorization: Bearer <your-personal-token>" \
  -- vault https://<your-vault-domain>/mcp
```

Paste it in terminal, restart Claude Code. Done.

Then ask Claude: *"search the vault for project strategy"*

## For Admins (server setup)

### Prerequisites
- [Bun](https://bun.sh) installed
- [ngrok](https://ngrok.com) installed + authenticated
- qmd index at `~/.cache/qmd/index.sqlite`

### One-time setup

```bash
cd mcps/vault-mcp
bun install

# Create users.json from the example (never commit this)
cp users.example.json users.json
# Edit users.json: add token -> name pairs
# Generate tokens with: openssl rand -hex 16
```

### Install daemon

```bash
bash mcps/vault-mcp/daemon/install.sh
```

This installs a LaunchAgent that starts the server + ngrok tunnel on boot and auto-restarts on crash. The install script validates the generated plist and waits for a health check before reporting success.

### Operations

```bash
# Check daemon status
launchctl list | grep vault-mcp

# Health check
curl http://localhost:3131/health

# View logs
tail -f ~/Library/Logs/company-os-vault-mcp.log

# Restart
launchctl unload ~/Library/LaunchAgents/com.company-os.vault-mcp.plist
launchctl load ~/Library/LaunchAgents/com.company-os.vault-mcp.plist

# Reinstall (regenerates plist from template)
bash mcps/vault-mcp/daemon/install.sh
```

## Access Control

- Each teammate has a unique bearer token (maps to their name in `users.json`)
- Collections are configured via `VAULT_COLLECTIONS` env var
- Every search and read is logged: `{"ts":"...","user":"alice","tool":"vault_search","query":"..."}`

## Files

```
vault-mcp/
├── server.ts          # Bun MCP server (~120 lines)
├── package.json       # Dependencies
├── users.example.json # Token map template (copy to users.json, never commit)
├── daemon/
│   ├── install.sh     # LaunchAgent installer (validates + health checks)
│   ├── run.sh         # Daemon runner (server + ngrok, called by launchd)
│   └── com.company-os.vault-mcp.plist.template
├── .gitignore         # Excludes users.json
└── README.md
```
