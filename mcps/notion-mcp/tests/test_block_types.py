"""Tests for block type builders and markdown parser."""

from notion_mcp.block_types import (
    build_paragraph,
    build_heading_1,
    build_heading_2,
    build_heading_3,
    build_bulleted_list_item,
    build_numbered_list_item,
    build_to_do,
    build_toggle,
    build_code,
    build_quote,
    build_callout,
    build_divider,
    build_table_of_contents,
    build_bookmark,
    build_image,
    build_embed,
    build_table,
    build_block,
    markdown_to_blocks,
)
import pytest


# --- Block builder tests ---


class TestBuildParagraph:
    def test_basic(self):
        result = build_paragraph("Hello world")
        assert result["type"] == "paragraph"
        assert result["paragraph"]["rich_text"][0]["text"]["content"] == "Hello world"

    def test_with_link(self):
        result = build_paragraph("Click here", link="https://example.com")
        assert result["paragraph"]["rich_text"][0]["text"]["link"] == {"url": "https://example.com"}

    def test_without_link(self):
        result = build_paragraph("No link")
        assert "link" not in result["paragraph"]["rich_text"][0]["text"]


class TestBuildHeadings:
    def test_h1(self):
        result = build_heading_1("Title")
        assert result["type"] == "heading_1"
        assert result["heading_1"]["rich_text"][0]["text"]["content"] == "Title"

    def test_h2(self):
        result = build_heading_2("Subtitle")
        assert result["type"] == "heading_2"

    def test_h3(self):
        result = build_heading_3("Section")
        assert result["type"] == "heading_3"


