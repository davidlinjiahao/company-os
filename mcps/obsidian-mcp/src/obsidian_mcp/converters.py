"""Convert vault data to markdown for token efficiency."""
from datetime import datetime
from pathlib import Path
from typing import Any


def format_timestamp(ts: float | None) -> str:
    """Format Unix timestamp to readable date."""
    if ts is None:
        return "Unknown"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def file_list_to_markdown(files: list[dict[str, Any]], title: str = "Files") -> str:
    """Convert file list to markdown table.

    Args:
        files: List of file info dicts with name, path, modified, size
        title: Section title

    Returns:
        Markdown-formatted table
    """
    if not files:
        return f"No {title.lower()} found."

    lines = [f"## {title}", "", f"Found **{len(files)}** files:", ""]
    lines.append("| # | Name | Path | Modified | Size |")
    lines.append("|---|------|------|----------|------|")

    for i, f in enumerate(files, 1):
        name = f.get("name", "Untitled")
        rel_path = f.get("path", "")
        modified = format_timestamp(f.get("modified"))
        size = f.get("size", 0)
        size_str = f"{size / 1024:.1f}KB" if size >= 1024 else f"{size}B"
        lines.append(f"| {i} | {name} | `{rel_path}` | {modified} | {size_str} |")

    return "\n".join(lines)


def folder_tree_to_markdown(tree: dict[str, Any], title: str = "Folder Structure") -> str:
    """Convert folder tree to markdown.

    Args:
        tree: Nested dict with 'files' and 'folders' keys
        title: Section title

    Returns:
        Markdown-formatted tree
    """
    lines = [f"## {title}", ""]

    def render_level(node: dict, indent: int = 0) -> None:
        prefix = "  " * indent
        folders = node.get("folders", {})
        for name in sorted(folders):
            lines.append(f"{prefix}- **{name}/**")
            render_level(folders[name], indent + 1)
        for file in sorted(node.get("files", [])):
            lines.append(f"{prefix}- {file}")

    render_level(tree)
    return "\n".join(lines)


def search_results_to_markdown(
    results: list[dict[str, Any]], query: str, search_type: str = "content"
) -> str:
    """Convert search results to markdown.

    Args:
        results: List of matches with file, line, context
        query: Search query string
        search_type: Type of search (content, filename, tag)

    Returns:
        Markdown-formatted results
    """
    if not results:
        return f"No matches found for '{query}'."

    lines = [
        f"## Search Results: `{query}`",
        "",
        f"Found **{len(results)}** matches ({search_type} search):",
        "",
    ]

    for i, r in enumerate(results, 1):
        file_path = r.get("path", "unknown")
        lines.append(f"### {i}. `{file_path}`")

        if "matches" in r:
            for match in r["matches"][:3]:  # Limit context shown
                line_num = match.get("line", 0)
                context = match.get("context", "").strip()
                lines.append(f"- Line {line_num}: `{context[:100]}...`" if len(context) > 100 else f"- Line {line_num}: `{context}`")
        lines.append("")

    return "\n".join(lines)


def note_to_markdown(path: str, content: str, metadata: dict[str, Any] | None = None) -> str:
    """Format a note for display.

    Args:
        path: Relative path to the note
        content: Note content
        metadata: Optional file metadata

    Returns:
        Markdown-formatted note
    """
    lines = [f"# {Path(path).stem}", ""]

    if metadata:
        lines.append("**Metadata:**")
        if metadata.get("modified"):
            lines.append(f"- Modified: {format_timestamp(metadata['modified'])}")
        if metadata.get("size"):
            size = metadata["size"]
            lines.append(f"- Size: {size / 1024:.1f}KB" if size >= 1024 else f"- Size: {size}B")
        lines.append(f"- Path: `{path}`")
        if metadata.get("content_hash"):
            lines.append(f"- Content Hash: `{metadata['content_hash']}`")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(content)

    return "\n".join(lines)


def tags_to_markdown(tags: dict[str, int]) -> str:
    """Convert tag frequency dict to markdown.

    Args:
        tags: Dict of tag -> count

    Returns:
        Markdown-formatted tag list
    """
    if not tags:
        return "No tags found in vault."

    lines = ["## Tags in Vault", "", f"Found **{len(tags)}** unique tags:", ""]
    lines.append("| Tag | Count |")
    lines.append("|-----|-------|")

    for tag, count in sorted(tags.items(), key=lambda x: -x[1]):
        lines.append(f"| `{tag}` | {count} |")

    return "\n".join(lines)
