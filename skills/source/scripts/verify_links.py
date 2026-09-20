#!/usr/bin/env python3
"""
Evidence-link verifier.

Every claim in a candidate list must be checkable by a human in one click.
This extracts every URL from a markdown file and resolves it, following
redirects. Exit 0 only if EVERY url ends at HTTP 200.

A 403 from a bot-walled host (LinkedIn is the usual one) is a FAIL, on purpose:
if a reviewer cannot open the link, it is not evidence. Cite something else.

    verify_links.py --input candidates.md
    verify_links.py --url https://example.com          # single-url check
    verify_links.py --input candidates.md --json report.json
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TIMEOUT = 15
RETRIES = 3
URL_RE = re.compile(r"https?://[^\s\)\]\}<>\"'`]+")
TRAILING = ".,;:!?"


def extract(text: str):
    seen, urls = set(), []
    for m in URL_RE.finditer(text):
        u = m.group(0).rstrip(TRAILING)
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return urls


def resolve(url: str):
    """(status, final_url, note). Tries HEAD, falls back to GET — many hosts
    405 or lie on HEAD."""
    last = (0, url, "")
    for attempt in range(RETRIES):
        for method in ("HEAD", "GET"):
            args = ["curl", "-sS", "-L", "-o", "/dev/null",
                    "--max-time", str(TIMEOUT),
                    "-w", "%{http_code} %{url_effective}"]
            if method == "HEAD":
                args.append("-I")
            args.append(url)
            try:
                r = subprocess.run(args, capture_output=True, text=True, timeout=TIMEOUT + 10)
            except subprocess.TimeoutExpired:
                last = (0, url, "timeout")
                continue
            parts = (r.stdout or "").strip().split(None, 1)
            if not parts or not parts[0].isdigit():
                last = (0, url, (r.stderr or "no response").strip()[:120])
                continue
            status = int(parts[0])
            final = parts[1] if len(parts) > 1 else url
            if status == 200:
                return status, final, ""
            last = (status, final, f"{method} {status}")
        if attempt < RETRIES - 1:
            subprocess.run(["sleep", str(2 ** attempt)], check=False)
    return last


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", help="markdown or text file to scan for URLs")
    src.add_argument("--url", action="append", help="check a single URL (repeatable)")
    ap.add_argument("--json", dest="json_out", help="write a machine-readable report here")
    ap.add_argument("--allow-status", type=int, action="append", default=[],
                    help="additionally accept this status (use sparingly, and say so in the output)")
    args = ap.parse_args()

    if args.input:
        path = Path(args.input).expanduser()
        if not path.exists():
            print(f"ERROR: no such file: {path}", file=sys.stderr)
            return 2
        urls = extract(path.read_text())
    else:
        urls = args.url

    if not urls:
        print("ERROR: no URLs found — a candidate list with no evidence links is a fail.", file=sys.stderr)
        return 2

    ok_statuses = {200, *args.allow_status}
    results, failures = [], []
    for u in urls:
        status, final, note = resolve(u)
        good = status in ok_statuses
        results.append({"url": u, "status": status, "final_url": final, "ok": good, "note": note})
        print(f"{'ok  ' if good else 'FAIL'} {status or '---'}  {u}")
        if not good:
            failures.append((u, status, note))

    total = len(results)
    passed = total - len(failures)
    print(f"\n{passed}/{total} resolved ({passed / total:.0%})")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(
            {"total": total, "passed": passed, "results": results}, indent=2))

    if failures:
        print("\nUnresolvable evidence — replace or drop these citations:", file=sys.stderr)
        for u, status, note in failures:
            print(f"  {status or '---'} {u} {note}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
