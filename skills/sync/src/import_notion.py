#!/usr/bin/env python3
"""
Notion to Obsidian Importer
Recursively imports a Notion page and all its children into Obsidian markdown.
Automatically organizes into subdirectories for pages with children.
"""

import json
import os
import re
import requests
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Get Notion token from environment
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("❌ Error: NOTION_TOKEN environment variable not set")
    print("Set it in ~/.claude/.env or export it in your shell")
    sys.exit(1)

NOTION_VERSION = "2022-06-28"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}


def sanitize_filename(name: str) -> str:
    """Convert title to valid filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:200] or "Untitled"


def rich_text_to_md(rich_text_array: List[Dict]) -> str:
    """Convert Notion rich text to markdown with formatting."""
    if not rich_text_array:
        return ""

    result = ""
    for rt in rich_text_array:
        text = rt.get("plain_text", "")
        annot = rt.get("annotations", {})

        if annot.get("code"):
            text = f"`{text}`"
        if annot.get("bold"):
            text = f"**{text}**"
        if annot.get("italic"):
            text = f"*{text}*"
        if annot.get("strikethrough"):
            text = f"~~{text}~~"
        if annot.get("underline"):
            text = f"<u>{text}</u>"

        href = rt.get("href")
        if not href:
            text_obj = rt.get("text") or {}
            link_obj = text_obj.get("link") or {}
            href = link_obj.get("url")
        if href:
            text = f"[{text}]({href})"

        color = annot.get("color", "default")
        if color != "default" and color != "gray":
            text = f'<span style="color:{color}">{text}</span>'

        result += text
    return result


def fetch_table_rows(table_id: str) -> List[List[str]]:
    """Fetch table rows from a table block."""
    try:
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            url = f"https://api.notion.com/v1/blocks/{table_id}/children?page_size=100"
            if start_cursor:
                url += f"&start_cursor={start_cursor}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            all_blocks.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        rows = []
        for block in all_blocks:
            if not block:
                continue
            if block.get("type") == "table_row":
                cells = block.get("table_row", {}).get("cells", [])
                row = [rich_text_to_md(cell) for cell in cells]
                rows.append(row)

        return rows
    except Exception as e:
        print(f"  ⚠️  Error fetching table rows: {e}")
        return []


def fetch_blocks_recursive(block_id: str, indent: int = 0) -> str:
    """Recursively fetch and convert blocks to markdown."""
    try:
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
            if start_cursor:
                url += f"&start_cursor={start_cursor}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            all_blocks.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        markdown = ""
        prefix = "  " * indent

        for block in all_blocks:
            if not block:
                continue
            block_type = block.get("type")
            if not block_type:
                continue
            block_data = block.get(block_type) or {}

            if block_type == "paragraph":
                text = rich_text_to_md(block_data.get("rich_text", []))
                if text:
                    markdown += f"{prefix}{text}\n\n"

            elif block_type in ["heading_1", "heading_2", "heading_3"]:
                level = int(block_type[-1])
                text = rich_text_to_md(block_data.get("rich_text", []))
                markdown += f"{'#' * level} {text}\n\n"

            elif block_type == "bulleted_list_item":
                text = rich_text_to_md(block_data.get("rich_text", []))
                markdown += f"{prefix}- {text}\n"
                if block.get("has_children"):
                    markdown += fetch_blocks_recursive(block["id"], indent + 1)

            elif block_type == "numbered_list_item":
                text = rich_text_to_md(block_data.get("rich_text", []))
                markdown += f"{prefix}1. {text}\n"
                if block.get("has_children"):
                    markdown += fetch_blocks_recursive(block["id"], indent + 1)

            elif block_type == "to_do":
                text = rich_text_to_md(block_data.get("rich_text", []))
                checked = "x" if block_data.get("checked") else " "
                markdown += f"{prefix}- [{checked}] {text}\n"

            elif block_type == "toggle":
                text = rich_text_to_md(block_data.get("rich_text", []))
                markdown += f"\n{prefix}<details>\n{prefix}<summary>{text}</summary>\n\n"
                if block.get("has_children"):
                    markdown += fetch_blocks_recursive(block["id"], indent)
                markdown += f"{prefix}</details>\n\n"

            elif block_type == "quote":
                text = rich_text_to_md(block_data.get("rich_text", []))
                markdown += f"> {text}\n\n"

            elif block_type == "callout":
                icon = block_data.get("icon") or {}
                emoji = icon.get("emoji", "💡") if icon.get("type") == "emoji" else "💡"
                text = rich_text_to_md(block_data.get("rich_text", []))
                markdown += f"> {emoji} {text}\n\n"

            elif block_type == "code":
                code_text = "".join(rt.get("plain_text", "") for rt in block_data.get("rich_text", []))
                language = block_data.get("language", "").lower() or ""
                markdown += f"```{language}\n{code_text}\n```\n\n"

            elif block_type == "divider":
                markdown += f"{prefix}---\n\n"

            elif block_type == "table":
                table_rows = fetch_table_rows(block["id"])
                if table_rows:
                    has_header = block_data.get("has_column_header", False)

                    if has_header and len(table_rows) > 0:
                        markdown += "| " + " | ".join(table_rows[0]) + " |\n"
                        markdown += "| " + " | ".join(["---"] * len(table_rows[0])) + " |\n"
                        for row in table_rows[1:]:
                            markdown += "| " + " | ".join(row) + " |\n"
                    else:
                        for row in table_rows:
                            markdown += "| " + " | ".join(row) + " |\n"

                    markdown += "\n"

            elif block_type == "image":
                img = block_data
                url = ""
                if img.get("type") == "external":
                    external = img.get("external") or {}
                    url = external.get("url", "")
                elif img.get("type") == "file":
                    file_obj = img.get("file") or {}
                    url = file_obj.get("url", "")
                caption = rich_text_to_md(img.get("caption", []))
                markdown += f"![{caption}]({url})\n\n"

            elif block_type == "bookmark":
                url = block_data.get("url", "")
                caption = rich_text_to_md(block_data.get("caption", []))
                markdown += f"[{caption or url}]({url})\n\n"

        return markdown

    except Exception as e:
        return f"<!-- Error fetching blocks: {e} -->\n\n"


def fetch_page(page_id: str) -> Optional[Dict]:
    """Fetch a page from Notion."""
    try:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ❌ Error fetching page {page_id}: {e}")
        return None


def get_page_title(page: Dict) -> str:
    """Extract title from page properties."""
    props = page.get("properties", {})
    for prop_name, prop_data in props.items():
        if prop_data.get("type") == "title":
            title_array = prop_data.get("title", [])
            if title_array:
                return "".join([rt.get("plain_text", "") for rt in title_array])
    return "Untitled"


def query_database(database_id: str, page_size: int = 100) -> List[Dict]:
    """Query all entries from a database."""
    try:
        url = f"https://api.notion.com/v1/databases/{database_id}/query"

        all_results = []
        has_more = True
        start_cursor = None

        while has_more:
            payload = {"page_size": page_size}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            all_results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        return all_results
    except Exception as e:
        print(f"  ⚠️  Error querying database: {e}")
        return []


def format_property_value(prop_name: str, prop_data: Dict) -> Any:
    """Format a property value for frontmatter."""
    prop_type = prop_data.get("type")

    if prop_type == "title":
        return rich_text_to_md(prop_data.get("title", []))
    elif prop_type == "rich_text":
        return rich_text_to_md(prop_data.get("rich_text", []))
    elif prop_type == "select":
        select = prop_data.get("select")
        return select.get("name") if select else None
    elif prop_type == "multi_select":
        return ", ".join([s.get("name", "") for s in prop_data.get("multi_select", [])])
    elif prop_type == "date":
        date = prop_data.get("date")
        return date.get("start") if date else None
    elif prop_type == "people":
        return ", ".join([p.get("name", "") for p in prop_data.get("people", [])])
    elif prop_type == "url":
        return prop_data.get("url")
    elif prop_type == "email":
        return prop_data.get("email")
    elif prop_type == "phone_number":
        return prop_data.get("phone_number")
    elif prop_type == "number":
        return prop_data.get("number")
    elif prop_type == "checkbox":
        return prop_data.get("checkbox")
    elif prop_type == "status":
        status = prop_data.get("status")
        return status.get("name") if status else None
    elif prop_type == "created_time":
        return prop_data.get("created_time")
    elif prop_type == "last_edited_time":
        return prop_data.get("last_edited_time")

    return None


def create_markdown_file(page: Dict, output_dir: Path, fetch_content: bool = True):
    """Create a markdown file from a Notion page."""
    page_id = page.get("id", "")
    title = get_page_title(page)
    safe_title = sanitize_filename(title)

    # Build frontmatter
    frontmatter = f"""---
