# Quickstart

> **macOS only.** Requires the [Plaud Desktop](https://www.plaud.ai/) app installed and signed in.

```bash
# 0. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 1. Install plaud-mcp
cd mcps/plaud-mcp
uv tool install --force .

# 2. Add to Claude Code config (~/.claude.json or project settings.json)
```

```json
{
  "mcpServers": {
    "plaud": {
      "command": "plaud-mcp"
    }
  }
}
```

```bash
# 3. Restart Claude Code, make sure Plaud Desktop is running and signed in
```

See [README.md](README.md) for full docs and troubleshooting.
