#!/usr/bin/env python3
"""House renderer — WeasyPrint, not ReportLab.

Usage:
    python3 render.py input.html output.pdf

Charts must be inline SVG with explicit hex (never currentColor, never
file:// images). The url_fetcher below keeps a single dead image/font URL from
aborting the whole render — it returns an empty payload instead of raising.
"""
import sys
from weasyprint import HTML, default_url_fetcher


def fetcher(url, t=15):
    try:
        return default_url_fetcher(url, timeout=t)
    except Exception:
        return {"string": b"", "mime_type": "image/jpeg"}


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: python3 render.py input.html output.pdf")
    src, out = sys.argv[1], sys.argv[2]
    # base_url lets relative links (styles, local logo PNGs) resolve.
    HTML(filename=src, url_fetcher=fetcher).write_pdf(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
