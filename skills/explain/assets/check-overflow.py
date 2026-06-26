#!/usr/bin/env python3
"""Deck overflow check — run after EVERY deck render.

Verifies no text block crosses the 1920x1080 safe area:
  - bottom safe line at y = 1000 (80px bottom padding)
  - side safe lines at x = 120 and x = 1800 (120px left/right padding)

Usage:
    python3 check-overflow.py out.pdf
Exits non-zero if any slide violates, so it can gate a build.
"""
import sys
import fitz  # PyMuPDF


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 check-overflow.py out.pdf")
    doc = fitz.open(sys.argv[1])
    scale = 1920 / doc[0].rect.width
    # 1px epsilon: content may sit exactly ON the padding edge (the legitimate
    # max extent). Only flag blocks that genuinely CROSS the safe line.
    EPS = 1.0
    violations = 0
    for i, page in enumerate(doc):
        for x0, y0, x1, y1, text, *_ in page.get_text("blocks"):
            if not text.strip():
                continue
            if y1 * scale > 1000 + EPS:
                print(f"slide {i+1}: crosses bottom safe line ({y1*scale:.0f} > 1000)")
                violations += 1
            if x0 * scale < 120 - EPS or x1 * scale > 1800 + EPS:
                print(f"slide {i+1}: side safe line violation "
                      f"({x0*scale:.0f}..{x1*scale:.0f} outside 120..1800)")
                violations += 1
    if violations:
        print(f"FAIL — {violations} safe-area violation(s)")
        sys.exit(1)
    print("OK — every slide inside the safe area")


if __name__ == "__main__":
    main()
