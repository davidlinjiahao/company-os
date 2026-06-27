---
name: sync
description: Sync external data sources to Obsidian. Supports Notion pages/databases and Plaud transcripts.
user-invocable: true
argument-hint: "<source> [args]"
allowed-tools: Bash, AskUserQuestion, Read
---

# /sync - External Data Sync

Sync content from external sources into your Obsidian vault.

## Subcommands

### /sync notion [page-url-or-id]
Import Notion pages and databases to Obsidian with full markdown conversion and automatic hierarchical organization.

```
/sync notion
/sync notion https://notion.so/Page-Name-abcd1234abcd1234abcd1234abcd1234
/sync notion abcd1234abcd1234abcd1234abcd1234
```

### /sync plaud
Import Plaud recording transcripts to Obsidian vault via PlaudClient (CDP connection to Plaud Desktop).

```
/sync plaud              # sync last 30 days
/sync plaud --days 7     # sync last 7 days
/sync plaud --cleanup    # remove old-format duplicates
```

---

## Instructions

### For `notion`:

1. **Get the Notion page identifier** from user:
   - If not provided as argument, ask: "What Notion page would you like to import? You can provide the page URL or page ID."
   - Extract page ID from URL if provided (format: `https://notion.so/page-name-{PAGE_ID}`)
   - Clean page ID: remove dashes if present

2. **Get the output directory**:
   - Ask: "Where in Obsidian would you like to save this? (e.g., 'Company' or 'Projects/Research')"
   - Construct full path: `$OBSIDIAN_VAULT/{their_answer}`
   - If user says "Obsidian" or "my vault", ask them to be more specific about the folder

3. **Verify Notion token is set**:
   ```bash
   echo ${NOTION_TOKEN:+Token is set}
   ```
   If not set, check if it's available via the Notion MCP (`mcp__notion__get_self`). If neither works, tell the user they need to configure the Notion token in their MCP settings.

4. **Run the import**:
   ```bash
   python3 ~/.claude/skills/sync/src/import_notion.py PAGE_ID OUTPUT_DIRECTORY
   ```
   - Add `--resume` flag to skip backup/clear and add files to an existing directory instead of overwriting it.

5. **Report the results** — review the evaluation report for success/failure rates

### For `plaud`:

1. **Check Plaud Desktop is running**
   ```bash
   curl -s http://127.0.0.1:9229/json | python3 -c "import sys,json; t=json.load(sys.stdin); print(f'Plaud inspector: {len(t)} target(s)')" 2>/dev/null || echo "Plaud Desktop not running or inspector not enabled"
   ```
   If not running, tell the user to open Plaud Desktop and log in.

2. **If `--cleanup` was requested**, run cleanup mode (no Plaud connection needed):
   ```bash
   # Find plaud-mcp dir: check common locations
   PLAUD_MCP_DIR="$(find ~/company-os -path '*/mcps/plaud-mcp/pyproject.toml' -maxdepth 4 2>/dev/null | head -1 | xargs dirname 2>/dev/null)"
   cd "$PLAUD_MCP_DIR" && uv run python3 -u ~/.claude/skills/sync/src/sync_plaud.py --cleanup
   ```
   - Preview first with `--dry-run` to see what would be deleted
   - Finds old-format files (`YYYY-MM-DD-MM-DD-slug.md`) that have new-format equivalents
   - Verifies by comparing transcript content (first 40 chars), not just filename keywords
   - Safe: only deletes when both keyword match AND content match confirm same recording

3. **Otherwise, run the sync script**
   ```bash
   # Find plaud-mcp dir: check common locations
   PLAUD_MCP_DIR="$(find ~/company-os -path '*/mcps/plaud-mcp/pyproject.toml' -maxdepth 4 2>/dev/null | head -1 | xargs dirname 2>/dev/null)"
   cd "$PLAUD_MCP_DIR" && uv run python3 -u ~/.claude/skills/sync/src/sync_plaud.py --days 30
   ```
   - Use `--days N` to control how far back to look (default: 30)
   - Use `--dry-run` to preview without writing files
   - Use `--limit N` to sync only the first N missing files
   - **Important:** Use `timeout: 600000` (10 minutes) on the Bash tool call — CDP calls are slow (~2-3s each) and syncing many files can take 5-10 minutes