class TestBuildListItems:
    def test_bulleted(self):
        result = build_bulleted_list_item("Item")
        assert result["type"] == "bulleted_list_item"
        assert result["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Item"

    def test_numbered(self):
        result = build_numbered_list_item("Step 1")
        assert result["type"] == "numbered_list_item"


class TestBuildToDo:
    def test_unchecked(self):
        result = build_to_do("Task")
        assert result["to_do"]["checked"] is False

    def test_checked(self):
        result = build_to_do("Done task", checked=True)
        assert result["to_do"]["checked"] is True


class TestBuildCode:
    def test_default_language(self):
        result = build_code("print('hi')")
        assert result["code"]["language"] == "plain text"

    def test_custom_language(self):
        result = build_code("def foo(): pass", language="python")
        assert result["code"]["language"] == "python"


class TestBuildQuote:
    def test_basic(self):
        result = build_quote("Famous words")
        assert result["type"] == "quote"


class TestBuildCallout:
    def test_default_emoji(self):
        result = build_callout("Note")
        assert result["callout"]["icon"]["emoji"] == "💡"

    def test_custom_emoji(self):
        result = build_callout("Warning", emoji="⚠️")
        assert result["callout"]["icon"]["emoji"] == "⚠️"


class TestBuildDivider:
    def test_basic(self):
        result = build_divider()
        assert result == {"type": "divider", "divider": {}}


class TestBuildTableOfContents:
    def test_basic(self):
        result = build_table_of_contents()
        assert result == {"type": "table_of_contents", "table_of_contents": {}}


class TestBuildBookmark:
    def test_without_caption(self):
        result = build_bookmark("https://example.com")
        assert result["bookmark"]["url"] == "https://example.com"
        assert "caption" not in result["bookmark"]

    def test_with_caption(self):
        result = build_bookmark("https://example.com", caption="Example")
        assert result["bookmark"]["caption"][0]["text"]["content"] == "Example"


class TestBuildImage:
    def test_basic(self):
        result = build_image("https://example.com/img.png")
        assert result["image"]["type"] == "external"
        assert result["image"]["external"]["url"] == "https://example.com/img.png"

    def test_with_caption(self):
        result = build_image("https://example.com/img.png", caption="Photo")
        assert result["image"]["caption"][0]["text"]["content"] == "Photo"


class TestBuildEmbed:
    def test_basic(self):
        result = build_embed("https://youtube.com/watch?v=123")
        assert result["embed"]["url"] == "https://youtube.com/watch?v=123"


class TestBuildTable:
    def test_basic(self):
        result = build_table([["A", "B"], ["1", "2"]])
        assert result["table"]["table_width"] == 2
        assert len(result["table"]["children"]) == 2
        assert result["table"]["has_column_header"] is True

    def test_empty(self):
        result = build_table([])
        assert result["table"]["table_width"] == 1
        assert result["table"]["children"] == []

    def test_ragged_rows_padded(self):
        result = build_table([["A", "B", "C"], ["1"]])
        row2_cells = result["table"]["children"][1]["table_row"]["cells"]
        assert len(row2_cells) == 3
        assert row2_cells[1][0]["text"]["content"] == ""
        assert row2_cells[2][0]["text"]["content"] == ""

    def test_no_column_header(self):
        result = build_table([["A", "B"]], has_column_header=False)
        assert result["table"]["has_column_header"] is False

    def test_row_header(self):
        result = build_table([["A", "B"]], has_row_header=True)
        assert result["table"]["has_row_header"] is True


# --- build_block dispatch tests ---


class TestBuildBlock:
    def test_paragraph(self):
        result = build_block("paragraph", text="Hello")
        assert result["type"] == "paragraph"

    def test_heading_1(self):
        result = build_block("heading_1", text="Title")
        assert result["type"] == "heading_1"

    def test_code(self):
        result = build_block("code", code="x = 1", language="python")
        assert result["code"]["language"] == "python"

    def test_divider(self):
        result = build_block("divider")
        assert result["type"] == "divider"

    def test_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown block type"):
            build_block("nonexistent_type")


# --- Markdown parser tests ---


class TestMarkdownToBlocks:
    def test_heading_1(self):
        blocks = markdown_to_blocks("# Title")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "heading_1"

    def test_heading_2(self):
        blocks = markdown_to_blocks("## Subtitle")
        assert blocks[0]["type"] == "heading_2"

    def test_heading_3(self):
        blocks = markdown_to_blocks("### Section")
        assert blocks[0]["type"] == "heading_3"

    def test_bullet_list_dash(self):
        blocks = markdown_to_blocks("- Item one\n- Item two")
        assert len(blocks) == 2
        assert blocks[0]["type"] == "bulleted_list_item"

    def test_bullet_list_asterisk(self):
        blocks = markdown_to_blocks("* Item")
        assert blocks[0]["type"] == "bulleted_list_item"

    def test_numbered_list_single_digit(self):
        blocks = markdown_to_blocks("1. First\n2. Second")
        assert len(blocks) == 2
        assert blocks[0]["type"] == "numbered_list_item"

    def test_numbered_list_multi_digit(self):
        """Regression test: items 10+ must parse correctly."""
        blocks = markdown_to_blocks("10. Tenth item\n11. Eleventh\n100. Hundredth")
        assert len(blocks) == 3
        assert all(b["type"] == "numbered_list_item" for b in blocks)
        assert blocks[0]["numbered_list_item"]["rich_text"][0]["text"]["content"] == "Tenth item"
        assert blocks[2]["numbered_list_item"]["rich_text"][0]["text"]["content"] == "Hundredth"

    def test_numbered_list_paren_style(self):
        blocks = markdown_to_blocks("1) First")
        assert blocks[0]["type"] == "numbered_list_item"

    def test_quote(self):
        blocks = markdown_to_blocks("> Wise words")
        assert blocks[0]["type"] == "quote"

    def test_divider_dashes(self):
        blocks = markdown_to_blocks("---")
        assert blocks[0]["type"] == "divider"

    def test_divider_asterisks(self):
        blocks = markdown_to_blocks("***")
        assert blocks[0]["type"] == "divider"

    def test_divider_underscores(self):
        blocks = markdown_to_blocks("___")
        assert blocks[0]["type"] == "divider"

    def test_code_block(self):
        md = "```python\nprint('hello')\nx = 1\n```"
        blocks = markdown_to_blocks(md)
        assert len(blocks) == 1
        assert blocks[0]["type"] == "code"
        assert blocks[0]["code"]["language"] == "python"
        assert "print('hello')" in blocks[0]["code"]["rich_text"][0]["text"]["content"]

    def test_code_block_no_language(self):
        md = "```\nsome code\n```"
        blocks = markdown_to_blocks(md)
        assert blocks[0]["code"]["language"] == "plain text"

    def test_paragraph(self):
        blocks = markdown_to_blocks("Just some text")
        assert blocks[0]["type"] == "paragraph"

    def test_skip_empty_lines(self):
        blocks = markdown_to_blocks("\n\nHello\n\n")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "paragraph"

    def test_mixed_content(self):
        md = """# Title

Some paragraph text.

- Bullet one
- Bullet two

1. First
2. Second

> A quote

---

```python
x = 1
```"""
        blocks = markdown_to_blocks(md)
        types = [b["type"] for b in blocks]
        assert types == [
            "heading_1",
            "paragraph",
            "bulleted_list_item",
            "bulleted_list_item",
            "numbered_list_item",
            "numbered_list_item",
            "quote",
            "divider",
            "code",
        ]
