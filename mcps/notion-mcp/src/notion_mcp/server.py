"""Notion MCP Server with full property type support."""

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from .property_types import (
    build_properties_from_schema,
    parse_all_properties,
)
from .block_types import build_block, markdown_to_blocks

# Notion API configuration
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Initialize FastMCP server
mcp = FastMCP(name="notion")


def get_headers() -> dict:
    """Get Notion API headers with auth token."""
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN environment variable not set")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def api_request(method: str, endpoint: str, data: dict | None = None) -> dict:
    """Make Notion API request."""
    url = f"{NOTION_API_BASE}/{endpoint}"
    headers = get_headers()

    with httpx.Client(timeout=30.0) as client:
        if method == "GET":
            response = client.get(url, headers=headers, params=data)
        elif method == "POST":
            response = client.post(url, headers=headers, json=data)
        elif method == "PATCH":
            response = client.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            response = client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code >= 400:
            return {"error": response.text, "status": response.status_code}

        return response.json()


@mcp.tool()
def get_database_schema(database_id: str) -> dict[str, Any]:
    """
    Get the schema of a Notion database with all property definitions.

    Args:
        database_id: The ID of the Notion database

    Returns:
        Dict with database title and properties schema
    """
    result = api_request("GET", f"databases/{database_id}")

    if "error" in result:
        return result

    schema = {}
    for prop_name, prop_def in result.get("properties", {}).items():
        prop_info = {
            "type": prop_def.get("type"),
            "id": prop_def.get("id"),
        }

        # Include options for select/multi_select
        if prop_def.get("type") == "select":
            prop_info["options"] = [
                opt.get("name") for opt in prop_def.get("select", {}).get("options", [])
            ]
        elif prop_def.get("type") == "multi_select":
            prop_info["options"] = [
                opt.get("name") for opt in prop_def.get("multi_select", {}).get("options", [])
            ]
        elif prop_def.get("type") == "status":
            prop_info["options"] = [
                opt.get("name") for opt in prop_def.get("status", {}).get("options", [])
            ]

        schema[prop_name] = prop_info

    title_list = result.get("title", [])
    title = "".join(t.get("plain_text", "") for t in title_list)

    return {
        "database_id": database_id,
        "title": title,
        "properties": schema,
    }


@mcp.tool()
def query_database(
    database_id: str,
    filter: dict | None = None,
    sorts: list[dict] | None = None,
    page_size: int = 100,
    start_cursor: str | None = None,
    fetch_all: bool = True,
) -> dict[str, Any]:
    """
    Query a Notion database with optional filter and sorts.

    Args:
        database_id: The ID of the Notion database
        filter: Optional Notion filter object (see Notion API docs)
        sorts: Optional list of sort objects
        page_size: Number of results per page (max 100)
        start_cursor: Cursor for pagination (from previous query's next_cursor)
        fetch_all: If True, auto-paginate to fetch ALL results. If False, return
                   single page with pagination info. Default True.

    Returns:
        Dict with:
            - results: List of database rows with parsed properties
            - total_count: Number of results returned
            - has_more: Whether more results exist (only when fetch_all=False)
            - next_cursor: Cursor for next page (only when fetch_all=False and has_more=True)
    """
    all_rows = []
    current_cursor = start_cursor

    while True:
        data: dict[str, Any] = {"page_size": min(page_size, 100)}
        if filter:
            data["filter"] = filter
        if sorts:
            data["sorts"] = sorts
        if current_cursor:
            data["start_cursor"] = current_cursor

        result = api_request("POST", f"databases/{database_id}/query", data)

        if "error" in result:
            return {"error": result.get("error"), "results": all_rows, "total_count": len(all_rows)}

        for page in result.get("results", []):
            row = {
                "id": page.get("id"),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "url": page.get("url"),
                "properties": parse_all_properties(page.get("properties", {})),
            }
            all_rows.append(row)

        has_more = result.get("has_more", False)
        next_cursor = result.get("next_cursor")

        # If not fetching all, return single page with pagination info
        if not fetch_all:
            response = {
                "results": all_rows,
                "total_count": len(all_rows),
                "has_more": has_more,
            }
            if has_more and next_cursor:
                response["next_cursor"] = next_cursor
            return response

        # If fetching all, continue until no more pages
        if not has_more:
            break
        current_cursor = next_cursor

    return {
        "results": all_rows,
        "total_count": len(all_rows),
    }


