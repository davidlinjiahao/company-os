---
name: explain
description: Use when the user types /explain or asks to explain a topic, concept, system, industry, or document — "explain X", "break this down", "make an explainer / primer / briefing", "help me understand Y", "ELI5 but smart". Produces a clear, plain-language explainer PDF that defines every acronym and term inline and dynamically generates the right visual for each idea (mermaid diagram for a system, process chart for a process, the actual periodic table for chemistry, a table for numbers), rendered in a monochrome editorial house style.
---

# /explain — turn any topic into a clear, visual explainer

Produce a **print-ready explainer PDF** that a smart non-expert finishes
*understanding* the topic. Two things make it work, and both are non-negotiable:

1. **Define every acronym and piece of jargon inline, at first use, in plain
   language — no glossary.** The reader never hits an undefined term and never has
   to jump elsewhere for a meaning.
2. **Dynamically generate the visual that the content *is*** — a process → a
   process chart; a system → a mermaid diagram; the periodic table → the actual
   periodic table; numbers → a table; a trend → a line chart. The picture carries
   the idea, not decorates it.

It renders in a **monochrome house style** (pure `#000`/`#FFF`, Satoshi +
Roboto Mono, zero radius, zero accent) so every explainer looks like one voice.

## Non-negotiables

1. **Read `reference/explaining.md` first** (how it teaches) and keep
   `reference/style.md` open (how it looks). Both rule sets bind the output.
2. **Inline definitions only.** Every acronym spelled out and every jargon word
   glossed the first time it appears. No end glossary, no front vocabulary list.
3. **Right visual, dynamically built — but earn it.** Don't make the reader
   imagine what you can show: use the content→visual table in `explaining.md`
   (system→diagram, numbers→table, elements→periodic table, existing thing→real
   screenshot). But apply the **cognitive-load gate** first — render a visual only
   when it reduces effort more than a clean sentence would; a diagram that just
   restates prose in boxes is decoration. Visual-first is a bias, not a mandate.
4. **Explain simply.** Short sentences, concrete first, lead with the plain point.
5. **Render with WeasyPrint; verify fill** with `check-report.py` before done.

## Inputs

`/explain <topic or source>` — a topic, a question, a file path, a vault note, a
URL's content, or a prior answer in this conversation. Default output is a
**report** explainer (US Letter). If the user wants slides, build a **deck**
(`template-deck.html` + `deck.css`); the pedagogy rules are identical. If the
topic or audience is genuinely ambiguous, ask one question; otherwise infer a
plain title + audience and proceed. If the topic is broad, research it first (the
content must be correct — explainers that are clear but wrong are worse than
useless).

## Workflow

Skill dir: `~/.claude/skills/explain`. Use the venv interpreter throughout:
`PY=~/.explain-venv/bin/python` (see Tooling notes). `PY` is just the path to the
project's Python venv — override it with any interpreter that has WeasyPrint +
PyMuPDF installed.

1. **Read `reference/explaining.md`.** Internalise the three rules, the
   content→visual selection table, and the document spine. Skim `style.md` for the
   visual contract and banned elements.

2. **Plan the explainer.** Decide the spine (short version → body sections →
   honest counterargument → sources). For each section, decide the **one visual
   that matches it** and what acronyms/terms appear (so you can define them inline).

3. **Set up a build dir** from the worked skeleton. The HTML source, CSS, and
   figures live under `~/Documents/Code/explainers/<slug>/` — one folder per
   explainer. (The finished **PDF** goes to the **Desktop** in step 6.)
   ```bash
   S=~/.claude/skills/explain/assets; D=~/Documents/Code/explainers/<slug>
   mkdir -p "$D"
   cp $S/theme.css $S/report.css $S/explainer.css "$D/"   # deck.css instead of report.css for slides
   cp $S/template-explainer.html "$D/index.html"
   ```
   The skeleton links `theme.css` → `report.css` → `explainer.css`, sets
   `class="report"` on `<body>`, and shows every component (stat-row, diagram
   figure, periodic table, table, callout, inline `.term`/`.gloss` definitions).

