# House Style — house design system reference

The full rule set. Read this before authoring. The house style is a *default stance, not a
constraint*: it gives every artifact a baseline of craft so a stack of dozens of
documents reads as one voice. Act as a presentation / editorial designer — HTML is
the medium, the thinking is **magazine, not web dev**. Switch to a Neutral profile
for white-label, blind-pitch, or confidential output; otherwise this is the house.

**If a rule below is broken anywhere on a finished artifact, the artifact is wrong.**

## The bottom line (four numbers)

| | Value |
|---|---|
| Surface values | **2** — `#000` and `#FFF`, no off-white |
| Type families | **2** — Satoshi + Roboto Mono |
| Border radius | **0** everywhere, no exceptions |
| Accent colours | **0** — monochrome, opacity is the only scale |

Everything else is an elaboration of those four numbers.

## 01 · Foundations — three commitments

1. **Pure extremes.** `#000` on `#FFF` or `#FFF` on `#000`. No off-white
   (`#F7F6F2`), no soft `#111`, no low-opacity washes, no ambient-gradient
   backdrops. Two values, no atmospheric fog.
2. **Opacity is the gray scale.** Secondary text is ink at reduced alpha —
   `rgba(0,0,0,0.55)` dim, `rgba(0,0,0,0.35)` faint (inverted on dark). **Never**
   introduce a `#6B6B6B` or any mid-gray hex — it breaks the opacity rule.
3. **Satoshi 500/400 + Roboto Mono.** Display and body in Satoshi. Eyebrows,
   labels, captions, table headers and metadata in Roboto Mono, tracked
   uppercase. No mixing. No serif substitute.

The only neutrals allowed are ink dialled down by alpha:

| Token | Light value | Use |
|---|---|---|
| ink | `#000000` | primary text |
| dim | `rgba(0,0,0,.55)` | captions, eyebrows |
| faint | `rgba(0,0,0,.35)` | dates, colophon |
| line | `rgba(0,0,0,.12)` | dividers, rows |
| fill | `rgba(0,0,0,.04)` | quiet panels |

## 02 · Typography — two families, tracked precisely

Satoshi carries everything read as **prose**; Roboto Mono carries everything read
as a **label**. The line between them is never crossed.

| Role | Family | Weight | Source |
|---|---|---|---|
| Display — titles, headings | Satoshi | 500 | fontshare · satoshi@500 |
| Body text | Satoshi | 400 | fontshare · satoshi@400 |
| Mono — eyebrows, labels, metadata | Roboto Mono | 400–500 | google · roboto+mono |

**Deck type scale (1920×1080):** eyebrow 13px · title 144px · subtitle 40px ·
body 26px · caption 16px · stat-big 168px · stat-label 20px · card-heading 36px.

**Report type scale (US Letter / A4):** doc-title 32pt · h2 18pt · h3 13pt ·
body 11.5pt · caption 10pt · eyebrow 10pt · metric-val 32pt · metric-lbl 10pt.

**Key typography rules**
- **Negative tracking on display type.** `letter-spacing: -0.03em` on titles
  ≥ 64px. Positive tracking on display is an AI-template tell.
- **Eyebrow exactly 13px (deck) / 10pt (report), 0.16em.** Not 12, not 14, not
  0.12. The precise number matters.
- **Tabular lining figures.** `"tnum" 1, "lnum" 1, "ss01" 1` on body — numerals
  align by column.
- **Line height.** Display ~1.0, body ~1.45, dek ~1.25.
- **Leading / measure.** ~65–80 characters per line; report body ~1.4× body
  size, display ~1.15×.

## 03 · Colour — monochrome, opacity stands in for every neutral

Light is default; dark flips the same token names. See `assets/theme.css` for
both token blocks verbatim. The **brand gradient is reserved and never applied** —
stored for favicon/colophon only; no CSS rule references it on a finished
artifact. There is no colored accent anywhere on a finished artifact.

## 04 · Signature moves — committed, non-default decisions

These make output recognisable as the house style before a word is read:

1. **Left-aligned, everywhere.** Titles, deks, body, captions, eyebrows, cover
   subtitle. Centered text is the #1 AI-template tell. (Stat numerals inside a
   card may center for weight; labels stay left.)