@mcp.tool()
def create_database_row(
    database_id: str,
    properties: dict[str, Any],
    content: str | None = None,
) -> dict[str, Any]:
    """
    Create a new row in a Notion database with full property type support.

    Args:
        database_id: The ID of the Notion database
        properties: Dict of property_name -> value. Supported types:
            - title: str
            - rich_text: str
            - number: int or float
            - select: str (option name)
            - multi_select: list[str] (option names)
            - date: str (ISO 8601) or {"start": str, "end": str}
            - checkbox: bool
            - url: str
            - email: str
            - phone_number: str
            - status: str (status name)
            - files: list[str] (URLs)
            - relation: list[str] (page IDs)
            - people: list[str] (user IDs)
        content: Optional markdown content to add to the page body

    Returns:
        Created page with ID and URL
    """
    # Get schema to know property types
    schema_result = get_database_schema(database_id)
    if "error" in schema_result:
        return schema_result

    schema = schema_result.get("properties", {})
    notion_properties = build_properties_from_schema(schema, properties)

    # Build request
    data: dict[str, Any] = {
        "parent": {"database_id": database_id},
        "properties": notion_properties,
    }

    # Add content blocks if provided
    if content:
        data["children"] = markdown_to_blocks(content)

    result = api_request("POST", "pages", data)

    if "error" in result:
        return result

    return {
        "id": result.get("id"),
        "url": result.get("url"),
        "created_time": result.get("created_time"),
        "properties": parse_all_properties(result.get("properties", {})),
    }


@mcp.tool()
def update_database_row(
    page_id: str,
    properties: dict[str, Any],
) -> dict[str, Any]:
    """
    Update properties on an existing Notion database row.

    Args:
        page_id: The ID of the page/row to update
        properties: Dict of property_name -> value to update

    Returns:
        Updated page info
    """
    # Get current page to know its parent database
    page_result = api_request("GET", f"pages/{page_id}")
    if "error" in page_result:
        return page_result

    # Get database schema
    parent = page_result.get("parent", {})
    if parent.get("type") != "database_id":
        return {"error": "Page is not a database row"}

    database_id = parent.get("database_id")
    schema_result = get_database_schema(database_id)
    if "error" in schema_result:
        return schema_result

    schema = schema_result.get("properties", {})
    notion_properties = build_properties_from_schema(schema, properties)

    result = api_request("PATCH", f"pages/{page_id}", {"properties": notion_properties})

    if "error" in result:
        return result

    return {
        "id": result.get("id"),
        "url": result.get("url"),
        "last_edited_time": result.get("last_edited_time"),
        "properties": parse_all_properties(result.get("properties", {})),
    }


