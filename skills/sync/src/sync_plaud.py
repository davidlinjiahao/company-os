#!/usr/bin/env python3
"""Sync Plaud transcripts to Obsidian vault.

Uses the PlaudClient from the plaud-mcp package to fetch transcripts and
summaries via Plaud Desktop's Chrome DevTools Protocol interface.

Usage:
    cd /path/to/company-os/mcps/plaud-mcp
    uv run python3 /path/to/skills/sync/src/sync_plaud.py [--days N] [--dry-run] [--limit N]
    uv run python3 /path/to/skills/sync/src/sync_plaud.py --refresh-titles [--dry-run]
    uv run python3 /path/to/skills/sync/src/sync_plaud.py --cleanup [--dry-run]

Modes:
    Default:          Fetch new Plaud transcripts and write them to Obsidian.
    --refresh-titles: Fix files with placeholder titles (timestamps or 'Recording')
                      by fetching the current title from Plaud.
    --cleanup:        Find and remove duplicate files (by plaud_id, transcript
                      content, and old-format naming).

Requirements:
    - Plaud Desktop must be running and logged in
    - Run from the plaud-mcp directory (for uv to resolve dependencies)
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure plaud-mcp package is importable (when not installed via uv)
# Prefer cwd/src (script is always run from plaud-mcp dir via uv run)
_cwd_src = os.path.join(os.getcwd(), "src")
if os.path.isdir(_cwd_src) and _cwd_src not in sys.path:
    sys.path.insert(0, _cwd_src)

from plaud_mcp.plaud_client import PlaudClient

# Force line-buffered stdout so progress is visible in non-TTY contexts (e.g., uv run)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

def _detect_obsidian_vault() -> Path:
    """Detect the active Obsidian vault path from Obsidian's config."""
    obsidian_config = Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json"
    if obsidian_config.exists():
        try:
            data = json.loads(obsidian_config.read_text())
            vaults = data.get("vaults", {})
            # Prefer the vault marked as open, otherwise take the most recently used
            for v in sorted(vaults.values(), key=lambda x: x.get("ts", 0), reverse=True):
                if v.get("open"):
                    return Path(v["path"])
            # No open vault — use the most recent
            if vaults:
                best = max(vaults.values(), key=lambda x: x.get("ts", 0))
                return Path(best["path"])
        except (json.JSONDecodeError, KeyError):
            pass
    # Fallback
    return Path.home() / "Documents" / "ObsidianVault"

OBSIDIAN_DIR = Path(os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    str(_detect_obsidian_vault())
)) / "Transcripts" / "Plaud"

# ---------- normalize raw Plaud API response ----------

def _format_timestamp(ts):
    if not ts:
        return ""
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()


def _format_duration(ms):
    if not ms:
        return ""
    seconds = ms // 1000
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def normalize_file(raw: dict) -> dict:
    """Normalize raw Plaud API file dict to the format the sync script expects."""
    return {
        "id": raw.get("id"),
        "filename": raw.get("filename"),
        "date": _format_timestamp(raw.get("start_time")),
        "duration": _format_duration(raw.get("duration")),
        "has_transcript": raw.get("is_trans", False),
        "has_summary": raw.get("is_summary", False),
        "start_time": raw.get("start_time", 0),
    }


# ---------- filename helpers ----------

def slugify(text: str, max_len: int = 60) -> str:
    """Convert title to a safe filename slug."""
    text = re.sub(r'\[.*?\]\s*', '', text)
    text = re.sub(r'^\d{2}-\d{2}\s+', '', text)
    text = text.strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_len].strip()


def make_filename(plaud_file: dict) -> str:
    """Generate Obsidian filename from Plaud file metadata."""
    date = plaud_file["date"][:10]
    title = slugify(plaud_file["filename"])
    if not title or title == date:
        title = "Recording"
    return f"{date} - {title}.md"


def extract_title(filename: str) -> str:
    """Extract display title from Plaud filename."""
    return re.sub(r'\[.*?\]\s*', '', filename).strip()

# ---------- deduplication ----------

