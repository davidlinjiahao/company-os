# Company OS

Any new employee can set up this repo and become a Claude Code power user on day one.

## Setup (5 minutes)

**Prerequisites:** Install [Homebrew](https://brew.sh) if you don't have it.

**Then run these 3 commands:**

```bash
brew install gh && gh auth login
gh repo clone your-org/company-os ~/company-os
~/company-os/setup.sh
```

That's it. `setup.sh` handles everything: CLI tools, SSH keys, 1Password secrets,
skills, MCPs, daemon setup, and the optional company-agent CLI. It asks you a few
questions along the way.

After setup finishes, start Claude Code:
```bash
cd ~/company-os && claude
```

To verify everything works, run `/setup --verify` in Claude Code.

### How setup works

```mermaid
flowchart LR
    A[New engineer] --> B[./setup.sh]
    B --> C[CLI tools]
    B --> D[SSH key + GitHub]
    B --> E[1Password secrets]
    B --> F[Symlink skills]
    B --> G[MCPs configured]
    G --> G1[Notion]
    G --> G2[Obsidian]
    G --> G3[Plaud]
    G --> G4[Vault]
```

### Re-running individual steps

Each step is a standalone script you can run independently:

```bash
bash ~/company-os/setup/steps/01-cli.sh      # CLI tools only
bash ~/company-os/setup/steps/06-mcps.sh      # MCPs only
bash ~/company-os/setup/steps/09-verify.sh    # Health checks only
~/company-os/setup.sh --verify                # Same as 09-verify.sh
```

---

## What You Get

Company OS is a shared repo that turns every engineer into a 10x Claude Code user. After setup, your machine has:

- **12 slash commands** — `/setup` for onboarding, `/build` to ship features, `/decide` for structured decisions, `/search` for deep research, `/eval` for testing and security, and more
- **4 MCP servers** — Notion integration, git-aware Obsidian vault, Plaud transcripts, team knowledge vault
- **Shared CLAUDE.md** — company context, coding standards, and safety rules that every Claude session reads
- **Automatic SSH key setup** — generates SSH keys and uploads them to GitHub
- **Optional company agent** — this repo is a [QM](https://github.com/yc-software/qm) deployment directory (Y Combinator, MIT). Same install path as `qm init`: pin `@yc-software/qm`, fill `.env`, `qm up`. Setup installs the CLI. It never deploys (that bills your cloud).

---

## Optional: company agent (QM)

**Agent:** if you were asked to install or deploy this (including Slack and
channels), read `AGENTS.md`, then `.codex/skills/company-os-deploy/SKILL.md`.
Do not run `qm init`. Do not copy another team's `.env` or Fly apps.

[QM](https://github.com/yc-software/qm) is the open-source multiplayer agent harness
from Y Combinator: Slack + web, one scoped agent per person and per channel. This
repository **is** a QM deployment directory. The runtime is the published npm
package, not a fork of the source tree.

```bash
# 1. Local setup already ran `npm ci` (or run it now)
cd ~/company-os && npm ci

# 2. Fill secrets interactively (generates signing keys; does not deploy)
npm exec qm -- setup

# 3. Validate, then deploy to YOUR Fly or AWS account
npm exec qm -- check
npm exec qm -- plan          # dry-run
npm exec qm -- up            # bills: always-on machines + Postgres + object storage + model tokens
```

Before `up`, edit `qm.config.jsonc`: `orgId`, `appPrefix`, `publicUrl`, `flyOrg`,
`region`. They default to the placeholder `your-company`. App names like
`<prefix>-core` must be free on Fly. `setup.sh` stamps these from
`COMPANY_SLUG` in `company-os.config.sh` when that slug is not the placeholder.

`skills/` is mounted into the agent (`qm.config.jsonc` → `skills: ["skills"]`),
so the company agent loads this repo's slash-command pack with no private git
token. Full operator workflow: `deployment.md` and `.codex/skills/deploy-qm/`.

Do not copy another team's `.env`, Fly app names, or bucket names.

Slack bot + channels (agent-runnable): `.codex/skills/company-os-deploy/references/channels.md`.
Required proof: invite the bot to `#agent-test`, mention it, get a reply.
Optional: `#decisions` (for `/decide`), `#general` if they want the bot there.
No unsolicited posts. No standing orders unless the operator asks.

---

## Skills (Slash Commands)

Type these in any Claude Code session. Each runs a specialized workflow.

| Skill | Command | What It Does |
|---|---|---|
| **setup** | `/setup` | One-command onboarding — interactive setup through Claude Code's UI |
| **build** | `/build [feature]` | Dispatcher: acceptance committed before code, loop until green |
| **decide** | `/decide [question]` | Ten principles, optional three-model panel, local ledger |
| **eval** | `/eval [component]` | Run evaluation suite on MCPs, agents, or skills. Also: `/eval secure` for security audits |
| **focus** | `/focus [brain dump]` | Paste messy thoughts, get a prioritized action plan |
| **pmf** | `/pmf questions\|log` | Customer-discovery loop (past-behaviour questions + quote-backed log) |
| **explain** | `/explain [topic]` | Turn any topic or document into a clear, visual explainer PDF |
| **legal** | `/legal [contract]` | Redline a contract → tracked-changes .docx + plain-English summary PDF |
| **source** | `/source [role]` | Turn a hiring need into a ranked A-grade candidate list |
| **search** | `/search [topic]` | Deep research: vault + knowledge graph + web + Reddit/X |
| **sync** | `/sync [source]` | Sync Notion or Plaud data to the vault |
| **learn** | `/learn [topic]` | Claude Code best practices reference |

### Daily workflow

```mermaid
flowchart LR
    A[Engineer types /command] --> B[Skill activates]
    B --> C{MCPs bridge to...}
    C --> D[Notion]
    C --> E[Obsidian]
    C --> F[Plaud]
    C --> G[Vault]
```

---

## MCPs (Model Context Providers)

| Server | What It Does |
|---|---|
| **notion** | Read/write Notion pages and databases. Full property type support. |
| **obsidian** | Read/write Obsidian vault files with git-aware sync. Auto-pulls before reads, auto-commits and pushes after writes. |
| **plaud** | Access Plaud meeting transcripts and summaries in real-time via Plaud Desktop. |
| **vault** | Search and read the team knowledge vault (shared across all engineers). |

### Data flow

```mermaid
flowchart TD
    subgraph Capture
        P[Plaud] --> T[Transcripts]
        G[Granola] --> T
    end
    subgraph Store
        T --> O[Obsidian vault]
        D["/decide"] --> N[Notion]
        D --> O
        R["/search"] --> V[Team vault]
    end
```

---

## Repo Structure

```
company-os/
├── CLAUDE.md              # Company instructions every Claude session reads
├── README.md              # This file
├── setup.sh               # Thin wrapper → setup/init.sh
├── setup/                 # Modular setup scripts
│   ├── init.sh            # Entrypoint: sources libs, runs steps in order
│   ├── verify.sh          # Standalone shortcut for health checks
│   ├── lib/
│   │   ├── colors.sh      # Color codes + output helpers
│   │   └── utils.sh       # resolve_uv, safe_symlink, ensure_path
│   └── steps/
│       ├── 01-cli.sh      # CLI tools (brew, git, python, uv, node, bun, etc.)
│       ├── 02-ssh.sh      # SSH key + GitHub upload
│       ├── 03-apps.sh     # Desktop apps (Obsidian, Plaud)
│       ├── 04-1password.sh # Service account token + secret injection
│       ├── 05-skills.sh   # Symlink skills + clean stale hooks
│       ├── 06-mcps.sh     # Install MCPs (absolute uv path)
│       ├── 07-daemon.sh   # Plaud sync LaunchAgent
│       ├── 08-vault.sh    # Vault MCP team selection
│       ├── 09-verify.sh   # Health checks (standalone)
│       ├── 10-summary.sh  # Final status table
│       └── 11-qm.sh       # Install QM CLI (never deploys)
├── package.json           # pins @yc-software/qm
├── qm.config.jsonc        # QM deployment config (placeholders only)
├── deployment.md          # QM operator workflow (from `qm init`)
├── .env.example           # QM secret catalog (names only)
├── .env.tpl               # 1Password secret template
├── skills/                # 12 slash commands
│   ├── setup/             # /setup — interactive onboarding
│   ├── build/             # /build — dev workflow
│   ├── decide/            # /decide — decision framework
│   ├── eval/              # /eval — evaluation + security audits
│   ├── focus/             # /focus — brain dump → action plan
│   ├── pmf/               # /pmf — customer-discovery loop
│   ├── explain/           # /explain — topic → visual explainer PDF
│   ├── legal/             # /legal — contract redline
│   ├── source/            # /source — recruiting candidate list
│   ├── learn/             # /learn — Claude Code best practices
│   ├── search/            # /search — deep multi-source research
│   └── sync/              # /sync — external data sync
├── mcps/                  # 4 MCP servers
│   ├── notion-mcp/        # Notion page/database access
│   ├── obsidian-mcp/      # Git-aware Obsidian vault access
│   ├── plaud-mcp/         # Plaud transcript access
│   └── vault-mcp/         # Team knowledge vault + daemon
├── sandbox/               # QM sandbox example (greet + example-tool)
├── .codex/skills/         # Agent deploy skills (QM upstream + Company OS wrapper)
├── evals/                 # Promptfoo adversarial security-eval scaffold
├── tests/                 # Integration tests
└── .claude/               # MCP + hooks config (auto-loaded)
    └── settings.json
```

---

## Quick Reference

| Action | How |
|---|---|
| Enter plan mode | Shift+Tab twice |
| Skip all permissions | `claude --dangerously-skip-permissions` |
| Resume last session | `/resume` |
| Cancel current action | Double-press Escape |
| Spawn parallel researchers | Say "spawn subagents" in your prompt |
| Get interactive questions | Say "use AskUserQuestion tool" |

---

## Engineering Standards

- **Keep it simple** — avoid over-engineering, no unnecessary abstractions
- **Python**: use ruff for formatting and linting
- **TypeScript**: use prettier for formatting
- **PRs**: short title (under 70 chars), summary + test plan in description
- **Safety**: never commit secrets, never force push to main, ask before destructive operations