4. **Parse and display results**
   - The script outputs progress for each file and a summary at the end
   - Report synced count, skipped count, and any errors
   - Note: errors on unnamed/very short recordings (< 1 min) are normal

5. **Provide summary**
   - Number of new transcripts imported
   - Location: `ObsidianVault/Transcripts/Plaud/`

---

## Notion Import Details

### Hierarchical Organization
- **Pages with children**: Create a subdirectory named after the page
- **Pages without children**: Remain at the current directory level
- **Databases**: Always create subdirectories with entries inside

### Import Verification
After import completes, the script automatically runs evaluation:
- Import statistics (pages, databases, entries)
- File verification (empty files, errors, missing content)
- Overall success rate

### Troubleshooting (Notion)
- **"Notion token not found"**: Configure NOTION_TOKEN in MCP settings or `~/.claude/.env`
- **"Could not find page"**: Check page ID or sharing permissions
- **"Permission denied"**: Share the Notion page with your integration

---

## Plaud Import Details

### Architecture
- **PlaudClient** (`mcps/plaud-mcp/src/plaud_mcp/plaud_client.py` in the company-os repo) connects to Plaud Desktop via Chrome DevTools Protocol (CDP) on `localhost:9229`
- The script piggybacks on Plaud Desktop's authenticated `$fetch` function — no token extraction needed
- SIGUSR1 is sent to the Plaud process to enable the Node.js inspector automatically
- Must be run via `uv run` from the plaud-mcp directory so dependencies (httpx, websockets) resolve

### What It Does
- Connects to Plaud Desktop via CDP
- Fetches recordings list, transcripts, and AI-generated summaries
- Deduplicates against existing Obsidian files (plaud_id from frontmatter first, keyword fallback second)
- Creates markdown files with frontmatter at `Transcripts/Plaud/`

### Deduplication Strategy
1. **plaud_id match** (exact): Reads `plaud_id` from YAML frontmatter of all existing `.md` files. Any Plaud recording whose ID is already present is skipped. This is the primary dedup method for future syncs.
2. **Keyword match** (fuzzy fallback): For files without `plaud_id` (old-format or manually created), extracts keywords (3+ chars) from filenames and checks for ≥3 overlapping keywords or ≥60% overlap ratio.
3. **Filename match**: Also checks if the exact output filename already exists.

### Output Format
```yaml
---
author: $USER
date: YYYY-MM-DD
source: plaud
plaud_id: <hash>       # <- used for dedup on future syncs
duration: Xh Ym Zs
tags: [meeting, transcript, auto-ingest]
---
```
Followed by `## Summary` (AI-generated) and `## Transcript` (speaker-labeled).

### File Format History
Three generations of Plaud files exist in the vault:
1. **Old manual** (~7 files): `file_id`/`category` in frontmatter, various filename styles
2. **Old transcript-hub** (~10 remaining): `YYYY-MM-DD-MM-DD-slug.md` format, `author`/`date`/`source`/`tags` frontmatter
3. **New sync** (majority): `YYYY-MM-DD - Title.md` format, includes `plaud_id`/`duration`

The `--cleanup` flag handles removing old-format duplicates that have new-format equivalents.

### Troubleshooting (Plaud)
- **"Plaud Desktop not running"**: Open Plaud Desktop app and log in
- **"Request URL is missing protocol"**: Normal for unnamed/incomplete recordings — safe to ignore
- **"list index out of range"**: Very long recordings (5h+) may have CDP issues — try again or fetch manually
- **Inspector not available**: The PlaudClient sends SIGUSR1 to enable Node.js inspector automatically
- **Import errors (httpcore)**: Don't use the MCP tool calls directly — run the sync script via `uv run` instead

---

## Related Files

- `src/import_notion.py` - Notion import script
- `src/sync_plaud.py` - Plaud transcript sync script (uses PlaudClient via CDP)
- `requirements.txt` - Python dependencies (for Notion)