def read_frontmatter(path: Path) -> dict:
    """Read YAML frontmatter from a markdown file. Returns {} on failure."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def get_existing_plaud_ids() -> set[str]:
    """Scan existing Obsidian files and return all plaud_ids from frontmatter."""
    ids = set()
    for path in OBSIDIAN_DIR.glob("*.md"):
        fm = read_frontmatter(path)
        pid = fm.get("plaud_id")
        if pid:
            ids.add(pid)
    return ids


def normalize(s: str) -> str:
    """Normalize a string for fuzzy matching."""
    s = re.sub(r'\[.*?\]\s*', '', s)
    s = re.sub(r'^\d{2,4}-\d{2}(-\d{2})?\s*', '', s)
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def extract_keywords(s: str) -> set:
    """Extract significant keywords (3+ chars) from a string."""
    return set(w for w in normalize(s).split() if len(w) >= 3)


def find_existing_matches(plaud_files: list, known_ids: set[str]) -> set:
    """Return set of Plaud IDs that already have matching Obsidian files.

    Uses plaud_id from frontmatter first (exact), then falls back to
    fuzzy keyword matching ONLY against old-format files that lack plaud_id.
    """
    matched_ids = set()

    # 1. Exact match by plaud_id in frontmatter
    for pf in plaud_files:
        if pf["id"] in known_ids:
            matched_ids.add(pf["id"])

    # 2. Fuzzy keyword match only against old-format files (no plaud_id)
    remaining = [pf for pf in plaud_files if pf["id"] not in matched_ids]
    if remaining:
        # Only consider Obsidian files that DON'T have a plaud_id (old-format)
        old_format_names = []
        for path in OBSIDIAN_DIR.glob("*.md"):
            fm = read_frontmatter(path)
            if not fm.get("plaud_id"):
                old_format_names.append(path.stem.lower())

        if old_format_names:
            for pf in remaining:
                plaud_keywords = extract_keywords(pf["filename"])
                if len(plaud_keywords) < 3:
                    continue
                for existing_name in old_format_names:
                    existing_keywords = extract_keywords(existing_name)
                    if len(existing_keywords) < 3:
                        continue
                    overlap = plaud_keywords & existing_keywords
                    if len(overlap) >= 3:
                        matched_ids.add(pf["id"])
                        break

    return matched_ids


def format_transcript(entries: list) -> str:
    """Format transcript entries into markdown."""
    lines = []
    prev_speaker = None
    for entry in entries:
        speaker = entry.get("speaker", entry.get("original_speaker", "Unknown"))
        content = entry.get("content", "").strip()
        if not content:
            continue
        if speaker != prev_speaker:
            if prev_speaker is not None:
                lines.append("")
            lines.append(f"**{speaker}:** {content}")
        else:
            lines[-1] += " " + content
        prev_speaker = speaker
    return "\n".join(lines)


def build_markdown(plaud_file: dict, summary_text: str, transcript_text: str) -> str:
    """Build the full markdown document."""
    date = plaud_file["date"][:10]
    title = extract_title(plaud_file["filename"])
    plaud_id = plaud_file["id"]
    duration = plaud_file.get("duration", "unknown")

    author = os.environ.get("USER") or Path.home().name

    return f"""---
author: {author}
date: {date}
source: plaud
plaud_id: {plaud_id}
duration: {duration}
tags: [meeting, transcript, auto-ingest]
---

# {title}

## Summary
{summary_text}

## Transcript
{transcript_text}
"""


async def sync_file(client: PlaudClient, plaud_file: dict, dry_run: bool = False) -> dict:
    """Sync a single Plaud file to Obsidian."""
    filename = make_filename(plaud_file)
    output_path = OBSIDIAN_DIR / filename
    plaud_id = plaud_file["id"]

    if output_path.exists():
        return {"id": plaud_id, "status": "skipped", "reason": "file exists", "path": str(output_path)}

    if dry_run:
        return {"id": plaud_id, "status": "dry_run", "path": str(output_path)}

    try:
        transcript = await client.get_transcript(plaud_id)
        transcript_text = format_transcript(transcript)

        summary_text = "No summary available."
        if plaud_file.get("has_summary", False):
            try:
                summary = await client.get_summary(plaud_id)
                summary_text = summary.get("ai_content", "No summary available.")
            except Exception as e:
                summary_text = f"Summary fetch failed: {e}"

        md = build_markdown(plaud_file, summary_text, transcript_text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md, encoding="utf-8")

        return {
            "id": plaud_id,
            "status": "synced",
            "path": str(output_path),
            "size": len(md),
            "transcript_entries": len(transcript),
        }
    except Exception as e:
        return {"id": plaud_id, "status": "error", "error": str(e)}


def get_first_transcript_line(path: Path, chars: int = 120) -> str:
    """Extract the first transcript line from a file for content comparison."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    m = re.search(r'## Transcript\n+(.*?)(?:\n\n|\Z)', text, re.DOTALL)
    return m.group(1)[:chars].strip() if m else ""


