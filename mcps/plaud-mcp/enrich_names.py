#!/usr/bin/env python3
"""Enrich Plaud transcript names with Google Calendar attendee info.

Matches Plaud recordings to calendar events by time overlap and appends
the calendar event title (which the user sets to the person name).

Usage:
    uv run --with google-api-python-client --with google-auth-oauthlib \
        python enrich_names.py --days 3
    uv run --with google-api-python-client --with google-auth-oauthlib \
        python enrich_names.py --days 3 --apply
"""

import argparse
import asyncio
import pickle
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from plaud_mcp.plaud_client import PlaudClient

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CONFIG_DIR = Path.home() / ".config" / "google-calendar"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.pickle"

ENRICHED_PREFIX = "["


def get_calendar_credentials() -> Credentials:
    """Get or refresh Google Calendar credentials."""
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return creds


def fetch_calendar_events(days: int) -> list[dict]:
    """Fetch events from all calendars for the given date range."""
    creds = get_calendar_credentials()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=days)).isoformat()
    time_max = now.isoformat()

    all_events = []
    calendars = service.calendarList().list().execute().get("items", [])

    for cal in calendars:
        cal_id = cal["id"]
        try:
            result = service.events().list(
                calendarId=cal_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            for event in result.get("items", []):
                start = event.get("start", {})
                end = event.get("end", {})
                # Skip all-day events (no dateTime)
                if "dateTime" not in start or "dateTime" not in end:
                    continue
                all_events.append(event)
        except Exception as e:
            print(f"  Warning: failed to fetch from calendar {cal.get('summary', cal_id)}: {e}")

    return all_events


def parse_iso_to_epoch_ms(iso_str: str) -> int:
    """Parse ISO 8601 datetime to epoch milliseconds."""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def compute_overlap_ms(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    """Compute overlap in ms between two time ranges."""
    overlap_start = max(a_start, b_start)
    overlap_end = min(a_end, b_end)
    return max(0, overlap_end - overlap_start)


def match_transcripts_to_events(
    transcripts: list[dict], events: list[dict]
) -> list[tuple[dict, dict, float]]:
    """Match each transcript to its best calendar event by time overlap.

    Returns list of (transcript, event, overlap_ratio) tuples.
    Only includes matches with >0 overlap.
    """
    # Pre-parse event times
    parsed_events = []
    for event in events:
        start = event.get("start", {})
        end = event.get("end", {})
        try:
            e_start = parse_iso_to_epoch_ms(start["dateTime"])
            e_end = parse_iso_to_epoch_ms(end["dateTime"])
            parsed_events.append((event, e_start, e_end))
        except (KeyError, ValueError):
            continue

    matches = []
    for t in transcripts:
        t_start = t.get("start_time", 0)
        t_duration = t.get("duration", 0)
        t_end = t_start + t_duration

        if t_duration <= 0:
            continue

        best_event = None
        best_ratio = 0.0

        for event, e_start, e_end in parsed_events:
            overlap = compute_overlap_ms(t_start, t_end, e_start, e_end)
            ratio = overlap / t_duration
            if ratio > best_ratio:
                best_ratio = ratio
                best_event = event

        if best_event and best_ratio > 0:
            matches.append((t, best_event, best_ratio))

    return matches


def format_duration(ms: int) -> str:
    """Format milliseconds to human-readable duration."""
    seconds = ms // 1000
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes}m"
    return f"{minutes}m{secs}s"


def format_epoch_ms(ms: int) -> str:
    """Format epoch ms to local datetime string."""
    dt = datetime.fromtimestamp(ms / 1000)
    return dt.strftime("%m/%d %H:%M")


async def main():
    parser = argparse.ArgumentParser(description="Enrich Plaud transcript names with calendar info")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")
    parser.add_argument("--apply", action="store_true", help="Actually rename files (default: dry-run)")
    args = parser.parse_args()

    # Fetch Plaud transcripts
    print(f"Fetching Plaud transcripts from last {args.days} days...")
    plaud = PlaudClient()
    transcripts = await plaud.get_recent_files(days=args.days)
    print(f"  Found {len(transcripts)} transcripts")

    # Fetch calendar events
    print(f"Fetching Google Calendar events from last {args.days} days...")
    events = fetch_calendar_events(days=args.days)
    print(f"  Found {len(events)} calendar events")

    # Match
    matches = match_transcripts_to_events(transcripts, events)
    print(f"\nMatched {len(matches)} transcripts to calendar events:\n")

    renames = []
    for transcript, event, ratio in matches:
        old_name = transcript.get("filename", "")
        event_title = event.get("summary", "")

        # Skip if already enriched
        if old_name.startswith(ENRICHED_PREFIX):
            print(f"  SKIP (already enriched): {old_name}")
            continue

        # Skip if no useful event title
        if not event_title.strip():
            continue

        new_name = f"[{event_title}] {old_name}"

        t_start = transcript.get("start_time", 0)
        t_dur = transcript.get("duration", 0)
        print(f"  {format_epoch_ms(t_start)} ({format_duration(t_dur)}) | overlap: {ratio:.0%}")
        print(f"    OLD: {old_name}")
        print(f"    NEW: {new_name}")
        print()

        renames.append((transcript["id"], new_name))

    if not renames:
        print("No renames needed.")
        return

    if not args.apply:
        print(f"Dry run complete. {len(renames)} file(s) would be renamed.")
        print("Run with --apply to rename.")
        return

    # Apply renames
    print(f"Applying {len(renames)} rename(s)...")
    for file_id, new_name in renames:
        try:
            result = await plaud.rename_file(file_id, new_name)
            status = result.get("status", -1)
            if status == 0:
                print(f"  OK: {new_name}")
            else:
                print(f"  WARN: status={status} for {file_id}: {result}")
        except Exception as e:
            print(f"  ERROR renaming {file_id}: {e}")

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
