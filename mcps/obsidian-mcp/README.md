# Obsidian Vault MCP

Git-aware MCP server for a shared Obsidian vault. Reads/writes markdown files and automatically syncs via git.

## Quickstart

**Prerequisites:** [uv](https://docs.astral.sh/uv/getting-started/installation/) and an Obsidian vault on disk.

```bash
# 1. Test that it starts (replace with your vault path)
OBSIDIAN_VAULT_PATH=~/Documents/ObsidianVault uv run --directory mcps/obsidian-mcp obsidian-mcp
```

If you see `Starting Obsidian MCP server for vault: ...`, it works. Ctrl-C to stop.

```bash
# 2. Add to Claude Code — edit ~/.claude.json or your settings.json:
```

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uv",
      "args": ["run", "--directory", "<absolute-path-to>/mcps/obsidian-mcp", "obsidian-mcp"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "<absolute-path-to-your-vault>",
        "VAULT_GIT_SYNC": "true"
      }
    }
  }
}
```

Replace `<absolute-path-to>` with the actual paths on your machine. Restart Claude Code.

**That's it.** No API keys needed. No pip install. uv handles everything.

## Architecture

```
Engineer A writes note ──▶ obsidian-mcp ──▶ vault/ ──▶ git commit + push ──▶ GitHub
                                                                                │
Engineer B reads note  ◀── obsidian-mcp ◀── vault/ ◀── git pull (every 2 min) ◀┘
```

## Tools

### Read (pull before read)
- **read_note** — content with metadata and `content_hash`
- **list_folder** — files in a folder (recursive option)
- **get_structure** — folder tree
- **search** — full-text search within notes
- **search_files** — search by filename
- **list_tags** — list all tags or find notes by tag
- **get_recent** — recently modified notes

### Write (commit + push after write)
- **create_note** — create a new note
- **update_note** — replace content (supports `expected_hash` for conflict detection)
- **append_to_note** — append to existing note
- **rename_note** — rename or move a note

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `OBSIDIAN_VAULT_PATH` | `~/Documents/ObsidianVault` | Path to vault directory |
| `VAULT_GIT_SYNC` | `true` | Enable git auto-sync |
| `VAULT_GIT_PULL_INTERVAL` | `120` | Seconds between pulls |

Set `VAULT_GIT_SYNC=false` if your vault isn't a git repo.

## Conflict Detection

When you read a note, the response includes a `content_hash`. Pass it back when updating to detect concurrent edits:

```python
update_note("Decisions/example.md", new_content, expected_hash="abc123def456")
# Fails if someone else modified the file since your read
```

The hash is optional — writes without it still work.

## Security

- All paths validated to stay within the vault
- Hidden files and .trash folder excluded
- Git operations use `--autostash` to prevent data loss

## Development

```bash
# Run in HTTP mode for testing
cd mcps/obsidian-mcp
uv run obsidian-mcp --http
```