@mcp.tool()
def append_blocks(
    page_id: str,
    blocks: list[dict[str, Any]],
    after_block_id: str | None = None,
) -> dict[str, Any]:
    """
    Append blocks to a Notion page.

    Args:
        page_id: The ID of the page to append to
        blocks: List of block objects. Each block should have:
            - type: Block type (paragraph, heading_1, code, table, etc.)
            - Additional fields depending on type:
              - paragraph: {"text": "content"}
              - heading_1/2/3: {"text": "heading"}
              - bulleted_list_item: {"text": "item"}
              - numbered_list_item: {"text": "item"}
              - to_do: {"text": "task", "checked": false}
              - code: {"code": "content", "language": "python"}
              - quote: {"text": "quote"}
              - callout: {"text": "content", "emoji": "💡"}
              - divider: {} (no additional fields)
              - bookmark: {"url": "https://..."}
              - image: {"url": "https://..."}
              - table: {"rows": [["a", "b"], ["c", "d"]], "has_column_header": true}
        after_block_id: Optional block ID to insert after

    Returns:
        List of created blocks
    """
    notion_blocks = []
    for block_spec in blocks:
        block_type = block_spec.get("type")
        if not block_type:
            continue

        kwargs = {k: v for k, v in block_spec.items() if k != "type"}
        try:
            notion_block = build_block(block_type, **kwargs)
            notion_blocks.append(notion_block)
        except (ValueError, TypeError) as e:
            return {"error": f"Failed to build block: {e}"}

    data: dict[str, Any] = {"children": notion_blocks}
    if after_block_id:
        data["after"] = after_block_id

    result = api_request("PATCH", f"blocks/{page_id}/children", data)

    if "error" in result:
        return result

    return {
        "created_blocks": len(result.get("results", [])),
        "block_ids": [b.get("id") for b in result.get("results", [])],
    }


@mcp.tool()
def append_markdown(
    page_id: str,
    markdown: str,
) -> dict[str, Any]:
    """
    Append markdown content to a Notion page.

    Converts markdown to Notion blocks and appends them.

    Args:
        page_id: The ID of the page to append to
        markdown: Markdown content to append

    Returns:
        Number of blocks created
    """
    blocks = markdown_to_blocks(markdown)

    result = api_request("PATCH", f"blocks/{page_id}/children", {"children": blocks})

    if "error" in result:
        return result

    return {
        "created_blocks": len(result.get("results", [])),
        "block_ids": [b.get("id") for b in result.get("results", [])],
    }


@mcp.tool()
def get_page(page_id: str, include_content: bool = False) -> dict[str, Any]:
    """
    Get a Notion page with its properties and optionally content.

    Args:
        page_id: The ID of the page
        include_content: Whether to fetch page content blocks (auto-paginates all blocks)

    Returns:
        Page info with properties and optionally content
    """
    result = api_request("GET", f"pages/{page_id}")

    if "error" in result:
        return result

    page = {
        "id": result.get("id"),
        "url": result.get("url"),
        "created_time": result.get("created_time"),
        "last_edited_time": result.get("last_edited_time"),
        "properties": parse_all_properties(result.get("properties", {})),
    }

    if include_content:
        # Paginate through all content blocks
        all_blocks = []
        current_cursor = None

        while True:
            params: dict[str, Any] = {"page_size": 100}
            if current_cursor:
                params["start_cursor"] = current_cursor

            blocks_result = api_request("GET", f"blocks/{page_id}/children", params)
            if "error" in blocks_result:
                break

            all_blocks.extend(blocks_result.get("results", []))

            if not blocks_result.get("has_more"):
                break
            current_cursor = blocks_result.get("next_cursor")

        page["content"] = all_blocks

    return page


