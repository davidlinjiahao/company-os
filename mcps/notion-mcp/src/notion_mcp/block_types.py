"""Block type builders for Notion page content."""

import re
from typing import Any


def build_paragraph(text: str, link: str | None = None) -> dict:
    """Build paragraph block."""
    text_obj = {"type": "text", "text": {"content": text}}
    if link:
        text_obj["text"]["link"] = {"url": link}
    return {
        "type": "paragraph",
        "paragraph": {"rich_text": [text_obj]}
    }


def build_heading_1(text: str) -> dict:
    """Build heading_1 block."""
    return {
        "type": "heading_1",
        "heading_1": {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }


def build_heading_2(text: str) -> dict:
    """Build heading_2 block."""
    return {
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }


def build_heading_3(text: str) -> dict:
    """Build heading_3 block."""
    return {
        "type": "heading_3",
        "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }


def build_bulleted_list_item(text: str) -> dict:
    """Build bulleted_list_item block."""
    return {
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }


def build_numbered_list_item(text: str) -> dict:
    """Build numbered_list_item block."""
    return {
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }


def build_to_do(text: str, checked: bool = False) -> dict:
    """Build to_do block."""
    return {
        "type": "to_do",
        "to_do": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "checked": checked
        }
    }


def build_toggle(text: str) -> dict:
    """Build toggle block."""
    return {
        "type": "toggle",
        "toggle": {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }


def build_code(code: str, language: str = "plain text") -> dict:
    """Build code block."""
    return {
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": code}}],
            "language": language
        }
    }


def build_quote(text: str) -> dict:
    """Build quote block."""
    return {
        "type": "quote",
        "quote": {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }


def build_callout(text: str, emoji: str = "💡") -> dict:
    """Build callout block."""
    return {
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "icon": {"type": "emoji", "emoji": emoji}
        }
    }


def build_divider() -> dict:
    """Build divider block."""
    return {"type": "divider", "divider": {}}


def build_table_of_contents() -> dict:
    """Build table_of_contents block."""
    return {"type": "table_of_contents", "table_of_contents": {}}


def build_bookmark(url: str, caption: str | None = None) -> dict:
    """Build bookmark block."""
    block = {
        "type": "bookmark",
        "bookmark": {"url": url}
    }
    if caption:
        block["bookmark"]["caption"] = [{"type": "text", "text": {"content": caption}}]
    return block


def build_image(url: str, caption: str | None = None) -> dict:
    """Build image block from external URL."""
    block = {
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": url}
        }
    }
    if caption:
        block["image"]["caption"] = [{"type": "text", "text": {"content": caption}}]
    return block


def build_embed(url: str) -> dict:
    """Build embed block."""
    return {
        "type": "embed",
        "embed": {"url": url}
    }


def build_table(rows: list[list[str]], has_column_header: bool = True, has_row_header: bool = False) -> dict:
    """
    Build table block with rows.

    Args:
        rows: List of rows, each row is list of cell strings
        has_column_header: First row is header
        has_row_header: First column is header

    Returns:
        Table block with children
    """
    if not rows:
        return {"type": "table", "table": {"table_width": 1, "children": []}}

    width = len(rows[0])

    table_rows = []
    for row in rows:
        cells = []
        for cell in row:
            cells.append([{"type": "text", "text": {"content": str(cell)}}])
        # Pad if needed
        while len(cells) < width:
            cells.append([{"type": "text", "text": {"content": ""}}])
        table_rows.append({
            "type": "table_row",
            "table_row": {"cells": cells}
        })

    return {
        "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": has_column_header,
            "has_row_header": has_row_header,
            "children": table_rows
        }
    }


# Block type to builder mapping
BLOCK_BUILDERS = {
    "paragraph": build_paragraph,
    "heading_1": build_heading_1,
    "heading_2": build_heading_2,
    "heading_3": build_heading_3,
    "bulleted_list_item": build_bulleted_list_item,
    "numbered_list_item": build_numbered_list_item,
    "to_do": build_to_do,
    "toggle": build_toggle,
    "code": build_code,
    "quote": build_quote,
    "callout": build_callout,
    "divider": build_divider,
    "table_of_contents": build_table_of_contents,
    "bookmark": build_bookmark,
    "image": build_image,
    "embed": build_embed,
    "table": build_table,
}


def build_block(block_type: str, **kwargs) -> dict:
    """
    Build a Notion block from type and arguments.

    Args:
        block_type: Type of block to build
        **kwargs: Arguments for the block builder

    Returns:
        Notion block object
    """
    builder = BLOCK_BUILDERS.get(block_type)
    if not builder:
        raise ValueError(f"Unknown block type: {block_type}")
    return builder(**kwargs)


def markdown_to_blocks(markdown: str) -> list[dict]:
    """
    Convert simple markdown to Notion blocks.

    Supports:
    - # Headings (h1, h2, h3)
    - - Bullet lists
    - 1. Numbered lists
    - > Quotes
    - ``` Code blocks
    - --- Dividers
    - Regular paragraphs

    Args:
        markdown: Markdown text

    Returns:
        List of Notion blocks
    """
    blocks = []
    lines = markdown.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip empty lines
        if not line.strip():
            i += 1
            continue

        # Code block
        if line.strip().startswith("```"):
            lang = line.strip()[3:] or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append(build_code("\n".join(code_lines), lang))
            i += 1
            continue

        # Headings
        if line.startswith("### "):
            blocks.append(build_heading_3(line[4:]))
        elif line.startswith("## "):
            blocks.append(build_heading_2(line[3:]))
        elif line.startswith("# "):
            blocks.append(build_heading_1(line[2:]))

        # Lists
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            blocks.append(build_bulleted_list_item(line.strip()[2:]))
        elif re.match(r'^\d+[.)] ', line.strip()):
            text = re.sub(r'^\d+[.)] ', '', line.strip())
            blocks.append(build_numbered_list_item(text))

        # Quote
        elif line.strip().startswith("> "):
            blocks.append(build_quote(line.strip()[2:]))

        # Divider
        elif line.strip() in ("---", "***", "___"):
            blocks.append(build_divider())

        # Regular paragraph
        else:
            blocks.append(build_paragraph(line))

        i += 1

    return blocks
