# The explainer playbook

How `/explain` thinks. The house visual system (`style.md`) is *how it looks*;
this is *how it teaches*. The goal: a smart reader who is **not** a domain expert
finishes the document understanding the topic, with no undefined term left behind
and the key structure shown as a picture, not buried in prose.

## Three rules (non-negotiable)

1. **Define every acronym and piece of jargon — inline, at the moment it is first
   used, in plain language. No glossary, no end-of-document definitions.**
   - First use of an acronym spells it out, in place: "the IEA (International
     Energy Agency — the rich countries' energy advisory body)". Never let an
     undefined acronym stand.
   - First use of a domain word glosses it inline: "metallurgists
     (metal-processing engineers)", "smelting (using heat to extract a crude
     metal)".
   - Anything a 12th-grader wouldn't know is jargon. When in doubt, define it.
   - Put the definition exactly where the reader meets the word — a parenthetical,
     an em-dash clause, or the next short sentence. Do **not** collect terms into a
     glossary or a separate vocabulary section; the reader should never have to
     jump to find a meaning.

2. **Explain simply.** Short sentences. Concrete over abstract. Analogy before
   formalism. Lead with the plain-English point, then add precision. Active voice.
   No throat-clearing, no "it is important to note". If a sentence needs a second
   read, split it.

3. **Show it, don't just say it — match the visual to the content.** Every major
   structural or quantitative idea gets the *right* picture (next section). Prose
   describing a structure that could be a diagram is a failure.

## Visual selection — content type → visual

**Don't make the reader imagine what you can show them.** If an idea has a shape —
a flow, a structure, a comparison, a real object — show that shape. This is the
heart of `/explain`.

**Dynamically generate the graphic that matches the content.** Don't reach for a
generic chart — look at what the thing *is* and render that. A process becomes a
process chart; a system becomes a mermaid diagram; the periodic table becomes the
periodic table; a set of numbers becomes a table; a trend becomes a line chart.
The artifact should *be* the idea, not a decoration of it.

**The cognitive-load gate — apply before every visual.** Ask: *will this picture
reduce the reader's effort more than one clean sentence would?* Only render it if
yes. A visual must do work prose can't — show simultaneity, structure, scale, or a
real thing. A diagram that just restates a sentence in boxes adds load, not
clarity; a three-row "table" that's really a list, a flowchart of two steps, a
chart of two numbers — these are decoration. When prose is genuinely clearer
(a definition, a judgment, a short causal chain), use prose. Visual-first is a
bias, not a mandate.

| If the content is… | Render… | How |
|---|---|---|
| A process / procedure / workflow with steps | **Process chart** (mermaid `flowchart`, numbered/sequential) | `mermaid.py` → inline SVG; see below |
| A system, pipeline, dependency graph, or org | **Mermaid diagram** (`flowchart`/`graph`) | `mermaid.py` → inline SVG; see below |
| A sequence of steps / message passing | **Mermaid** `sequenceDiagram` | same |
| A timeline / roadmap / phases over time | **Mermaid** `timeline` or `gantt`, or a dated table | same |
| States and transitions | **Mermaid** `stateDiagram-v2` | same |
| A hierarchy / tree / taxonomy | **Mermaid** `flowchart TD` | same |
| Several numbers compared | **Table** (house: top/bottom frame, row hairlines) | hand-author HTML |
| A few headline metrics | **Stat-row** (3–4 cards, one hairline) | house `.stat-row` |
| A trend over time / before-after | **Chart** — inline SVG line or bar | house `.chart` SVG, explicit hex |
| Part-to-whole / shares | **Stacked bar or labeled % row** (never a pie — banned) | house SVG |
| The chemical elements involved | **The actual periodic table**, relevant cells highlighted | `periodic-table.py` |
| Geography / location | **A real map** (embed a rasterized map image) | PNG at 1:1 px |
| An existing product, UI, screen, device, place, or artwork | **The real thing** — a screenshot or photo, not an invented diagram | rasterise to grayscale PNG, 1:1 px |
| A comparison across 2 axes | **2×2 / quadrant** or a matrix table | hand-author |

