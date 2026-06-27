# Notion Enhanced MCP

Enhanced Notion MCP server with full property type support for database operations.

## Features

- **Full Property Type Support**: Create and update database rows with all 24 Notion property types
- **Auto-Pagination**: Query functions automatically fetch ALL results by default (no 100-item limit)
- **Block Operations**: Append any block type (tables, callouts, code, etc.) to pages
- **Markdown Conversion**: Convert markdown to Notion blocks
- **Schema Introspection**: Get database schemas with property definitions

## Tools

### Database Operations

- `get_database_schema(database_id)` - Get database schema with property types and options
- `query_database(database_id, filter, sorts, page_size, start_cursor, fetch_all)` - Query database with filters
  - `fetch_all=True` (default): Auto-paginates to fetch ALL results
  - `fetch_all=False`: Returns single page with `next_cursor` for manual pagination
- `create_database_row(database_id, properties, content)` - Create row with any property types
- `update_database_row(page_id, properties)` - Update row properties

### Page Operations

- `get_page(page_id, include_content)` - Get page with properties and content (auto-paginates content blocks)
- `search_pages(query, filter_type, page_size, start_cursor, fetch_all)` - Search pages and databases
  - `fetch_all=True` (default): Auto-paginates to fetch ALL results
  - `fetch_all=False`: Returns single page with `next_cursor` for manual pagination
- `append_blocks(page_id, blocks)` - Append blocks to page
- `append_markdown(page_id, markdown)` - Append markdown content

## Property Types Supported

| Type | Example Value |
|------|---------------|
| title | `"My Title"` |
| rich_text | `"Some text"` |
| number | `42` or `3.14` |
| select | `"Option A"` |
| multi_select | `["Tag1", "Tag2"]` |
| date | `"2024-01-15"` or `{"start": "...", "end": "..."}` |
| checkbox | `true` or `false` |
| url | `"https://example.com"` |
| email | `"user@example.com"` |
| phone_number | `"+1234567890"` |
| status | `"In Progress"` |
| files | `["https://url1.com", "https://url2.com"]` |
| relation | `["page_id_1", "page_id_2"]` |
| people | `["user_id_1"]` |

## Installation

```bash
uv tool install .
```

## Configuration

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "notion": {
      "type": "stdio",
      "command": "notion-mcp",
      "args": [],
      "env": {
        "NOTION_TOKEN": "your_notion_token"
      }
    }
  }
}
```

## Pagination

By default, `query_database` and `search_pages` automatically paginate through ALL results. The Notion API limits responses to 100 items per request, but this MCP handles pagination transparently.

```python
# Fetch ALL rows (auto-pagination, default behavior)
result = query_database(database_id="abc123...")
print(f"Total tools: {result['total_count']}")  # e.g., 500

# Manual pagination (for large datasets or streaming)
result = query_database(database_id="abc123...", fetch_all=False)
while result.get('has_more'):
    # Process current batch
    process(result['results'])
    # Fetch next page
    result = query_database(
        database_id="abc123...",
        start_cursor=result['next_cursor'],
        fetch_all=False
    )
```

## Usage Example

```python
# Create a tool row with full properties
create_database_row(
    database_id="abc123...",
    properties={
        "Tool Name": "Morph LLM",
        "URL": "https://morphllm.com",
        "Tags": ["Coding", "AI", "Developers"],
        "Rating": 2,
        "Description": "Fast code editing AI"
    }
)
```