def is_placeholder_title(filename: str) -> bool:
    """Check if a filename has a placeholder title (timestamp or 'Recording')."""
    m = re.match(r'^\d{4}-\d{2}-\d{2} - (.+)\.md$', filename)
    if not m:
        return False
    title = m.group(1)
    # Timestamp titles like "2026-02-24 195227"
    if re.match(r'^\d{4}-\d{2}-\d{2} \d{6}$', title):
        return True
    if title == "Recording":
        return True
    return False


async def refresh_titles(client: PlaudClient, dry_run: bool = False) -> None:
    """Find files with placeholder titles and update them from Plaud's current data.

    Detects files where the title is a raw timestamp (e.g. '2026-02-24 195227')
    or 'Recording', fetches the current title from Plaud, and renames if updated.
    """
    stale = []
    for path in sorted(OBSIDIAN_DIR.glob("*.md")):
        if is_placeholder_title(path.name):
            fm = read_frontmatter(path)
            pid = fm.get("plaud_id")
            if pid:
                stale.append((path, pid))

    if not stale:
        print("No placeholder titles found. All titles are up to date.")
        return

    print(f"Found {len(stale)} files with placeholder titles, fetching current names from Plaud...")

    # Build plaud_id -> filename map from API
    raw_files = await client.get_files()
    id_to_name = {f.get("id"): f.get("filename", "") for f in raw_files}

    updated = 0
    skipped = 0
    for path, pid in stale:
        plaud_name = id_to_name.get(pid)
        if not plaud_name:
            print(f"  SKIP (not found in Plaud): {path.name}")
            skipped += 1
            continue

        # Build new filename from current Plaud title
        plaud_file = normalize_file(next(f for f in raw_files if f.get("id") == pid))
        new_filename = make_filename(plaud_file)

        if new_filename == path.name or is_placeholder_title(new_filename):
            print(f"  SKIP (title still pending): {path.name}")
            skipped += 1
            continue

        new_path = OBSIDIAN_DIR / new_filename
        if new_path.exists():
            print(f"  SKIP (target exists): {path.name} -> {new_filename}")
            skipped += 1
            continue

        new_title = extract_title(plaud_name)
        print(f"  {'[DRY RUN] ' if dry_run else ''}RENAME: {path.name}")
        print(f"      -> {new_filename}")

        if not dry_run:
            # Update the heading inside the file
            text = path.read_text(encoding="utf-8")
            old_heading_match = re.search(r'^# .+$', text, re.MULTILINE)
            if old_heading_match:
                text = text[:old_heading_match.start()] + f"# {new_title}" + text[old_heading_match.end():]
                path.write_text(text, encoding="utf-8")
            path.rename(new_path)

        updated += 1

    print(f"\nTitle refresh: {updated} updated, {skipped} skipped")