For something that *already exists*, show it — a real screenshot, photo, or
diagram of the actual thing beats a clean abstraction you made up. (Convert to
grayscale and embed at 1:1 px so it sits in the monochrome system; cite the
source.) We do **not** generate AI illustrations or decorative imagery — every
mark is authored or real, per the banned-elements rule in `style.md`.

Default bias: **when prose is describing how parts connect, stop and draw a
mermaid diagram.** When prose is listing numbers, stop and build a table or
stat-row. The reference mining report is excellent but *under-visualised* — it
explains the supply chain and China's chokepoint in paragraphs where a single
highlighted flowchart would land faster. `/explain` fixes that.

## Document structure (report explainer)

Adapt to the topic, but this spine works for most explainers — it mirrors the
reference:

1. **Cover** — eyebrow (topic · date · audience), a plain-English title that
   states the payoff, a 2–3 line dek, a sources/colophon line.
2. **The short version** — the entire explainer in ~2 paragraphs + a stat-row of
   the 3–4 numbers that matter. A reader who stops here still "gets it".
3. **Body sections** — numbered, each a single clear idea. Open with the plain
   point; support with the matching visual (diagram/table/chart); define every
   term inline as it appears; end with a one-line "what this means". Earn one
   emphasis moment (callout) per spread.
4. **The honest counterargument** — where the simple story breaks, what you're
   unsure of. Explainers that only confirm are propaganda.
5. **Sources** — a table of what this was built from.

No glossary and no separate vocabulary section — every term is defined inline,
once, the first time it appears (rule 1).

## Mermaid → WeasyPrint (monochrome, JS-free)

WeasyPrint cannot run JavaScript, so mermaid is **pre-rendered to SVG** by
`assets/mermaid.py`, which calls mermaid-cli through the already-installed Google
Chrome (no chromium download). It injects a monochrome init directive and handles
the two WeasyPrint gotchas:

- **`htmlLabels:false`** — mermaid's default label uses `<foreignObject>`, which
  WeasyPrint renders blank. Force SVG `<text>` labels.
- **No `currentColor`** — house style §09: WeasyPrint won't resolve it. The injected
  theme sets explicit `#000000`/`#FFFFFF` and `Roboto Mono` so diagrams match the
  house style (black strokes, white fills, square nodes, no accent).

Usage: write a `.mmd` file, run `mermaid.py diagram.mmd diagram.svg`, then inline
the SVG inside a `<figure class="diagram">` with a `<figcaption>` (see
`explainer.css` and `template-explainer.html`). Keep diagrams to ≤ ~12 nodes; if
bigger, split into two. Caption every figure, and define any term that appears
inside it in the caption or nearby.

## Honesty & sourcing

- Mark estimates as estimates ("~", "roughly", "≈"). Don't fabricate precision.
- Attribute non-obvious facts (who says so). A sources table at the end.
- Distinguish "this is settled" from "this is my read".
- Keep the reader's specific situation in view when relevant ("why this matters to
  *you*") — but never at the cost of accuracy.

## Common mistakes

| Mistake | Fix |
|---|---|
| Acronym used before it's expanded | Expand on first use, every time |
| A paragraph describing a system | Replace/augment with a mermaid diagram |
| Numbers strung through prose | Pull into a table or stat-row |
| A pie chart | Stacked bar or labeled % row (pie is banned) |
| "Periodic table of X" as a metaphor with no table | Render the real grid (`periodic-table.py`) |
| Term defined in an end glossary | Define inline at first use; there is no glossary |
| Generic chart that doesn't fit the idea | Render the artifact the content *is* (process→flowchart, etc.) |
| Decorative visual that just restates a sentence | Apply the cognitive-load gate — cut it or use prose |
| Inventing a diagram of a thing that already exists | Show the real screenshot/photo instead |
| Diagram with colored mermaid defaults | Always render through `mermaid.py` (monochrome) |
| Confident tone on uncertain facts | Hedge honestly; add the counterargument section |

---

*Visual-first principle, the cognitive-load gate, and "show the real thing" adapted
from [uncoooloj/visual-explainer-skill](https://github.com/uncoooloj/visual-explainer-skill).*
