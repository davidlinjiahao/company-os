# Plaud MCP Server

MCP server for Plaud transcripts via CDP proxy through the running Plaud Desktop app.

## How It Works

```
Claude Code → MCP Server → CDP (WebSocket) → Plaud Desktop → Plaud API
```

The MCP connects to the running Plaud Desktop Electron app via Chrome DevTools Protocol:

1. Sends `SIGUSR1` to the Plaud Desktop process to enable Node.js inspector (port 9229)
2. Connects via WebSocket to the inspector
3. Executes API calls through the app's own authenticated `$fetch` function
4. Returns results back through MCP tools

No token extraction, no cookies, no API keys. Uses the app's live authenticated session directly.

## Prerequisites

1. **macOS** (Plaud Desktop is an Electron app; CDP + SIGUSR1 is macOS-only)
2. **[Plaud Desktop](https://www.plaud.ai/)** installed and signed in
3. **Python 3.10+**
4. **[uv](https://docs.astral.sh/uv/getting-started/installation/)** (recommended)

## Installation

```bash
cd mcps/plaud-mcp
uv tool install --force .
```

## Configuration

Add to your Claude Code MCP config (`~/.claude.json` or project settings):

**Option A: Via `uv tool install` (recommended)**

```json
{
  "mcpServers": {
    "plaud": {
      "command": "plaud-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

**Option B: Via `uv run` (no install needed)**

```json
{
  "mcpServers": {
    "plaud": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/your/clone/mcps/plaud-mcp",
        "plaud-mcp"
      ]
    }
  }
}
```

Replace `/path/to/your/clone` with wherever you cloned `company-os`.

No API keys or tokens needed. Just ensure Plaud Desktop is running.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PLAUD_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |

## MCP Tools

| Tool | Description |
|------|-------------|
| `check_connection` | Verify Plaud Desktop is available |
| `get_file_count` | Total number of recordings |
| `get_recent_files` | Files from the last N days |
| `get_files` | Files with optional date filters |
| `get_file` | Metadata for a specific file |
| `get_transcript` | Full transcript with speaker labels |
| `get_summary` | AI-generated summary |
| `rename_file` | Rename a Plaud file |
| `search_transcripts` | Search transcripts by content |

## Troubleshooting

### "Plaud Desktop is not running"
Launch the Plaud Desktop app and sign in.

### "Could not enable inspector"
The SIGUSR1 signal may have failed. Ensure Plaud Desktop is the main process, not a helper.

### Search is slow
`search_transcripts` fetches and searches client-side. Reduce the `days` parameter.

## Why CDP?

Plaud's API validates auth at the Chromium network stack level - tokens extracted from LevelDB don't work with standard HTTP clients (httpx, curl, curl_cffi with Chrome impersonation all return 401). The CDP approach bypasses this entirely by executing requests through the app's own authenticated context.

## Development

```bash
uv sync --group dev
uv run ruff check src/ && uv run pyright src/
```