source: notion
notion_id: {page_id}
created_time: {page.get("created_time", "")}
last_edited_time: {page.get("last_edited_time", "")}
"""

    # Add properties
    props = page.get("properties", {})
    for prop_name, prop_data in props.items():
        if prop_name == "title":
            continue
        value = format_property_value(prop_name, prop_data)
        if value is not None:
            value_escaped = str(value).replace('"', '\\"')
            frontmatter += f'{prop_name}: "{value_escaped}"\n'

    frontmatter += "---\n\n"

    # Fetch content
    content = f"# {title}\n\n"
    if fetch_content:
        content += fetch_blocks_recursive(page_id)

    # Write file
    file_path = output_dir / f"{safe_title}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter + content)

    return file_path


def get_page_children(page_id: str) -> Tuple[List[str], List[str]]:
    """Get child page IDs and child database IDs for a page."""
    try:
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
            if start_cursor:
                url += f"&start_cursor={start_cursor}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            all_blocks.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        child_pages = []
        child_databases = []

        for block in all_blocks:
            if not block:
                continue

            block_type = block.get("type")

            if block_type == "child_page":
                child_pages.append(block.get("id"))
            elif block_type == "child_database":
                child_databases.append(block.get("id"))

        return child_pages, child_databases

    except Exception as e:
        print(f"  ⚠️  Error fetching children: {e}")
        return [], []


def import_page_recursive(page_id: str, output_dir: Path, visited: set = None, import_stats: Dict = None):
    """Recursively import a page and all its children with hierarchical organization."""
    if visited is None:
        visited = set()
    if import_stats is None:
        import_stats = {"success": [], "failed": [], "databases": []}

    if page_id in visited:
        return

    visited.add(page_id)

    # Fetch the page
    page = fetch_page(page_id)
    if not page:
        import_stats["failed"].append({"id": page_id, "reason": "Failed to fetch page"})
        return

    title = get_page_title(page)
    print(f"  📄 Importing: {title}")

    try:
        # Check if page has children
        child_pages, child_databases = get_page_children(page_id)
        has_children = len(child_pages) > 0 or len(child_databases) > 0

        if has_children:
            # Create subdirectory for this page
            safe_title = sanitize_filename(title)
            page_dir = output_dir / safe_title
            page_dir.mkdir(exist_ok=True)

            # Create the parent page inside its subdirectory
            file_path = create_markdown_file(page, page_dir)
            import_stats["success"].append({
                "id": page_id,
                "title": title,
                "path": str(file_path),
                "has_children": True
            })

            # Import all child pages into this subdirectory
            for child_id in child_pages:
                import_page_recursive(child_id, page_dir, visited, import_stats)

            # Import all child databases into this subdirectory
            for db_id in child_databases:
                import_database(db_id, page_dir, visited, import_stats)

        else:
            # No children - create page at current level
            file_path = create_markdown_file(page, output_dir)
            import_stats["success"].append({
                "id": page_id,
                "title": title,
                "path": str(file_path),
                "has_children": False
            })

    except Exception as e:
        import_stats["failed"].append({
            "id": page_id,
            "title": title if 'title' in locals() else page_id,
            "reason": str(e)
        })
        print(f"  ❌ Error importing {title if 'title' in locals() else page_id}: {e}")


def import_database(database_id: str, output_dir: Path, visited: set = None, import_stats: Dict = None):
    """Import all entries from a database."""
    if visited is None:
        visited = set()
    if import_stats is None:
        import_stats = {"success": [], "failed": [], "databases": []}

    if database_id in visited:
        return

    visited.add(database_id)

    print(f"  🗄️  Importing database entries...")

    # Query database
    entries = query_database(database_id)

    if not entries:
        print(f"    No entries found")
        import_stats["databases"].append({
            "id": database_id,
            "title": "Unknown",
            "entries": 0,
            "status": "empty"
        })
        return

    print(f"    Found {len(entries)} entries")

    # Create database subdirectory
    # Fetch database title
    try:
        url = f"https://api.notion.com/v1/databases/{database_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        db_data = response.json()
        db_title = rich_text_to_md(db_data.get("title", []))
        safe_db_title = sanitize_filename(db_title or "Database")

        db_dir = output_dir / safe_db_title
        db_dir.mkdir(exist_ok=True)

        # Import each entry
        entry_count = 0
        for entry in entries:
            create_markdown_file(entry, db_dir)
            entry_count += 1

        import_stats["databases"].append({
            "id": database_id,
            "title": db_title,
            "entries": entry_count,
            "status": "success",
            "path": str(db_dir)
        })

    except Exception as e:
        print(f"    ⚠️  Error: {e}")
        import_stats["databases"].append({
            "id": database_id,
            "title": db_title if 'db_title' in locals() else "Unknown",
            "entries": 0,
            "status": "failed",
            "error": str(e)
        })


def verify_imported_files(output_dir: Path, import_stats: Dict) -> Dict:
    """Verify all imported files are valid and complete."""
    print(f"\n🔍 Running import verification...")

    verification_results = {
        "total_files": 0,
        "valid_files": 0,
        "empty_files": [],
        "error_files": [],
        "missing_content": []
    }

    # Check all markdown files
    for md_file in output_dir.rglob("*.md"):
        verification_results["total_files"] += 1

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if file is empty or too small
            if len(content) < 50:
                verification_results["empty_files"].append(str(md_file.relative_to(output_dir)))
                continue

            # Check for error messages in content
            if "Error fetching blocks:" in content or "Error fetching page" in content:
                verification_results["error_files"].append(str(md_file.relative_to(output_dir)))
                continue

            # Check if file has only frontmatter and title (no actual content)
            lines = content.split('\n')
            content_lines = [l for l in lines if l.strip() and not l.startswith('---') and not l.startswith('#') and not l.startswith('source:') and not l.startswith('notion_id:') and not l.startswith('created_time:') and not l.startswith('last_edited_time:')]

            if len(content_lines) == 0:
                verification_results["missing_content"].append(str(md_file.relative_to(output_dir)))
            else:
                verification_results["valid_files"] += 1

        except Exception as e:
            verification_results["error_files"].append(f"{md_file.relative_to(output_dir)} (Error: {e})")

    return verification_results


def print_evaluation_report(import_stats: Dict, verification_results: Dict, output_dir: Path):
    """Print comprehensive evaluation report."""
    print(f"\n{'='*60}")
    print(f"📋 IMPORT EVALUATION REPORT")
    print(f"{'='*60}")

    # Import statistics
    print(f"\n📊 Import Statistics:")
    print(f"  ✅ Successfully imported pages: {len(import_stats['success'])}")
    print(f"  ❌ Failed pages: {len(import_stats['failed'])}")
    print(f"  🗄️  Databases imported: {len(import_stats['databases'])}")

    total_db_entries = sum(db['entries'] for db in import_stats['databases'] if db['status'] == 'success')
    print(f"  📄 Total database entries: {total_db_entries}")

    # File verification
    print(f"\n🔍 File Verification:")
    print(f"  📁 Total files created: {verification_results['total_files']}")
    print(f"  ✅ Valid files with content: {verification_results['valid_files']}")
    print(f"  ⚠️  Empty or minimal files: {len(verification_results['empty_files'])}")
    print(f"  ❌ Files with errors: {len(verification_results['error_files'])}")
    print(f"  📝 Files missing content: {len(verification_results['missing_content'])}")

    # Failed imports
    if import_stats['failed']:
        print(f"\n❌ Failed Imports:")
        for failure in import_stats['failed']:
            print(f"  - {failure.get('title', failure['id'])}: {failure['reason']}")

    # Empty files
    if verification_results['empty_files']:
        print(f"\n⚠️  Empty Files (may be legitimately empty in Notion):")
        for file in verification_results['empty_files'][:10]:  # Show first 10
            print(f"  - {file}")
        if len(verification_results['empty_files']) > 10:
            print(f"  ... and {len(verification_results['empty_files']) - 10} more")

    # Error files
    if verification_results['error_files']:
        print(f"\n❌ Files with Errors:")
        for file in verification_results['error_files']:
            print(f"  - {file}")

    # Database details
    if import_stats['databases']:
        print(f"\n🗄️  Database Details:")
        for db in import_stats['databases']:
            status_icon = "✅" if db['status'] == 'success' else "❌"
            print(f"  {status_icon} {db['title']}: {db['entries']} entries")

    # Overall success rate
    total_attempts = len(import_stats['success']) + len(import_stats['failed'])
    success_rate = (len(import_stats['success']) / total_attempts * 100) if total_attempts > 0 else 0

    print(f"\n{'='*60}")
    print(f"📈 Overall Success Rate: {success_rate:.1f}%")
    print(f"📁 Output Location: {output_dir}")
    print(f"{'='*60}\n")


def main():
    """Main import function."""
    if len(sys.argv) < 3:
        print("Usage: python3 import_notion.py <page_id> <output_directory> [--resume]")
        print("Example: python3 import_notion.py abcd1234-5678-9012-3456-7890abcdef12 /path/to/output/MyPage")
        print("  --resume: Add files to existing directory without backup/clear")
        sys.exit(1)

    page_id = sys.argv[1].replace("-", "")
    output_dir = Path(sys.argv[2]).expanduser()
    resume_mode = "--resume" in sys.argv

    # Create backup if directory exists (skip in resume mode)
    if output_dir.exists() and not resume_mode:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = output_dir.parent / f"{output_dir.name}_backup_{timestamp}"
        print(f"📦 Creating backup: {backup_dir.name}")
        import shutil
        shutil.copytree(output_dir, backup_dir)

        # Clear output directory
        shutil.rmtree(output_dir)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 Starting import from Notion...")
    print(f"📍 Output: {output_dir}\n")

    # Initialize import statistics
    import_stats = {"success": [], "failed": [], "databases": []}

    # Start recursive import with statistics tracking
    import_page_recursive(page_id, output_dir, import_stats=import_stats)

    # Verify imported files
    verification_results = verify_imported_files(output_dir, import_stats)

    # Print comprehensive evaluation report
    print_evaluation_report(import_stats, verification_results, output_dir)


if __name__ == "__main__":
    main()
