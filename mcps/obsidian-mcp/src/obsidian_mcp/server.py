"""Obsidian Vault MCP Server."""
import logging
import sys

from mcp.server.fastmcp import FastMCP

from .config import config
from .vault_client import VaultError, client

logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

mcp = FastMCP(name="obsidian-mcp")


# --- Read Tools ---


@mcp.tool()
def read_note(path: str) -> str:
    """Read a note from the Obsidian vault.

    Args:
        path: Relative path to the note (e.g., "GTD/GTD.md" or "knowledge/topic")

    Returns:
        Markdown-formatted note content with metadata
    """
    try:
        return client.read_note(path)
    except VaultError as e:
        return f"Error: {e.message}"


@mcp.tool()
def list_folder(folder: str = "", recursive: bool = False) -> str:
    """List markdown files in a folder.

    Args:
        folder: Relative folder path (empty for vault root)
        recursive: Include files from subfolders

    Returns:
        Markdown-formatted list of files with metadata
    """
    try:
        return client.list_folder(folder, recursive)
    except VaultError as e:
        return f"Error: {e.message}"


@mcp.tool()
def get_structure(folder: str = "", max_depth: int = 3) -> str:
    """Get the folder tree structure.

    Args:
        folder: Starting folder (empty for vault root)
        max_depth: Maximum depth to traverse (default 3)

    Returns:
        Markdown-formatted folder tree
    """
    try:
        return client.get_folder_structure(folder, max_depth)
    except VaultError as e:
        return f"Error: {e.message}"


@mcp.tool()
def search(query: str, folder: str = "", limit: int = 20) -> str:
    """Search for text within notes.

    Args:
        query: Text to search for (case-insensitive)
        folder: Limit search to specific folder
        limit: Maximum results to return (default 20)

    Returns:
        Markdown-formatted search results with context
    """
    try:
        return client.search_content(query, folder, limit)
    except VaultError as e:
        return f"Error: {e.message}"


@mcp.tool()
def search_files(query: str, folder: str = "", limit: int = 20) -> str:
    """Search for notes by filename.

    Args:
        query: Filename pattern to search for (case-insensitive)
        folder: Limit search to specific folder
        limit: Maximum results to return (default 20)

    Returns:
        Markdown-formatted list of matching files
    """
    try:
        return client.search_filename(query, folder, limit)
    except VaultError as e:
        return f"Error: {e.message}"


@mcp.tool()
def list_tags(tag: str | None = None) -> str:
    """List all tags in the vault or find notes with a specific tag.

    Args:
        tag: Specific tag to search for (without #), or None to list all tags

    Returns:
        Markdown-formatted tag list or files with the specified tag
    """
    try:
        return client.search_tags(tag)
    except VaultError as e:
        return f"Error: {e.message}"


@mcp.tool()
def get_recent(limit: int = 10) -> str:
    """Get recently modified notes.

    Args:
        limit: Number of recent notes to return (default 10)

    Returns:
        Markdown-formatted list of recent notes
    """
    try:
        return client.get_recent(limit)
    except VaultError as e:
        return f"Error: {e.message}"


# --- Write Tools ---


@mcp.tool()
def create_note(path: str, content: str) -> str:
    """Create a new note in the vault.

    Args:
        path: Relative path for the new note (e.g., "knowledge/new-topic")
        content: Content for the note (markdown)

    Returns:
        Confirmation message or error
    """
    try:
        return client.create_note(path, content)
    except VaultError as e:
        return f"Error: {e.message}"


@mcp.tool()
def update_note(path: str, content: str, expected_hash: str | None = None) -> str:
    """Replace the content of an existing note.

    Args:
        path: Relative path to the note
        content: New content for the note
        expected_hash: Optional content_hash from a previous read_note call.
            If provided, the update will fail if the file was modified since
            that read, preventing accidental overwrites of concurrent edits.

    Returns:
        Confirmation message or error
    """
    try:
        return client.update_note(path, content, expected_hash=expected_hash)
    except VaultError as e:
        return f"Error: {e.message}"


@mcp.tool()
def append_to_note(path: str, content: str) -> str:
    """Append content to an existing note.

    Args:
        path: Relative path to the note
        content: Content to append

    Returns:
        Confirmation message or error
    """
    try:
        return client.append_to_note(path, content)
    except VaultError as e:
        return f"Error: {e.message}"


@mcp.tool()
def rename_note(old_path: str, new_path: str) -> str:
    """Rename or move a note.

    Args:
        old_path: Current path of the note
        new_path: New path for the note

    Returns:
        Confirmation message or error
    """
    try:
        return client.rename_note(old_path, new_path)
    except VaultError as e:
        return f"Error: {e.message}"


def main():
    """Main entry point."""
    if not config.vault.exists():
        logger.error(f"Vault not found: {config.vault_path}")
        logger.error("Set OBSIDIAN_VAULT_PATH environment variable or check config.")
        sys.exit(1)

    logger.info(f"Starting Obsidian MCP server for vault: {config.vault_path}")

    transport = "stdio"
    if "--http" in sys.argv:
        transport = "streamable-http"

    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