2. **Eyebrow exactly 13px / 0.16em.** The precise number matters.
3. **Negative tracking on display type** (`-0.03em` on titles ≥ 64px).
4. **Tabular lining figures** (`"tnum" 1, "lnum" 1`).
5. **Border-radius 0 everywhere** — cards, callouts, chart areas, pills, tables.
   Rounded corners are the loudest AI-template fingerprint.
6. **No shadows, no SVG icons, no icon fonts, no emoji-as-chrome.** Depth via
   fill + whitespace. Emoji as content and typographic symbols (·, –, →) are fine
   when earned.
7. **Orphan whitespace is intentional.** Every slide has one deliberately empty
   quadrant.
8. **Statement slides at 144px+.** Single sentence, line-height 1.0, left-aligned,
   no quote marks, no attribution.
9. **Monochrome.** No colored accent anywhere.

Notice how few of these are additive. **The house style is defined mostly by subtraction** —
the radius removed, the accent removed, the centering removed, the shadow removed.
What remains has to carry the page on type and spacing alone.

## 05 · Spacing & rhythm — never hug the heading

Each gap above a paragraph is ≥ 1.5× the following paragraph's line-height, scaled
with heading size. **Air is structural, not leftover.** Token values for deck and
report rhythm live in `deck.css` / `report.css`.

**Canvas sizes**
- **Deck.** 1920 × 1080 exactly. Fixed `width`/`height`, never `min-height` —
  violations clip rather than silently grow the canvas.
- **Report.** US Letter default, `margin: 0.75in`; A4 only when the brief or
  source is A4, `margin: 20mm`. Single column unless content earns two.

## 06 · Components — tables, stat rows, charts

**Tables.** 1px top + bottom border on the table; 1px hairline between rows; no
vertical borders; no zebra striping. Header row is tracked-mono uppercase at
eyebrow size, dim. Right-align numerics, left-align text.

| Rule | Setting |
|---|---|
| Table frame | top + bottom border, ink, 1px |
| Row separator | `border-bottom` on `:not(:last-child)`, 1px |
| Vertical borders | none |
| Zebra striping | none |
| Header | tracked mono, uppercase, dim |

**Stat rows.** Three to four cards in a horizontal row, separated by a single 1px
vertical hairline — **the one vertical line the house style permits.** Numeral in Satoshi
500 at 168px (deck) / 32pt (report), `-0.02em`; label in mono uppercase; optional
one-line context in dim. Max 3–4 cards per row for text-heavy content.

**Charts** (inline SVG, explicit hex):
- **Line.** 2px ink stroke, no markers, no fill. Gridlines at `--c-line` or
  dropped. Second series → `--c-dim`.
- **Bar.** Solid ink fills, squared, ~40% width, hair gaps. Values on or above
  each bar in tracked mono. No legend.
- **Pie charts. BANNED.** Use a stacked bar or a labeled percentage row instead.

## 07 · Composition — hard rules & parallelism

**Hard rules**
- **No sidebar lines, ever.** No `border-left`, no accent rails, no vertical
  strokes alongside content. (Stat-card separators are the single exception.)
- **Dividers don't double.** Use `border-bottom` on `:not(:last-child)`, never
  top + bottom.
- **Hairlines are `border`,** never stacked boxes.
- **No runts.** A 1–3 character word on the last line is forbidden.
  `text-wrap: pretty` on body, `balance` on headings; backstop by joining the
  last two words with `&nbsp;`.
- **Flexbox: always `min-width: 0`** on items. Max 3–4 cards per row for
  text-heavy content.
- **Grid for finite sets,** never `flex-wrap`.
- **No adjacent eyebrows.** Two tracked-mono elements can't stack within ~3×
  eyebrow line-height.
- **Cover subtitle ≠ footer band.** Never stack subtitle and bottom-chrome in the
  bottom 10%.

**Parallelism**
- Section headers identical across slides.
- Repeated elements — eyebrow, footer, mark — share x, y.
- Consecutive stat-card slides share grid, numeral size, label placement.

**Page breaks (reports)** — see `report.css`; reports are print-ready. Body pages
stay on white — no full-page gray wash, no tinted card fills, no soft `#F5F5F5`
panel under body copy. Colour is earned on covers, section breaks, callouts and
chart highlights only.

