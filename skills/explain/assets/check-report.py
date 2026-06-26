#!/usr/bin/env python3
"""Explain report fill check — run after every report render.

Flags pages that end early (a stranded callout or a thin tail page is the most
common failure). Measures ACTUAL rendered ink per page by rasterizing — so a page
filled by a diagram, a periodic table, or an image counts as full, not just one
filled by text. The metric is trailing whitespace: how much of the page below the
last mark is blank. A body page whose content stops before ~70% down is sparse;
the final page is held to a far looser bar (a short tail is fine, near-blank is
not).

Usage:
    python3 check-report.py report.pdf [max_trailing]
max_trailing defaults to 0.30 for body pages (content must reach ~70% down).
Exits non-zero if any page is too sparse, so it can gate a build.
"""
import sys
import fitz  # PyMuPDF

INK = 245          # grayscale value below which a pixel counts as a mark
DPI = 100


def last_inked_row(page):
    pm = page.get_pixmap(colorspace=fitz.csGRAY, matrix=fitz.Matrix(DPI / 72, DPI / 72))
    w, h, s = pm.width, pm.height, pm.samples
    for y in range(h - 1, -1, -1):
        row = s[y * w:(y + 1) * w]
        if min(row) < INK:
            return y, h
    return 0, h


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 check-report.py report.pdf [max_trailing]")
    pdf = sys.argv[1]
    max_trailing = float(sys.argv[2]) if len(sys.argv) > 2 else 0.30
    doc = fitz.open(pdf)
    n = doc.page_count
    bad = 0
    for i, page in enumerate(doc):
        last, h = last_inked_row(page)
        trailing = (h - 1 - last) / h          # fraction of page blank below last mark
        filled = 1 - trailing
        is_last = i == n - 1
        limit = 0.85 if is_last else max_trailing  # last page: only flag if near-blank
        flag = trailing > limit
        tag = "last" if is_last else "body"
        print(f"page {i+1}/{n} [{tag}]: content reaches ~{filled*100:3.0f}% down  "
              f"{'SPARSE — fill it or merge into a neighbour' if flag else 'ok'}")
        bad += flag
    if bad:
        print(f"FAIL — {bad} sparse page(s). Add content, merge sections, pull a "
              f"figure up, or rebalance so every page is full or almost full.")
        sys.exit(1)
    print("OK — every page full or almost full")


if __name__ == "__main__":
    main()
