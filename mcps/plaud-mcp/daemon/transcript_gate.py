#!/usr/bin/env python3
"""Transcript Gate: classify new Plaud transcripts and queue team-relevant ones for approval.

Runs as Step 3 of the plaud-sync daemon (after sync + enrich). For each new
transcript in the personal Obsidian vault, uses Claude to classify
SHARE vs PERSONAL with a short reason. Shared transcripts are staged
for explicit approval before copying to the team vault.

Safety: NEVER auto-copies to the team vault. All writes require explicit approval.
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Force line-buffered stdout for launchd
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# --- Paths ---
GATE_DIR = Path.home() / ".claude" / "transcript_gate"
STATE_FILE = GATE_DIR / "state.json"
PENDING_FILE = GATE_DIR / "pending.json"
STAGING_DIR = GATE_DIR / "staging"
ENV_FILE = GATE_DIR / "env"

_vault_root = Path(os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    str(Path.home() / "Documents" / "ObsidianVault")
))
PERSONAL_VAULT = _vault_root / "Transcripts" / "Plaud"

# --- Classification prompt ---
RULES_FILE = Path(__file__).parent / "CLASSIFICATION_RULES.md"


def _load_rules() -> str:
    if RULES_FILE.exists():
        return RULES_FILE.read_text()
    return "No classification rules file found. Use your best judgment."


CLASSIFY_PROMPT = """You are filtering transcripts for a team.
Classify whether this transcript should be shared with the team vault.

{rules}

Calendar event hint: {calendar_event}

Respond in EXACTLY this format:
CLASSIFICATION: SHARE or PERSONAL
REASON: max 10 word reason

