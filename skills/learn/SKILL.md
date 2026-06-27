---
name: learn
description: Claude Code best practices reference. Covers skills, hooks, subagents, context management, parallelization, token optimization, evals, and continuous learning. Based on community patterns from everything-claude-code.
user-invocable: true
disable-model-invocation: false
argument-hint: "[topic] | list"
allowed-tools: Read, Glob, Grep, WebFetch
---

# /learn - Claude Code Best Practices

Quick reference for Claude Code patterns, distilled from [everything-claude-code](https://github.com/affaan-m/everything-claude-code) and team experience.

## Usage

```
/learn                     # Show all topics
/learn hooks               # Hooks patterns and recipes
/learn subagents           # Subagent architecture
/learn context             # Context and memory management
/learn parallel            # Parallelization strategies
/learn tokens              # Token optimization
/learn evals               # Verification loops and evals
/learn skills              # Writing effective skills
/learn tdd                 # Test-driven development
/learn security            # Security review patterns
/learn learning            # Continuous learning / instincts
/learn setup               # Editor, MCP, plugin setup
/learn tips                # Keyboard shortcuts, aliases, tricks
```

## Instructions

1. Parse `$ARGUMENTS` to find the topic
2. If no topic or `list`, show the topics table above
3. Find the matching section below and present it clearly
4. Keep responses concise — link to source repo for deep dives

---

## Topic: Skills

Skills are workflow definitions that constrain Claude to a specific scope. They're shorthand for complex prompts.

**Structure:**
```
~/.claude/skills/
  coding-standards.md        # Single-file skill
  tdd-workflow/              # Multi-file skill with SKILL.md
    SKILL.md
    evals/
  security-review/
    SKILL.md
```

**Anatomy of a good skill:**
```yaml
---
name: my-skill
description: What it does (shown in /help)
user-invocable: true
argument-hint: "[args]"
allowed-tools: Bash, Read, Edit   # Scope the tools
---

# Skill Title

## When to use
[Clear trigger conditions]

## Steps
1. [Concrete step with example]
2. [Next step]

## Output format
[Expected output template]
```

**Key principles:**
- Scope tools narrowly — a security reviewer shouldn't need Write
- Include output format templates so output is consistent
- Add eval datasets to measure skill quality over time (but never save raw user input — only metrics)
- Skills activate ~50-80% of the time; for 100% reliability, use hooks instead

**Commands vs Skills:**
- **Skills** (`~/.claude/skills/`): Broader workflow definitions, can be multi-file
- **Commands** (`~/.claude/commands/`): Quick executable prompts, always slash-invocable

---

## Topic: Hooks

Hooks are event-driven automations that fire on specific Claude Code events. Unlike skills, they're 100% reliable.

**Hook types:**

| Event | When it fires | Use case |
|-------|---------------|----------|
| `PreToolUse` | Before a tool executes | Validation, reminders, blocking |
| `PostToolUse` | After a tool finishes | Formatting, linting, feedback |
| `UserPromptSubmit` | When you send a message | Input preprocessing |
| `Stop` | When Claude finishes | Session persistence, cleanup |
| `PreCompact` | Before context compaction | Save important state |
| `Notification` | Permission requests | Custom handling |

**Exit codes:**
- `0` = success (hook ran, no issue)
- `2` = block (prevent the tool call from executing)
- stderr = warning message shown to Claude

**Example: Auto-format after edits**
```json
{
  "PostToolUse": [
    {
      "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\.tsx?$\"",
      "hooks": [
        {
          "type": "command",
          "command": "prettier --write \"$TOOL_INPUT_FILE_PATH\""
        }
      ]
    }
  ]
}
```

**Example: Block accidental doc writes**
```json
{
  "PreToolUse": [
    {
      "matcher": "tool == \"Write\" && tool_input.file_path matches \"\\.md$\" && !(tool_input.file_path matches \"(README|CLAUDE)\")",
      "hooks": [
        {
          "type": "command",
          "command": "echo 'Blocked: Use Edit for .md files, or rename to README/CLAUDE' >&2; exit 2"
        }
      ]
    }
  ]
}
```

**Example: tmux reminder for long commands**
```json
{
  "PreToolUse": [
    {
      "matcher": "tool == \"Bash\" && tool_input.command matches \"(npm|pnpm|yarn|cargo|pytest)\"",
      "hooks": [
        {
          "type": "command",
          "command": "if [ -z \"$TMUX\" ]; then echo '[Hook] Consider tmux for session persistence' >&2; fi"
        }
      ]
    }
  ]
}
```

**Pro tips:**
- Use hooks for standards enforcement (formatting, linting, blocking bad patterns)
- Use `PreCompact` to save state before context compaction
- Use `Stop` for session-end persistence (lighter than UserPromptSubmit)
- Keep hooks fast — slow hooks add latency to every tool call
- Use the `hookify` plugin to create hooks conversationally

**Source:** [hooks/README.md](https://github.com/affaan-m/everything-claude-code/tree/main/hooks)

---

## Topic: Subagents

Subagents are scoped Claude instances that the main orchestrator delegates to. They save context by returning summaries instead of dumping everything into the main conversation.

**Structure:**
```
~/.claude/agents/
  planner.md             # Implementation planning
  architect.md           # System design
  tdd-guide.md           # Test-driven development
  code-reviewer.md       # Quality + security review
  security-reviewer.md   # Vulnerability analysis
  build-error-resolver.md
  e2e-runner.md          # Playwright E2E tests
  refactor-cleaner.md    # Dead code removal
```

**Key principles:**

1. **Scope tools narrowly** — a code reviewer shouldn't have Write/Edit access
2. **Pass objective context, not just the query** — the sub-agent lacks the orchestrator's semantic context
3. **Iterative retrieval** — evaluate sub-agent returns, ask follow-ups before accepting (max 3 cycles)
4. **One input, one output** — each agent gets one clear task and produces one clear artifact

**Orchestrator pattern (sequential phases):**
```
Phase 1: RESEARCH  (Explore agent)        → research-summary.md
Phase 2: PLAN      (planner agent)        → plan.md
Phase 3: IMPLEMENT (tdd-guide agent)      → code changes
Phase 4: REVIEW    (code-reviewer agent)  → review-comments.md
Phase 5: VERIFY    (build-error-resolver) → done or loop back
```

**Model selection for subagents:**

| Task | Model | Why |
|------|-------|-----|
| Exploration/search | Haiku | Fast, cheap, sufficient |
| Simple edits | Haiku | Single-file, clear instructions |
| Multi-file implementation | Sonnet | Best balance for coding |
| Complex architecture | Opus | Deep reasoning needed |
| PR reviews | Sonnet | Context + nuance |
| Security analysis | Opus | Can't afford to miss things |
| Writing docs | Haiku | Structure is simple |
| Debugging complex bugs | Opus | Needs whole-system view |

**Default to Sonnet for 90% of coding.** Upgrade to Opus when: first attempt failed, spans 5+ files, architectural decisions, or security-critical.

**Source:** [agents/](https://github.com/affaan-m/everything-claude-code/tree/main/agents)

---

## Topic: Context

Context window management is the #1 factor in Claude Code productivity.

### Memory persistence across sessions

Create session files that capture state:
```
.claude/sessions/
  2026-02-10-feature-auth.md
  2026-02-11-refactor-api.md
```

**Each session file should contain:**
- What approaches worked (with evidence)
- What was attempted but failed
- What's left to do
- Key decisions made

Start a new conversation by providing the session file path. Create a new file per session — don't pollute old context into new work.

### Strategic compaction

- Disable auto-compact for critical sessions
- Manually compact at logical intervals (after completing a phase)
- Use `PreCompact` hooks to save important state before compaction
- After planning, clear context and work from the plan

### Dynamic system prompt injection

Instead of putting everything in CLAUDE.md, inject context dynamically:

```bash
# Context-specific aliases
alias claude-dev='claude --system-prompt "$(cat ~/.claude/contexts/dev.md)"'
alias claude-review='claude --system-prompt "$(cat ~/.claude/contexts/review.md)"'
alias claude-research='claude --system-prompt "$(cat ~/.claude/contexts/research.md)"'
```

System prompt content has higher authority than user messages, which have higher authority than tool results.

### MCP context cost

- Have 20-30 MCPs configured, but keep **under 10 enabled / under 80 tools active**
- Your 200k context window can shrink to ~70k with too many tools enabled
- Replace MCPs with CLI-wrapping skills when possible (e.g., `gh` instead of GitHub MCP)
- Check with `/mcp` and disable unused ones

**Source:** [the-longform-guide.md](https://github.com/affaan-m/everything-claude-code/blob/main/the-longform-guide.md)

---

## Topic: Parallel

Parallelization strategies for running multiple Claude instances.

### Forking conversations

Use `/fork` to split a conversation into parallel branches for non-overlapping work.

**Best pattern:** Main chat for code changes, forks for questions about the codebase or research on external services.

### Git worktrees for overlapping work

```bash
# Create worktrees for parallel features
git worktree add ../project-feature-a feature-a
git worktree add ../project-feature-b feature-b

# Each worktree gets its own Claude instance
cd ../project-feature-a && claude
```

**When overlapping work is unavoidable**, worktrees prevent merge conflicts between instances.

### The cascade method

When running multiple instances:
1. Open new tasks in new tabs to the right
2. Sweep left to right, oldest to newest
3. Focus on at most 3-4 tasks at a time
4. Use `/rename <name>` to label each chat

### The two-instance kickoff

For new projects, start with two instances:
- **Instance 1 (Scaffolding):** Project structure, configs, CLAUDE.md, rules
- **Instance 2 (Research):** PRD, architecture diagrams, documentation references

### Key principle

**How much can you get done with the minimum viable amount of parallelization?** Don't set arbitrary terminal counts. Each new instance should serve a genuine need.

**Source:** [the-longform-guide.md#parallelization](https://github.com/affaan-m/everything-claude-code/blob/main/the-longform-guide.md)

---

## Topic: Tokens

Token optimization strategies to reduce cost and improve performance.

### Subagent model selection

Default to Sonnet. Use Haiku for exploration/search/docs. Use Opus only when needed (see subagents topic).

### Replace grep with mgrep

The `mgrep` plugin reduces token usage by ~50% compared to traditional grep/ripgrep. Install via plugin marketplace.

### Modular codebase

Files in the hundreds of lines instead of thousands help both token costs and first-try accuracy.

### Replace MCPs with CLI skills

MCPs eat context even when idle. Replace with skills that wrap CLI tools:
- GitHub MCP → `/gh-pr` command wrapping `gh pr create`
- Supabase MCP → skills using Supabase CLI
- Vercel MCP → skills using `vercel` CLI

### llms.txt pattern

Many documentation sites expose `/llms.txt` — an LLM-optimized version of their docs. Use these instead of scraping full pages.

**Source:** [the-longform-guide.md#token-optimization](https://github.com/affaan-m/everything-claude-code/blob/main/the-longform-guide.md)

---

## Topic: Evals

Verification loops and evaluation patterns.

### Benchmarking skills

Compare output with and without a skill:
1. Fork the conversation
2. Run one branch without the skill, one with
3. Diff the outputs
4. Measure quality difference

### Eval pattern types

- **Checkpoint-based:** Set explicit checkpoints, verify against criteria, fix before proceeding
- **Continuous:** Run every N minutes or after major changes (full test suite + lint)

### Key metrics

```
pass@k: At least ONE of k attempts succeeds
        k=1: 70%   k=3: 91%   k=5: 97%

pass^k: ALL k attempts must succeed
        k=1: 70%   k=3: 34%   k=5: 17%
```

Use **pass@k** when you just need it to work. Use **pass^k** when consistency matters.

### Skill eval datasets

Track metrics per session (scores, counts, pattern usage). **Never save raw input or output** — only aggregate metrics. See the focus skill's eval approach for reference.

**Source:** [the-longform-guide.md#verification-loops-and-evals](https://github.com/affaan-m/everything-claude-code/blob/main/the-longform-guide.md)

---

## Topic: TDD

Test-driven development workflow.

### The cycle

```
RED    → Write a failing test first
GREEN  → Write minimum code to pass
REFACTOR → Clean up, maintain 80%+ coverage
```

### Rules

1. **Never write implementation before tests**
2. **One test at a time** — don't batch
3. **Run tests after every change**
4. **80% minimum coverage** — no exceptions
5. **Mock external services** (APIs, databases, file system)

### Anti-patterns to avoid

- Writing tests after implementation (loses the design benefit)
- Testing implementation details instead of behavior
- Skipping the refactor step
- Testing private methods directly
- Not mocking external dependencies

### Test structure

```
tests/
  unit/           # Fast, isolated, mock dependencies
  integration/    # Real services, slower
  e2e/            # Full user flows (Playwright)
```

**Source:** [skills/tdd-workflow/](https://github.com/affaan-m/everything-claude-code/tree/main/skills/tdd-workflow)

---

## Topic: Security

Security review checklist for Claude Code projects.

### The checklist

1. **Secrets management** — Never hardcode. Use env vars, `.env` files (gitignored), or secret managers
2. **Input validation** — Validate at system boundaries (user input, API responses). Use Zod schemas
3. **SQL injection** — Use parameterized queries, never string concatenation
4. **XSS prevention** — Sanitize output, use framework escaping (React does this by default)
5. **CSRF protection** — Use tokens for state-changing operations
6. **Auth/authz** — Verify both authentication AND authorization on every request
7. **Rate limiting** — Apply to all public endpoints
8. **Row Level Security** — Enable RLS on all Supabase tables
9. **Dependency audit** — Run `npm audit` / `pip audit` regularly
10. **No console.logs in production** — Use proper logging with levels

### Pre-deployment checklist

- [ ] All secrets in env vars (not in code)
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS sanitization confirmed
- [ ] Auth checks on all protected routes
- [ ] Rate limiting configured
- [ ] Dependencies audited
- [ ] No debug code in production

**Source:** [skills/security-review/](https://github.com/affaan-m/everything-claude-code/tree/main/skills/security-review)

---

## Topic: Learning

Continuous learning — teaching Claude your patterns over time.

### The problem

Repeating the same corrections session after session wastes tokens, context, and time.

### The solution: Instincts

When Claude discovers something non-trivial (a debugging technique, a workaround, a project pattern), it saves that knowledge. Next time a similar problem arises, the knowledge loads automatically.

### Architecture

```
instincts/
  instinct-001.md    # Confidence: 0.3 (new observation)
  instinct-002.md    # Confidence: 0.7 (confirmed pattern)
  instinct-003.md    # Confidence: 0.9 (promoted to skill)
```

**Confidence scoring:**
- `0.3` — New observation, single occurrence
- `0.5` — Seen 2-3 times, likely a pattern
- `0.7` — Confirmed pattern, applied successfully
- `0.9` — Ready to promote to a full skill or command

### Hook-based capture (100% reliable)

Use hooks instead of skills for observation — skills activate ~50-80% of the time, hooks fire every time.

- `PreToolUse` / `PostToolUse` hooks observe every tool call
- Background Haiku agent analyzes patterns without burning main context
- Instincts evolve into skills/commands/agents over time

### Commands

```
/instinct-status    # View current instincts and confidence scores
/instinct-import    # Import instincts from teammate
/instinct-export    # Export your instincts for sharing
/evolve             # Cluster instincts into skills/commands
```

### Key design decision

Use a **Stop hook** (session end) instead of UserPromptSubmit (every message). UserPromptSubmit adds latency to every prompt. Stop runs once — lightweight.

**Source:** [skills/continuous-learning-v2/](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2)

---

## Topic: Setup

Editor, MCP, and plugin setup recommendations.

### Editor pairing

**Zed** (recommended for speed):
- Rust-based, opens instantly, low resource usage
- Agent panel tracks file changes in real-time
- CMD+Shift+R for command palette
- Won't compete with Claude for RAM/CPU

**VS Code / Cursor:**
- Claude Code extension for integrated UI
- `\ide` for LSP sync (somewhat redundant with LSP plugins now)

**Editor-agnostic tips:**
- Split screen: terminal + editor side by side
- Enable auto-save
- Enable file watcher / auto-reload
- Use git integration to review changes before committing

### MCP configuration

Keep MCPs in user config but disable unused ones:
```bash
/mcp   # Check enabled MCPs
```

**Rule of thumb:** 20-30 configured, under 10 enabled, under 80 tools active.

### Useful plugins

```
typescript-lsp@claude-plugins-official    # TypeScript intelligence
pyright-lsp@claude-plugins-official       # Python type checking
hookify@claude-plugins-official           # Create hooks conversationally
mgrep@Mixedbread-Grep                     # Better search (~50% token reduction)
context7@claude-plugins-official          # Live documentation
```

Same warning as MCPs — watch context window.

### Rules structure

```
~/.claude/rules/
  security.md       # No hardcoded secrets, validate inputs
  coding-style.md   # Immutability, file organization
  testing.md        # TDD, 80% coverage
  git-workflow.md   # Conventional commits
  agents.md         # When to delegate to subagents
  performance.md    # Model selection, context management
```

**Source:** [the-shortform-guide.md](https://github.com/affaan-m/everything-claude-code/blob/main/the-shortform-guide.md)

---

## Topic: Tips

Keyboard shortcuts, aliases, and workflow tricks.

### Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+U` | Delete entire line (faster than backspace) |
| `!` | Quick bash command prefix |
| `@` | Search for files |
| `/` | Slash commands |
| `Shift+Enter` | Multi-line input |
| `Tab` | Toggle thinking display |
| `Esc Esc` | Interrupt Claude / restore code |

### Useful commands

| Command | Action |
|---------|--------|
| `/fork` | Fork conversation for parallel work |
| `/rename` | Name your chat for easy identification |
| `/rewind` | Go back to a previous state |
| `/compact` | Manually trigger context compaction |
| `/checkpoints` | File-level undo points |
| `/statusline` | Customize status bar |
| `/mcp` | Manage MCP servers |

### Terminal aliases

```bash
alias c='claude'
alias claude-dev='claude --system-prompt "$(cat ~/.claude/contexts/dev.md)"'
alias claude-review='claude --system-prompt "$(cat ~/.claude/contexts/review.md)"'
```

### Voice transcription

Talk to Claude Code instead of typing:
- **macOS:** SuperWhisper, MacWhisper
- Claude understands intent even with transcription errors

### llms.txt

Many docs sites expose `/llms.txt` — add it to any docs URL for an LLM-optimized version.

**Source:** [the-shortform-guide.md](https://github.com/affaan-m/everything-claude-code/blob/main/the-shortform-guide.md), [the-longform-guide.md](https://github.com/affaan-m/everything-claude-code/blob/main/the-longform-guide.md)

---

## Attribution

Patterns distilled from [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by [@affaan-m](https://github.com/affaan-m), Anthropic hackathon winner. Adapted for team use.