@mcp.tool()
def search_pages(
    query: str,
    filter_type: str | None = None,
    page_size: int = 100,
    start_cursor: str | None = None,
    fetch_all: bool = True,
) -> dict[str, Any]:
    """
    Search Notion pages and databases.

    Args:
        query: Search query
        filter_type: Optional filter - "page" or "database"
        page_size: Number of results per page (max 100)
        start_cursor: Cursor for pagination
        fetch_all: If True, auto-paginate to fetch ALL results. Default True.

    Returns:
        Dict with:
            - results: List of matching pages/databases
            - total_count: Number of results
            - has_more: Whether more results exist (only when fetch_all=False)
            - next_cursor: Cursor for next page (only when fetch_all=False and has_more=True)
    """
    all_items = []
    current_cursor = start_cursor

    while True:
        data: dict[str, Any] = {
            "query": query,
            "page_size": min(page_size, 100),
        }

        if filter_type in ("page", "database"):
            data["filter"] = {"property": "object", "value": filter_type}
        if current_cursor:
            data["start_cursor"] = current_cursor

        result = api_request("POST", "search", data)

        if "error" in result:
            return {"error": result.get("error"), "results": all_items, "total_count": len(all_items)}

        for item in result.get("results", []):
            obj_type = item.get("object")

            if obj_type == "page":
                all_items.append({
                    "type": "page",
                    "id": item.get("id"),
                    "url": item.get("url"),
                    "properties": parse_all_properties(item.get("properties", {})),
                })
            elif obj_type == "database":
                title_list = item.get("title", [])
                title = "".join(t.get("plain_text", "") for t in title_list)
                all_items.append({
                    "type": "database",
                    "id": item.get("id"),
                    "url": item.get("url"),
                    "title": title,
                })

        has_more = result.get("has_more", False)
        next_cursor = result.get("next_cursor")

        # If not fetching all, return single page with pagination info
        if not fetch_all:
            response = {
                "results": all_items,
                "total_count": len(all_items),
                "has_more": has_more,
            }
            if has_more and next_cursor:
                response["next_cursor"] = next_cursor
            return response

        # If fetching all, continue until no more pages
        if not has_more:
            break
        current_cursor = next_cursor

    return {
        "results": all_items,
        "total_count": len(all_items),
    }


# --- Block operations ---


@mcp.tool()
def get_block(block_id: str) -> dict[str, Any]:
    """
    Retrieve a single block by ID.

    Args:
        block_id: The ID of the block

    Returns:
        Block object with type and content
    """
    return api_request("GET", f"blocks/{block_id}")


@mcp.tool()
def get_block_children(
    block_id: str,
    page_size: int = 100,
    start_cursor: str | None = None,
    fetch_all: bool = True,
) -> dict[str, Any]:
    """
    Retrieve children blocks of a block or page.

    Args:
        block_id: The ID of the parent block or page
        page_size: Number of results per page (max 100)
        start_cursor: Cursor for pagination
        fetch_all: If True, auto-paginate all children. Default True.

    Returns:
        Dict with results list and pagination info
    """
    all_blocks = []
    current_cursor = start_cursor

    while True:
        params: dict[str, Any] = {"page_size": min(page_size, 100)}
        if current_cursor:
            params["start_cursor"] = current_cursor

        result = api_request("GET", f"blocks/{block_id}/children", params)
        if "error" in result:
            return {"error": result.get("error"), "results": all_blocks, "total_count": len(all_blocks)}

        all_blocks.extend(result.get("results", []))
        has_more = result.get("has_more", False)
        next_cursor = result.get("next_cursor")

        if not fetch_all:
            response: dict[str, Any] = {
                "results": all_blocks,
                "total_count": len(all_blocks),
                "has_more": has_more,
            }
            if has_more and next_cursor:
                response["next_cursor"] = next_cursor
            return response

        if not has_more:
            break
        current_cursor = next_cursor

    return {"results": all_blocks, "total_count": len(all_blocks)}