def find_all_duplicates(dry_run: bool = False) -> None:
    """Find and remove all duplicate files: same plaud_id or same transcript content."""
    # Group files by plaud_id
    id_groups: dict[str, list[Path]] = {}
    no_id_files: list[Path] = []

    for path in sorted(OBSIDIAN_DIR.glob("*.md")):
        fm = read_frontmatter(path)
        pid = fm.get("plaud_id")
        if pid:
            id_groups.setdefault(pid, []).append(path)
        else:
            no_id_files.append(path)

    to_delete = []

    # Handle plaud_id duplicates: keep the one with the best (non-placeholder) title
    for pid, paths in id_groups.items():
        if len(paths) <= 1:
            continue
        # Prefer non-placeholder titles, then newest by mtime
        def sort_key(p):
            return (not is_placeholder_title(p.name), p.stat().st_mtime)
        paths.sort(key=sort_key, reverse=True)
        keeper = paths[0]
        for dup in paths[1:]:
            to_delete.append((dup, keeper, "same plaud_id"))

    # Handle no-id files: check if any match a file with plaud_id by transcript content
    for old_path in no_id_files:
        old_line = get_first_transcript_line(old_path)
        if not old_line:
            continue
        for pid_paths in id_groups.values():
            for new_path in pid_paths:
                new_line = get_first_transcript_line(new_path)
                if new_line and old_line[:60] == new_line[:60]:
                    to_delete.append((old_path, new_path, "same transcript"))
                    break
            else:
                continue
            break

    if not to_delete:
        print("No duplicates found.")
        return

    print(f"{'[DRY RUN] ' if dry_run else ''}Found {len(to_delete)} duplicates to remove:\n")
    for dup, keeper, reason in to_delete:
        print(f"  DEL: {dup.name}  ({reason})")
        print(f"    -> keeping: {keeper.name}")
        if not dry_run:
            dup.unlink()

    total = len(list(OBSIDIAN_DIR.glob("*.md")))
    print(f"\nDuplicates removed: {0 if dry_run else len(to_delete)}")
    print(f"Files remaining: {total}")


def find_old_format_duplicates(dry_run: bool = False) -> None:
    """Find old-format files (YYYY-MM-DD-MM-DD-slug) that have new-format
    equivalents, verified by transcript content match. Remove the old ones.

    Old format: 2026-02-03-02-02-strategic-alignment-on-app-development-and-d.md
    New format: 2026-02-03 - Strategic Alignment on App Development and Data Collection.md
    """
    old_files = sorted(
        p for p in OBSIDIAN_DIR.glob("*.md")
        if re.match(r'^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-', p.name)
    )
    new_files = [
        p for p in OBSIDIAN_DIR.glob("*.md")
        if re.match(r'^\d{4}-\d{2}-\d{2} - ', p.name)
    ]

    if not old_files:
        print("No old-format files found. Nothing to clean up.")
        return

    print(f"Found {len(old_files)} old-format files, checking against {len(new_files)} new-format files...\n")

    to_delete = []
    kept = []

    for old_path in old_files:
        old_kw = extract_keywords(old_path.stem)
        old_line = get_first_transcript_line(old_path)

        matched_new = None
        # Try keyword matching first
        for new_path in new_files:
            new_kw = extract_keywords(new_path.stem)
            if not old_kw or not new_kw:
                continue
            overlap = old_kw & new_kw
            min_set = min(len(old_kw), len(new_kw))
            if min_set > 0 and (len(overlap) >= 3 or len(overlap) / min_set >= 0.6):
                # Verify by transcript content
                new_line = get_first_transcript_line(new_path)
                if old_line and new_line and old_line[:40] == new_line[:40]:
                    matched_new = new_path
                    break

        # If keyword matching failed, try all same-date files by content only
        if not matched_new and old_line:
            m = re.match(r'\d{4}-(\d{2})-(\d{2})-(\d{2})-(\d{2})-', old_path.name)
            if m:
                rec_month, rec_day = m.group(3), m.group(4)
                date_prefix = f"2026-{rec_month}-{rec_day}"
                for new_path in new_files:
                    if new_path.name[:10] == date_prefix:
                        new_line = get_first_transcript_line(new_path)
                        if new_line and old_line[:40] == new_line[:40]:
                            matched_new = new_path
                            break

        if matched_new:
            to_delete.append((old_path, matched_new))
        else:
            kept.append(old_path)

    print(f"Duplicates found: {len(to_delete)}")
    print(f"Unique old files (kept): {len(kept)}")

    if to_delete:
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Removing {len(to_delete)} old-format duplicates:\n")
        for old_path, new_path in to_delete:
            print(f"  DEL: {old_path.name}")
            print(f"    -> {new_path.name}")
            if not dry_run:
                old_path.unlink()

    if kept:
        print(f"\nKept (no new-format counterpart):")
        for p in kept:
            print(f"  {p.name}")

    total = len(list(OBSIDIAN_DIR.glob("*.md")))
    print(f"\n{'='*60}")
    print(f"CLEANUP {'(DRY RUN) ' if dry_run else ''}COMPLETE")
    print(f"  Deleted: {0 if dry_run else len(to_delete)}")
    print(f"  Kept:    {len(kept)} old-format + {len(new_files)} new-format")
    print(f"  Total:   {total} files")
    print(f"{'='*60}")


