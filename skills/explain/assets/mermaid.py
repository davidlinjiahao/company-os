#!/usr/bin/env python3
"""Render a Mermaid diagram to a monochrome, WeasyPrint-safe inline SVG.

WeasyPrint can't run JavaScript, so mermaid is rendered ahead of time with the
already-installed Google Chrome (headless) loading a vendored mermaid.min.js — no
mermaid-cli, no chromium download, no external render service. The output is
house-style: pure black strokes, white fills, square corners, Roboto Mono
labels, and the two WeasyPrint gotchas handled:
  - htmlLabels:false  -> labels are SVG <text>, not <foreignObject> (which
    WeasyPrint renders blank).
  - currentColor      -> rewritten to explicit #000000 (WeasyPrint won't resolve
    currentColor).

Usage:
    python3 mermaid.py diagram.mmd diagram.svg
Then inline the SVG inside <figure class="diagram"> ... <figcaption>…</figcaption>.

Notes:
  - First run downloads mermaid.min.js to ~/.cache/explain/ (cached after).
  - Set CHROME env var to override the Chrome binary path.
  - The .mmd is the diagram body only (e.g. `flowchart LR\\n A-->B`); the
    monochrome theme is applied here, so don't add a colored %%{init}%% directive.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

CACHE = os.path.expanduser("~/.cache/explain")
MERMAID_JS = os.path.join(CACHE, "mermaid.min.js")
# jsdelivr is the CDN reachable from this environment (unpkg/kroki are blocked).
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"

CHROME_CANDIDATES = [
    os.environ.get("CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

# Monochrome house theme — black on white, square, Roboto Mono.
CONFIG = {
    "startOnLoad": False,
    "securityLevel": "loose",
    "htmlLabels": False,                 # top-level: the one that matters in v11
    "theme": "base",
    "themeVariables": {
        "primaryColor": "#FFFFFF",
        "primaryTextColor": "#000000",
        "primaryBorderColor": "#000000",
        "secondaryColor": "#FFFFFF",
        "tertiaryColor": "#FFFFFF",
        "lineColor": "#000000",
        "textColor": "#000000",
        "fontFamily": "Roboto Mono, monospace",
        "fontSize": "16px",
    },
    "flowchart": {"htmlLabels": False, "curve": "linear"},
    "sequence": {"useMaxWidth": True},
}


def find_chrome():
    for p in CHROME_CANDIDATES:
        if p and os.path.exists(p):
            return p
    sys.exit("error: Google Chrome not found. Set CHROME=/path/to/Chrome.")


def ensure_mermaid_js():
    if os.path.exists(MERMAID_JS) and os.path.getsize(MERMAID_JS) > 100000:
        return
    os.makedirs(CACHE, exist_ok=True)
    req = urllib.request.Request(MERMAID_URL, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=60).read()
    with open(MERMAID_JS, "wb") as f:
        f.write(data)


def render(defn):
    chrome = find_chrome()
    ensure_mermaid_js()
    harness = f"""<!doctype html><html><head><meta charset="utf-8">
<script src="file://{MERMAID_JS}"></script></head>
<body><div id="out"></div><script>
const def = {json.dumps(defn)};
mermaid.initialize({json.dumps(CONFIG)});
mermaid.render('g0', def)
  .then(({{svg}})=>{{document.getElementById('out').innerHTML=svg;document.title='DONE';}})
  .catch(e=>{{document.getElementById('out').textContent='ERR '+e;document.title='ERR';}});
</script></body></html>"""
    with tempfile.TemporaryDirectory() as d:
        hp = os.path.join(d, "harness.html")
        with open(hp, "w") as f:
            f.write(harness)
        out = subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=20000", "--dump-dom", f"file://{hp}"],
            capture_output=True, text=True, timeout=90,
        ).stdout
    m = re.search(r"(<svg.*?</svg>)", out, re.S)
    if not m:
        err = re.search(r"ERR[^<]*", out)
        sys.exit(f"error: mermaid render produced no SVG. {err.group(0) if err else out[:300]}")
    svg = m.group(1)
    # WeasyPrint safety: explicit hex instead of currentColor.
    svg = svg.replace("currentColor", "#000000")
    return svg


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: python3 mermaid.py diagram.mmd diagram.svg")
    defn = open(sys.argv[1]).read().strip()
    # Drop any author-supplied init directive so the monochrome theme wins.
    defn = re.sub(r"^\s*%%\{init[^}]*\}%%\s*", "", defn, flags=re.S)
    svg = render(defn)
    with open(sys.argv[2], "w") as f:
        f.write(svg)
    print(f"wrote {sys.argv[2]} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
