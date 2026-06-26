# CLAUDE.md

Global instructions for all team members using Claude Code.

## Company Context

This is a shared Claude Code team environment. Customize `company-os.config.sh` after forking.

- **Team**: Configure team in `company-os.config.sh`
- **Stack**: Configure stack in `company-os.config.sh`

## Available Skills

| Skill | Description |
|-------|-------------|
| `/setup` | One-command onboarding — interactive setup through Claude Code's UI. |
| `/build [feature]` | Complete dev workflow: brainstorm -> plan -> TDD -> review -> ship. |
| `/decide [question]` | Structured decision framework. 1-way vs 2-way doors. Saves to Obsidian + Notion. |
| `/eval [component]` | Universal evaluation framework for Skills. Also: `/eval secure` for security audits. |
| `/focus [capture list]` | Brain dump -> prioritized action plan. Also: `/focus read [urls]`, `/focus timeaudit`. |
| `/momtest [idea]` | Generate a bias-free Mom Test interview-question bank for customer discovery / problem validation. |
| `/explain [topic]` | Turn any topic or document into a clear, visual explainer PDF (defines terms inline, auto-picks the right diagram). |
| `/legal [contract]` | Redline a contract term-by-term → tracked-changes .docx + plain-English summary PDF. |
| `/source [role]` | Turn a hiring need into a ranked A-grade candidate list (WHO scorecard + multi-source sweep → PDF). |
| `/search [topic]` | Deep research: local qmd + vault knowledge + Firecrawl + Parallel.ai + Reddit/X. |
| `/sync <source>` | Sync Notion pages/databases and Plaud transcripts to Obsidian vault. |
| `/learn [topic]` | Claude Code best practices: hooks, subagents, parallelization, evals, TDD. |

## Repo Structure

```
company-os/
├── CLAUDE.md              ← This file
├── README.md              ← Getting started guide
├── setup.sh               ← Thin wrapper → setup/init.sh
├── setup/                 ← Modular setup scripts
│   ├── init.sh            # Entrypoint: sources libs, runs steps in order
│   ├── verify.sh          # Standalone health checks shortcut
│   ├── lib/               # Shared helpers (colors, utils)
│   └── steps/             # 01-cli.sh through 10-summary.sh
├── .env.tpl               ← 1Password secret template
├── .claude/settings.json  ← MCP + hooks config (auto-loaded)
├── mcps/
│   ├── notion-mcp/        # Notion API (databases, pages, blocks)
│   ├── obsidian-mcp/      # Obsidian vault read/write
│   ├── plaud-mcp/         # Plaud transcripts & summaries
│   └── vault-mcp/         # Team knowledge vault
│       └── daemon/        # Background daemon: server + ngrok tunnel
├── skills/
│   ├── build/             # Dev workflow skill
│   ├── decide/            # Decision framework skill
│   ├── eval/              # Eval runner + security audits
│   ├── focus/             # Brain dump → action plan skill
│   ├── learn/             # Claude Code best practices reference
│   ├── search/            # Deep research skill
│   ├── setup/             # Interactive onboarding skill
│   └── sync/              # External data sync skill
├── upgrades/              # Staging area — playbooks & tools being evaluated
│   ├── developer/         # Developer playbook (workflow gates, knowledge lifecycle)
│   ├── researcher/        # AI research kit (paper discovery, analysis, indexing)
│   ├── hooks/             # Workflow enforcement hooks
│   ├── learnings/         # Team instinct system
│   └── tools/             # Research tooling
└── tests/                 # Integration tests for repo structure
```

## MCP Setup

Run `/setup` in Claude Code for onboarding. It handles everything interactively.

MCPs are installed at the **user level** by `/setup`, so they work in every Claude Code session — not just inside `company-os/`.

| MCP | Type | Works out of the box? |
|-----|------|-----------------------|
| **notion** | Local (uv) | Yes — shared team token |
| **obsidian** | Local (uv) | Yes if Obsidian installed |
| **plaud** | Local (uv) | Yes if Plaud Desktop is running |
| **vault** | Remote (HTTP) | Configured by `/setup` — pick your name |

### Troubleshooting
- **Notion fails** — shared token may have expired, ask your team admin
- **Plaud fails** — Plaud Desktop not running
- **Obsidian fails** — vault path wrong, re-run `/setup` to reconfigure
- **MCP not found** — re-run `/setup` from the `company-os/` directory

## Engineering Standards

### Code Style
- Keep it simple - avoid over-engineering
- Python: use ruff for formatting and linting
- TypeScript: use prettier for formatting
- Well-documented code with clear comments where logic isn't self-evident
- No unnecessary abstractions - three similar lines > premature abstraction

### PR Conventions
- Short title (under 70 characters)
- Description includes: Summary (1-3 bullets), Test plan (checklist)
- Always run tests before pushing

### Tool Usage
- Bias toward slash commands for one-off tasks
- Use skills for repeatable problem domains

## Safety

- Never commit secrets - use environment variables for all API keys
- Never force push to main/master
- When in doubt, ask before running destructive operations