async def main():
    dry_run = "--dry-run" in sys.argv
    cleanup = "--cleanup" in sys.argv
    do_refresh_titles = "--refresh-titles" in sys.argv
    days = 30
    limit = None

    for i, arg in enumerate(sys.argv):
        if arg == "--days" and i + 1 < len(sys.argv):
            days = int(sys.argv[i + 1])
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    # Cleanup mode: remove all duplicates (no Plaud API needed)
    if cleanup:
        find_all_duplicates(dry_run)
        find_old_format_duplicates(dry_run)
        return

    # Title refresh mode (requires Plaud API)
    if do_refresh_titles:
        client = PlaudClient()
        await refresh_titles(client, dry_run)
        return

    client = PlaudClient()

    # Fetch files from Plaud (paginate to get all, then filter by date)
    print(f"Fetching Plaud recordings from last {days} days...")
    cutoff_ms = int((time.time() - days * 86400) * 1000)

    # Plaud API ignores skip/limit and always returns all files in one call
    raw_files = await client.get_files()

    # Normalize and filter to files within the date range
    all_files = [normalize_file(f) for f in raw_files]
    files = [f for f in all_files if f.get("start_time", 0) >= cutoff_ms]
    files_with_transcript = [f for f in files if f.get("has_transcript", False)]
    print(f"Found {len(all_files)} total recordings, {len(files)} in last {days} days ({len(files_with_transcript)} with transcripts)")

    # Find already-synced files (plaud_id first, then keyword fallback)
    known_ids = get_existing_plaud_ids()
    existing_ids = find_existing_matches(files_with_transcript, known_ids)

    # Also check by output filename
    to_sync = []
    for f in files_with_transcript:
        if f["id"] in existing_ids:
            continue
        output_path = OBSIDIAN_DIR / make_filename(f)
        if output_path.exists():
            continue
        to_sync.append(f)

    if limit:
        to_sync = to_sync[:limit]

    print(f"Already synced: {len(existing_ids)} ({len(known_ids)} by plaud_id, {len(existing_ids) - len(known_ids)} by keyword)")
    print(f"To sync: {len(to_sync)}")

    if not to_sync:
        print("\nAll transcripts are up to date!")
        return

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Syncing {len(to_sync)} transcripts...\n")

    results = {"synced": 0, "skipped": 0, "error": 0, "dry_run": 0}
    errors = []

    for i, pf in enumerate(to_sync, 1):
        name = pf["filename"][:70]
        print(f"[{i}/{len(to_sync)}] {name}...", end=" ", flush=True)

        result = await sync_file(client, pf, dry_run)
        status = result["status"]
        results[status] = results.get(status, 0) + 1

        if status == "synced":
            size_kb = result["size"] / 1024
            print(f"OK ({size_kb:.1f}KB, {result['transcript_entries']} entries)")
        elif status == "error":
            print(f"ERROR: {result['error']}")
            errors.append(result)
        elif status == "skipped":
            print("SKIPPED")
        else:
            print(status.upper())

        if not dry_run and status == "synced":
            await asyncio.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"SYNC COMPLETE")
    print(f"  Synced:  {results.get('synced', 0)}")
    print(f"  Skipped: {results.get('skipped', 0)}")
    print(f"  Errors:  {results.get('error', 0)}")
    if dry_run:
        print(f"  Dry run: {results.get('dry_run', 0)}")
    print(f"  Location: {OBSIDIAN_DIR}")
    print(f"{'='*60}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e['id']}: {e['error']}")


if __name__ == "__main__":
    asyncio.run(main())