4. **Generate the visuals dynamically** (don't reuse the template's figures):
   - **Diagram / process / system / timeline / flow** → write a `.mmd` and render
     a monochrome, WeasyPrint-safe inline SVG:
     ```bash
     printf 'flowchart LR\n  A[Step one] --> B[Step two] --> C[Done]\n' > "$D/d1.mmd"
     $PY $S/mermaid.py "$D/d1.mmd" "$D/d1.svg"
     ```
     Paste the SVG inside `<figure class="diagram"> … <figcaption>…</figcaption>`.
     Mermaid types: `flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `timeline`,
     `gantt`. Keep to ≤ ~12 nodes; split if bigger.
   - **Chemistry / elements / materials** → render the real periodic table with
     the relevant cells highlighted:
     ```bash
     $PY $S/periodic-table.py "Li,Co,Ni,Nd,Dy" "Battery + magnet metals" >> "$D/index.html"
     # or a preset:  rare-earths | critical-minerals | battery-metals | platinum-group
     ```
   - **Numbers compared** → a house `<table>`. **Headline metrics** → `.stat-row`.
     **Trend / before-after** → inline-SVG line or bar chart (explicit hex; no pie).
   - **Map / real artifact** → embed a rasterized PNG at 1:1 pixels.

5. **Author the prose.** Plain language; define each acronym/term inline with
   `<span class="term">Word</span> <span class="gloss">(plain meaning)</span>` the
   first time it appears. Open each section with the point, support with its
   visual, close with a one-line "what this means". Budget content so pages fill.

6. **Render and verify** — the PDF goes to the **Desktop**; the editable source
   stays in the build dir:
   ```bash
   $PY $S/render.py "$D/index.html" ~/Desktop/"<Title>.pdf"
   $PY $S/check-report.py ~/Desktop/"<Title>.pdf"      # rebalance any SPARSE page
   ```
   Then rasterize a page or two and eyeball: every term defined? every structural
   idea a picture? monochrome, square, left-aligned? (For a **deck**, use
   `check-overflow.py` instead — see `style.md`.)

7. **Report** both paths and the page count: the **PDF on the Desktop**
   (`~/Desktop/<Title>.pdf`) and the editable **source** in
   `~/Documents/Code/explainers/<slug>/` for re-rendering.

## Tooling notes

- **Python:** WeasyPrint (render) + PyMuPDF/`fitz` (checks). System is externally
  managed (PEP 668); use a venv:
  ```bash
  python3 -m venv ~/.explain-venv && ~/.explain-venv/bin/pip install weasyprint pymupdf
  ```
  Run everything with `~/.explain-venv/bin/python` (bare `pip`/`python3` are
  refused / lack the packages). WeasyPrint's system deps (cairo/pango/harfbuzz)
  are already installed via Homebrew.
- **Mermaid (`mermaid.py`):** renders via the already-installed **Google Chrome**
  headless loading a vendored `mermaid.min.js` (cached in `~/.cache/explain/`) —
  no mermaid-cli, no chromium download, no external service. First run fetches
  `mermaid.min.js` from **jsdelivr** (the CDN reachable here; unpkg/kroki are
  proxy-blocked). It forces `htmlLabels:false` (labels become SVG `<text>`, not
  `<foreignObject>`, which WeasyPrint renders blank) and rewrites `currentColor` →
  `#000000`. Set `CHROME=/path` to override the browser.
- **Fonts** load via remote `@import` in `theme.css` (Fontshare Satoshi + Google
  Roboto Mono, both reachable); `render.py`'s `url_fetcher` keeps a dead URL from
  aborting the render.
- **Logos / images:** rasterise SVG → PNG at 1:1 pixels; never `<img src="…svg">`
  in WeasyPrint (masks/clips/`<use>` silently break). See `style.md` §09.