@mcp.tool()
def update_block(block_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    """
    Update a block's content or archive it.

    Args:
        block_id: The ID of the block to update
        fields: Block fields to update. Pass the block type key with
                its content, e.g. {"paragraph": {"rich_text": [...]}}
                or {"archived": true} to archive.

    Returns:
        Updated block object
    """
    return api_request("PATCH", f"blocks/{block_id}", fields)


@mcp.tool()
def delete_block(block_id: str) -> dict[str, Any]:
    """
    Delete (archive) a block.

    Args:
        block_id: The ID of the block to delete

    Returns:
        Deleted block object
    """
    return api_request("DELETE", f"blocks/{block_id}")


# --- Page operations ---


@mcp.tool()
def create_page(
    parent_type: str,
    parent_id: str,
    title: str,
    properties: dict[str, Any] | None = None,
    content: str | None = None,
) -> dict[str, Any]:
    """
    Create a standalone page (not a database row).

    For creating database rows, use create_database_row instead.

    Args:
        parent_type: "page_id" or "workspace" (for top-level pages)
        parent_id: The ID of the parent page (ignored if workspace)
        title: Page title
        properties: Optional additional properties
        content: Optional markdown content for the page body

    Returns:
        Created page with ID and URL
    """
    if parent_type == "workspace":
        parent = {"type": "workspace", "workspace": True}
    else:
        parent = {"type": "page_id", "page_id": parent_id}

    data: dict[str, Any] = {
        "parent": parent,
        "properties": {
            "title": {"title": [{"text": {"content": title}}]},
            **(properties or {}),
        },
    }

    if content:
        data["children"] = markdown_to_blocks(content)

    result = api_request("POST", "pages", data)
    if "error" in result:
        return result

    return {
        "id": result.get("id"),
        "url": result.get("url"),
        "created_time": result.get("created_time"),
    }


@mcp.tool()
def move_page(page_id: str, parent_type: str, parent_id: str) -> dict[str, Any]:
    """
    Move a page to a different parent.

    Args:
        page_id: The ID of the page to move
        parent_type: "page_id" or "database_id"
        parent_id: The ID of the new parent

    Returns:
        Moved page info
    """
    data = {"parent": {"type": parent_type, parent_type: parent_id}}
    result = api_request("POST", f"pages/{page_id}/move", data)
    if "error" in result:
        return result

    return {
        "id": result.get("id"),
        "url": result.get("url"),
    }


# --- Comment operations ---


@mcp.tool()
def create_comment(
    page_id: str,
    text: str,
    discussion_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a comment on a page or reply to a discussion thread.

    Args:
        page_id: The ID of the page to comment on
        text: Comment text content
        discussion_id: Optional discussion thread ID to reply to

    Returns:
        Created comment object
    """
    data: dict[str, Any] = {
        "rich_text": [{"text": {"content": text}}],
    }

    if discussion_id:
        data["discussion_id"] = discussion_id
    else:
        data["parent"] = {"page_id": page_id}

    return api_request("POST", "comments", data)


# --- User operations ---


@mcp.tool()
def get_self() -> dict[str, Any]:
    """
    Get the bot user associated with the current token.

    Returns:
        Bot user object with name, type, and workspace info
    """
    return api_request("GET", "users/me")


@mcp.tool()
def get_users(
    page_size: int = 100,
    start_cursor: str | None = None,
) -> dict[str, Any]:
    """
    List all users in the workspace.

    Args:
        page_size: Number of results per page (max 100)
        start_cursor: Cursor for pagination

    Returns:
        List of user objects
    """
    params: dict[str, Any] = {"page_size": min(page_size, 100)}
    if start_cursor:
        params["start_cursor"] = start_cursor
    return api_request("GET", "users", params)


@mcp.tool()
def get_user(user_id: str) -> dict[str, Any]:
    """
    Get a user by ID.

    Args:
        user_id: The ID of the user

    Returns:
        User object
    """
    return api_request("GET", f"users/{user_id}")


# --- Database operations ---


@mcp.tool()
def create_database(
    parent_page_id: str,
    title: str,
    properties: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Create a new database (as a child of a page).

    Args:
        parent_page_id: The ID of the parent page
        title: Database title
        properties: Database property schema. Keys are property names,
                    values are property config objects, e.g.:
                    {"Name": {"title": {}}, "Tags": {"multi_select": {"options": []}}}

    Returns:
        Created database with ID and URL
    """
    data: dict[str, Any] = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"text": {"content": title}}],
        "properties": properties,
    }

    result = api_request("POST", "databases", data)
    if "error" in result:
        return result

    return {
        "id": result.get("id"),
        "url": result.get("url"),
        "title": title,
    }


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
