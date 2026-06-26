---
name: setup
description: One-command onboarding for new engineers. Calls modular bash scripts — no improvisation needed.
user-invocable: true
disable-model-invocation: false
argument-hint: "[--verify]"
allowed-tools: Bash, Read, AskUserQuestion, mcp__notion-enhanced__get_self, mcp__obsidian__get_structure, mcp__plaud__check_connection, mcp__vault__vault_search
---

# /setup - Company OS Onboarding

This skill calls the modular bash scripts in `setup/steps/`. Each step is a standalone script that can be re-run individually.

**IMPORTANT:** Use the exact commands below. Do NOT improvise executable names, paths, or flags.

## `/setup --verify` Mode

If the user runs `/setup --verify` or `/setup verify`, SKIP all setup steps and ONLY run MCP verification:

**Notion** (always):
```
Call mcp__notion-enhanced__get_self()
```
- PASS if it returns a bot user object
- FAIL → "Shared token may have expired — ask your team admin"

**Obsidian** (if `mcp__obsidian__*` tools are available):
```
Call mcp__obsidian__get_structure(max_depth=1)
```
- PASS if it returns the vault folder tree
- FAIL → "Vault path may be wrong — re-run /setup to reconfigure"

**Plaud** (if `mcp__plaud__*` tools are available):
```
Call mcp__plaud__check_connection()
```
- PASS if connected
- FAIL → "Make sure Plaud Desktop is open and you're signed in"

**Vault** (if `mcp__vault__*` tools are available):
```
Call mcp__vault__vault_search(query="test")
```
- PASS if it returns results or empty list
- FAIL → "The vault server may be down — try again later"

Display results as a table, then stop.

## Full Setup Mode

**Announce at start:** "Setting up Company OS. I'll run the setup scripts and ask you a few questions along the way."

### Step 1: CLI Dependencies (automatic)

Run the CLI install step. This checks and installs: Homebrew, git, Python, uv, Node, Bun, Claude Code, qmd, gh, 1Password CLI.

```bash
REPO_DIR="$(cd "$(dirname "$(readlink -f ~/.claude/skills)")" && pwd)"
bash "$REPO_DIR/setup/steps/01-cli.sh"
```

If `REPO_DIR` can't be resolved from the skills symlink, ask the user where the repo is cloned.

### Step 2: GitHub SSH Key (automatic)

```bash
bash "$REPO_DIR/setup/steps/02-ssh.sh"
```

### Step 3: Desktop Apps (AskUserQuestion)

Use AskUserQuestion with **multiSelect: true**:

```
Question: "Which tools do you use?"
Header: "Apps"
Options:
  - label: "Obsidian"
    description: "Note-taking app — enables the Obsidian MCP for vault access"
  - label: "Plaud Desktop"
    description: "Meeting recorder — enables Plaud MCP for transcripts"
```

Based on their selection, set environment variables and run app setup:

```bash
export USE_OBSIDIAN=true   # or false
export USE_PLAUD=true      # or false
```

**If Obsidian selected**, find the vault path:
1. Check `~/Documents/ObsidianVault` and `~/ObsidianVault`
2. If not found, search:
   ```bash
   find "$HOME" -maxdepth 3 -name ".obsidian" -type d 2>/dev/null | grep -v '/Library/' | grep -v '/node_modules/' | sed 's|/.obsidian$//'
   ```
3. Present found vaults via AskUserQuestion (up to 4 options)
4. If none found, ask user to type the path

```bash
export OBSIDIAN_VAULT_PATH="/path/to/vault"
```

**If Plaud selected**, check if Plaud Desktop is running:
```bash
lsof -i :9229 2>/dev/null | grep -q LISTEN && echo "RUNNING" || echo "NOT_RUNNING"
```
If not running, warn: "Plaud Desktop needs to be open and signed in. The MCP will work once it's running."

Do NOT block setup waiting for Plaud Desktop.

### Step 4: 1Password (interactive — delegates to script)

The script handles token prompting, validation, and secret injection interactively:

```bash
source "$REPO_DIR/setup/lib/colors.sh"
source "$REPO_DIR/setup/lib/utils.sh"
source "$REPO_DIR/company-os.config.sh"
export REPO_DIR OP_VAULT_NAME
declare -A STATUS
bash "$REPO_DIR/setup/steps/04-1password.sh"
```

If the user doesn't have a token yet, the script will skip gracefully. They can re-run later.

### Step 5: Symlink Skills (automatic)

```bash
bash "$REPO_DIR/setup/steps/05-skills.sh"
```

### Step 6: Install MCPs (automatic)

This is the critical step. Run it with the env vars from Step 3:

```bash
export USE_OBSIDIAN USE_PLAUD OBSIDIAN_VAULT_PATH REPO_DIR
bash "$REPO_DIR/setup/steps/06-mcps.sh"
```

**DO NOT** modify MCP commands. The script uses absolute `uv` paths and correct executable names.

### Step 7: Plaud Daemon (AskUserQuestion, if Plaud selected)

Only ask if Plaud was selected:

```
Question: "Install the plaud-sync background daemon? Syncs transcripts every 30 min."
Header: "Daemon"
Options:
  - label: "Yes, install it"
    description: "Runs as a macOS LaunchAgent in the background"
  - label: "Skip"
    description: "Install later with: bash mcps/plaud-mcp/daemon/install.sh"
```

If yes:
```bash
bash "$REPO_DIR/mcps/plaud-mcp/daemon/install.sh"
```

### Step 8: Vault MCP (interactive — delegates to script)

The script handles auth method selection (OAuth vs legacy token), team member selection, and MCP configuration interactively:

```bash
source "$REPO_DIR/setup/lib/colors.sh"
source "$REPO_DIR/setup/lib/utils.sh"
source "$REPO_DIR/company-os.config.sh"
export REPO_DIR VAULT_NGROK_DOMAIN
declare -A STATUS
bash "$REPO_DIR/setup/steps/08-vault.sh"
```

If `VAULT_NGROK_DOMAIN` is not configured, the script skips automatically.

### Step 9: Summary

Print status table:

```
Company OS Setup Complete!

CLI Tools:     brew, git, python, uv, bun, node, gh, claude, qmd
SSH Key:       configured for GitHub
1Password:     [X keys pulled / skipped]
Skills:        [N] commands linked
---
Notion:        enabled (shared token)
Obsidian:      [enabled / disabled]
Plaud:         [enabled / disabled]
Plaud Daemon:  [running / skipped / n/a]
Vault:         [logged in as X / not configured]
```

Then tell the user:
> **Restart Claude Code** (MCPs load on session start), then run `/setup --verify` to test all MCP connections.