> **Callout fill is allowed — it is not the banned panel.** A `.callout` uses
> `--c-fill-subtle`/`--c-fill-alt`, which is **ink at 0.04–0.06 alpha**, i.e. the
> sanctioned opacity scale, on an *earned emphasis site* (callouts are explicitly
> listed above). The banned thing is an off-white *hex surface* (`#F7F6F2`,
> `#F5F5F5`) or a gray wash sitting under ordinary body copy. Use callout fill
> sparingly — one emphasis moment per spread — never as a default card background
> behind running prose. Keep a callout to a few lines so it never strands a
> near-empty page (the most common report failure).

**Order of operations — how a page comes together**
1. **Set the grid first.** Choose canvas (deck or report), lock the safe area,
   decide single vs two-column before any content lands.
2. **Place the eyebrow and heading.** Eyebrow at exact size, heading with negative
   tracking; never hug — open the title-to-block gap.
3. **Flow the body.** Prose at the 65–80 character measure, lists and tables to
   the same left edge as the heading.
4. **Earn the emphasis.** A callout, a stat row, or a single dark break — one
   accent moment per spread, not three.
5. **Subtract.** Remove the radius, the shadow, the second hue, the centered line.
   Leave one quadrant deliberately empty.

> **The discipline.** Composition in the house style is mostly editing, not adding. If a
> page feels busy, the fix is almost never a new element — it is removing one and
> widening the whitespace around what remains.

## 08 · Banned elements — what never ships

| Element | Why | Alternative |
|---|---|---|
| "Thank You" closing slide | Template tell | Restate the thesis or mirror the cover |
| Agenda / TOC at display scale | Too heavy | Plain numbered list at body size |
| `Page X of Y` | Too formal | Bare numeral in tracked mono |
| Oversized step-card numerals | Template tell | Smaller, less dominant |
| Strikethrough-as-argument | Gimmick | — |
| Brightness-as-encoding charts | Unreadable | Position-encoded charts |
| Pie charts | Hard to read | Stacked bar or labeled % row |
| Centered text | #1 AI-template tell | Left-align everything |
| `border-radius > 0` | Loudest AI fingerprint | Square corners everywhere |
| Shadows | Flat depth model | Fill + whitespace |
| SVG icons / icon fonts | Chrome noise | Text labels or earned emoji |
| Off-white backgrounds | Breaks pure extremes | `#FFFFFF` or `#000000` only |
| Mid-gray hex (`#6B6B6B`) | Breaks opacity rule | `rgba()` with ink colour |
| "It's not X, it's Y" titles | Manufactured tension | Title introduces; speaker delivers |

> **The pattern.** Nearly every banned element is an AI-template tell — a default
> that signals machine-made. The house style's job is to strip those defaults so the
> artifact reads as authored.

## 09 · Rendering & logos — print-ready, WeasyPrint-first

Render with **WeasyPrint, not ReportLab** (`assets/render.py`). Charts are inline
SVG with explicit hex — never `currentColor`, never `file://` images.

**WeasyPrint gotchas**
- SVG `fill="currentColor"` does not resolve — always explicit hex.
- Charts: inline SVG only — no `<img>` with `file://` or base64.
- Units: `36pt` = points; `px = pt × 1.333`.
- `<a href>` emits clickable PDF links.

**Logos**
- Start with real SVGs — never author `<path>` data from scratch.
- **1:1 pixels** — source PNG dimensions equal CSS display size exactly; explicit
  `width`/`height`; `image-rendering: crisp-edges`.
- Preserve transparency; re-rasterise from SVG if needed.
- **Never** `<img src="…svg">` in WeasyPrint — masks, clips, `<use>` and external
  refs silently break. Rasterise to PNG first.
- No 2× retina PNGs scaled down — two display sizes mean two PNGs.

**Verification — check for overflow after every deck render** with
`assets/check-overflow.py` (PyMuPDF). It flags any text block crossing the
1920×1080 safe area (bottom y=1000; sides x=120 / x=1800).

## Closing note

The house style is a default stance, not a constraint. It exists so every artifact has a
baseline of craft and so consistency across dozens of documents is automatic.
Switch to the Neutral profile for white-label, blind-pitch, or confidential
outputs — otherwise, this is the house.