Transcript title: {title}
Transcript excerpt (first 2000 chars):
{excerpt}"""


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_paths": [], "classified": {}}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_pending() -> dict:
    if PENDING_FILE.exists():
        return json.loads(PENDING_FILE.read_text())
    return {
        "pending": [],
        "rejected_paths": [],
        "approved_history": [],
        "next_id": 1,
        "last_notified": None,
    }


def save_pending(pending: dict) -> None:
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    PENDING_FILE.write_text(json.dumps(pending, indent=2))


def get_api_key() -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return None


def extract_excerpt(content: str, max_chars: int = 2000) -> str:
    match = re.search(r"## Transcript\s*\n(.+)", content, re.DOTALL)
    text = match.group(1) if match else content
    return text[:max_chars]


def read_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in content[3:end].strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def extract_title_from_filename(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"^\d{4}-\d{2}-\d{2}\s*-\s*", "", name)
    return name or "Unknown Recording"


def extract_date_from_filename(filename: str) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    return match.group(1) if match else "unknown"


def parse_calendar_event(plaud_filename: str) -> str | None:
    """Extract calendar event from enriched Plaud filename like '[Team - Standup] 02-18 Title'."""
    match = re.match(r"\[(.+?)\]", plaud_filename)
    return match.group(1) if match else None


def classify_transcript(api_key: str, title: str, excerpt: str, calendar_event: str | None = None) -> tuple[str, str]:
    """Call Claude Opus to classify a transcript. Returns (classification, reason)."""
    cal_hint = calendar_event if calendar_event else "none"
    rules = _load_rules()
    prompt = CLASSIFY_PROMPT.format(title=title, excerpt=excerpt, calendar_event=cal_hint, rules=rules)

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-opus-4-6",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    text = result["content"][0]["text"].strip()

    # Parse structured response
    classification = "PERSONAL"
    reason = ""
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("CLASSIFICATION:"):
            val = line.split(":", 1)[1].strip().upper()
            if "SHARE" in val:
                classification = "SHARE"
            else:
                classification = "PERSONAL"
        elif line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()

    return classification, reason


async def build_plaud_id_map() -> dict[str, str]:
    """Build a map of plaud_id -> enriched Plaud filename from the Plaud API."""
    try:
        from plaud_mcp.plaud_client import PlaudClient

        client = PlaudClient()
        files = await client.get_files()
        return {f["id"]: f.get("filename", "") for f in files}
    except Exception as e:
        print(f"  WARNING: Could not fetch Plaud filenames: {e}")
        return {}


def send_notification(pending_items: list[dict]) -> bool:
    """Send notification via webhook (if configured)."""
    webhook = os.environ.get("NOTIFICATION_WEBHOOK")
    if not webhook or not pending_items:
        return False

    try:
        summary = [f"#{item['id']} {item['title']}" for item in pending_items[-5:]]
        resp = httpx.post(
            webhook,
            json={
                "text": f"Transcripts pending approval ({len(pending_items)} total):\n" + "\n".join(summary),
            },
            timeout=30,
        )
        resp.raise_for_status()
        print(f"  Notification sent ({len(pending_items)} items)")
        return True
    except Exception as e:
        print(f"  WARNING: notification failed: {e}")
        return False


async def main() -> None:
    print("=== Transcript Gate ===")

    api_key = get_api_key()
    if not api_key:
        print("ERROR: No ANTHROPIC_API_KEY found. Set it in env or ~/.claude/transcript_gate/env")
        sys.exit(1)

    if not PERSONAL_VAULT.exists():
        print(f"ERROR: Personal vault not found at {PERSONAL_VAULT}")
        sys.exit(1)

    # Build plaud_id -> enriched filename map (has calendar event prefixes)
    print("Fetching Plaud filenames for calendar event mapping...")
    plaud_map = await build_plaud_id_map()
    print(f"  Mapped {len(plaud_map)} Plaud files")

    state = load_state()
    pending = load_pending()

    seen_paths = set(state.get("seen_paths", []))
    rejected_paths = set(pending.get("rejected_paths", []))

    all_files = sorted(PERSONAL_VAULT.glob("*.md"))
    print(f"Found {len(all_files)} transcripts in personal vault, {len(seen_paths)} already classified")

    new_files = []
    for f in all_files:
        rel_path = f"Transcripts/Plaud/{f.name}"
        if rel_path in seen_paths or rel_path in rejected_paths:
            continue
        new_files.append(f)

    if not new_files:
        print("No new transcripts to classify.")
        return

    print(f"Classifying {len(new_files)} new transcript(s)...")

    new_pending = []

    for f in new_files:
        rel_path = f"Transcripts/Plaud/{f.name}"
        title = extract_title_from_filename(f.name)
        date = extract_date_from_filename(f.name)

        content = f.read_text(encoding="utf-8", errors="replace")
        excerpt = extract_excerpt(content)

        # Look up calendar event from enriched Plaud filename
        fm = read_frontmatter(content)
        plaud_id = fm.get("plaud_id", "")
        plaud_filename = plaud_map.get(plaud_id, "")
        calendar_event = parse_calendar_event(plaud_filename)

        try:
            classification, reason = classify_transcript(api_key, title, excerpt, calendar_event)
        except Exception as e:
            print(f"  ERROR classifying {f.name}: {e}")
            continue

        cal_tag = f" [{calendar_event}]" if calendar_event else ""
        print(f"  {f.name}{cal_tag} → {classification} ({reason})")

        seen_paths.add(rel_path)
        state.setdefault("classified", {})[rel_path] = classification

        if classification == "SHARE":
            item_id = pending["next_id"]
            pending["next_id"] = item_id + 1

            item = {
                "id": item_id,
                "source": "plaud",
                "title": title,
                "date": date,
                "source_path": rel_path,
                "calendar_event": calendar_event,
                "reason": reason,
                "enqueued_at": datetime.now(timezone.utc).isoformat(),
            }
            pending["pending"].append(item)
            new_pending.append(item)

            STAGING_DIR.mkdir(parents=True, exist_ok=True)
            staging_path = STAGING_DIR / f"{item_id}.md"
            staging_path.write_text(content, encoding="utf-8")

    state["seen_paths"] = sorted(seen_paths)
    save_state(state)
    save_pending(pending)

    print(f"\nResults: {len(new_pending)} queued for approval, {len(new_files) - len(new_pending)} personal (skipped)")

    if new_pending:
        notified = send_notification(new_pending)
        if notified:
            pending["last_notified"] = datetime.now(timezone.utc).isoformat()
            save_pending(pending)


if __name__ == "__main__":
    asyncio.run(main())
