---
name: source
description: Turns a hiring need into an A-grade candidate list. Use when the user wants to source, recruit, or hire for a role, "find candidates", "build a candidate list", "who should we hire for X", or asks for a WHO/scorecard. Chains a WHO-method scorecard, competitor calibration via /search, a looped multi-source candidate sweep with strict A-bar filtering, and a ranked Desktop markdown + clickable PDF. Run with "/source [role or context]".
user-invocable: true
disable-model-invocation: false
argument-hint: "[role or context]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, WebFetch, WebSearch, mcp__notion__search_pages, mcp__notion__get_page, mcp__notion__get_block_children, mcp__notion__get_block, mcp__notion__create_page, mcp__notion__append_markdown, mcp__notion__append_blocks, mcp__notion__update_block, mcp__notion__delete_block, mcp__exa__web_search_exa, mcp__exa__people_search_exa, mcp__exa__crawling_exa, mcp__exa__company_research_exa, Skill, ScheduleWakeup, Monitor, TaskStop, TaskList, PushNotification
---

# Sourcing Skill

**Hiring need → A-grade candidate list.** WHO-method scorecard → competitor calibration via `/search` → looped multi-source sweep with strict A-bar filtering → ranked Desktop markdown + verified clickable PDF.

**Prime directive: quality over volume.** An honest short list of true A-players beats a padded one. List a candidate only when EVERY A-bar leg is met on first glance. Borderline → HOLD. Adjacent-but-not → excluded with reason.

## Quick Reference

```
/source "Senior Backend Engineer"                    # role name
/source "we keep shipping data-loss regressions"     # pain point → derive role
/source <path-to-JD.md or Notion JD>                 # existing JD → scorecard
/source                                              # vague need → ask for the role/JD
```

Six phases, run in order: **UNDERSTAND → SCORECARD → CALIBRATE → SOURCE → LOOP → OUTPUT.**

See `reference.md` for the full source matrix, agent-prompt templates, and the PDF recipe. See `assets/scorecard_prompt.md` for the WHO scorecard template. Render with `scripts/make_pdf.sh`.

---

## Phase 0 — INPUT

Accept one of: (a) a role name, (b) a context source (a pasted JD, or a written/verbal description of the need), (c) nothing. The neutral default is **"paste the role/JD or describe the need."** If the need is vague, ask for it, or **derive the role from whatever evidence is provided in Phase 1** before proceeding. Do not invent a role from a job title alone — anchor it to the failures it must fix.

> **Optional context sources:** if the environment has meeting-transcript or calendar tooling configured (e.g. a transcript MCP or a calendar MCP), you may use it to surface the pain in the user's own words. This is an enrichment, never a requirement — if absent, work from the user's brief alone.

## Phase 1 — UNDERSTAND (pull the real pain)

Find the true mission: what is breaking, who owns the fix, what "shipped" looks like.

The primary input is whatever the user gives you — a JD, a written brief, or a verbal description of the pain. Read any provided JD / doc (`Read`, or `mcp__notion__get_page` + `get_block_children`).

- Optionally search prior context if available: a prior-context vault, prior candidate lists on `~/Desktop`, or prior scorecards in Notion.
- **Output of this phase:** a 1-paragraph statement of the role's true mission, framed as the failures it must fix (e.g. "repeated data-loss regressions in the storage layer → need an owner who has shipped a correctness-critical distributed system on a real product").

## Phase 2 — SCORECARD (WHO / Geoff Smart, *Who: The A Method*)

Build the scorecard, then create it as a Notion page. Structure:

1. **Mission** — one paragraph. The role's reason to exist.
2. **Outcomes** — 3–8, ranked, each **measurable + time-bound**, set at the "an A-player has shipped this exact thing" bar. Score 1–5.
3. **Competencies** — **A. role-specific technical** + **B. cultural / values**. Score 1–5.

If a **sibling role page exists in Notion** (search first), mirror its exact structure and headings.

### Define the A-BAR here (this is the Phase-4 filter)

State a small set of **must-have legs** — the non-negotiable signals. Borderline candidates fail. Example (generic — replace for the real role):

> **A-bar:** (1) has personally shipped a production system of the relevant class on a real product **AND** (2) ≥1 of a small, role-specific skill set named in the scorecard.

Write the legs explicitly. Every sourced candidate must be mapped against each leg with evidence.

### ⚠️ CRITICAL NOTION TABLE GOTCHA (cost a rework — do not skip)

`mcp__notion__create_page` and `append_markdown` **FLATTEN GFM markdown tables** into raw `| ... |` text paragraphs, and leave literal `**bold**` / `*italic*` markers as text. To get real tables:

1. Create the page / sections with `create_page` or `append_markdown` (headings + prose only — no tables, no `**`/`*` markup in cells).
2. For each table, call `mcp__notion__append_blocks` with a native table block, inserted **after the section heading** via `after_block_id`:
   ```json
   {"type":"table","has_column_header":true,
    "rows":[["Outcome","Measure","Score"],["Ship X","by Q3, p95<5ms","5"]]}
   ```
3. **Delete the flattened `| ... |` text paragraphs** with `mcp__notion__delete_block`.
4. Fix any surviving literal `**bold**` / `*italic*` with `mcp__notion__update_block`, setting `paragraph.rich_text` with annotations `{bold:true}` / `{italic:true}`.
5. **`append_blocks` responses echo following-sibling IDs (misleading counts).** Always re-fetch `mcp__notion__get_block_children` to verify true state before deleting anything.

## Phase 3 — CALIBRATE (competitor /search)

Invoke the **`search` skill** (Skill tool) on the competitor set. Purpose:

- (a) **Validate role design** — one combined role vs split (e.g. two adjacent skill areas as one hire or two?).
- (b) **Extract the recurring stack / keyword taxonomy** — feeds the source queries.
- (c) **Capture comp + locations** — sets the bullseye geography and pay band.
- (d) **Seed the candidate pool** — named competitor employees in the target function.

Feed the taxonomy and role-design finding back into the scorecard (refine Outcomes/Competencies) and into the Phase-4 query set.

## Phase 4 — SOURCE (multi-source sweep)

Dispatch **PARALLEL subagents** (`Agent` tool), one per source lane. Each agent returns **ONLY A-grade candidates**, with evidence mapped to **each A-bar leg**, plus a **HOLD** bucket (named missing leg). See `reference.md` for per-agent prompt templates.

The lanes below are **pluggable** — run whichever are configured in the environment, skip the rest, and report honestly what ran. The always-available core is **Web/Exa + Competitor employees**; the others are optional add-ons.

| Lane | Tooling | Honest yield |
|---|---|---|
| Competitor employees | Enumerate named engineers in the target function at each competitor from the Phase-3 `/search` output. **Exclude founders/CxO** (not recruitable). | **Highest-value pool** — people already doing the exact job. |
| Web / Exa | `mcp__exa__web_search_exa`, `mcp__exa__people_search_exa` (**flaky/timeouts** → fall back to `web_search_exa` with category=people), `mcp__exa__crawling_exa`, `mcp__exa__company_research_exa`; plus `WebSearch`. | Solid for named people + company rosters. Always available. |
| GitHub | Optional. Needs a `GITHUB_TOKEN` env var. Pull **TOP CONTRIBUTORS of ~20–25 curated high-signal repos** in the domain (beats noisy free-text search), then read profiles for company/location. | High-signal for technical roles — if a token is set. |
| LinkedIn enrichment | Optional. If a LinkedIn enrichment provider is configured (via its own env vars), use it for headline/location/network-distance + warmth. Most such APIs do **NOT** return full work history → verify A-bar legs via Exa enrichment. | Good for warmth/identity; weak for confirming legs alone. |
| Job-board / community scrapers | Optional, pluggable. If a candidate-scraper lane is wired up (job boards, community forums, regional CV boards, hackathon rosters, etc.), run it and harvest genuine A-grade hits. | Often keys on generic software keywords → weak for niche roles. Report honestly; don't pad. |

### FILTER DISCIPLINE

- List only if **every A-bar leg is met on first glance.**
- Borderline → **HOLD**, name the missing leg.
- Adjacent-but-not (wrong specialty, pure adjacent discipline, tuning-only, founders) → **excluded with reason.**
- Rank survivors into **tiers**: **bullseye** (location + pedigree fit) first.

## Phase 5 — LOOP (until source depletion)

This is a self-paced **`/loop`**. Each round:

1. Dispatch the **remaining** source agents.
2. **Dedup** new finds against the running list (name + profile URL).
3. **Append** to the Desktop file (do not rewrite from scratch).
4. Update the **source-depletion tracker**: **Swept / Pending / Blind-spots-needing-user-action**.
5. **Self-pace.** If the user invoked `/loop /source …`, the `/loop` skill drives the cadence — just run one round per turn. If you pace it yourself, call `ScheduleWakeup` with `prompt = "/loop /source <original args>"` **verbatim** (the `/loop ` prefix re-enters the loop on the next firing), `delaySeconds` 1200–1800, and a one-line `reason`. Optionally arm a `Monitor` as the primary wake signal, keeping `ScheduleWakeup` as the fallback heartbeat.

**CONVERGENCE RULE — stop when:** two consecutive rounds add **no new Tier-1/2 candidate**, OR all named sources are resolved/dead-ended. Then **omit `ScheduleWakeup`** to end the loop, `TaskStop` any Monitor, write a closing summary, and `PushNotification` it.

**Track blind spots that need the user:** missing creds for an optional lane (e.g. a LinkedIn provider key, a scraper cookie), an absent `GITHUB_TOKEN`, CAPTCHA-walled boards, stale tokens needing rotation, warm-intro bridges. Surface these — they are user-only levers.

## Phase 6 — OUTPUT (markdown + verified clickable PDF)

Write `~/Desktop/<Role>_Candidates.md`:

- **Tiers** (Tier 1 bullseye → Tier 2 → HOLD → Excluded-with-reason).
- **Per-candidate:** evidence mapped to each A-bar leg, clickable profile link(s), warmth / network-distance.
- **Top-Picks shortlist** (the 3–5 to contact first).
- **Source-depletion tracker** (Swept / Pending / Blind-spots).

Then render a **clickable PDF** (the script lives next to this skill, in `scripts/`):

```bash
bash "$(dirname "$0")/scripts/make_pdf.sh" "$HOME/Desktop/<Role>_Candidates.md"
```

`make_pdf.sh` runs (weasyprint + pandoc, installed via homebrew):

```bash
pandoc "<md>" -f gfm -t html5 --standalone \
  --css scripts/style.css \
  --pdf-engine=weasyprint -o "<pdf>"
```

`style.css`: `@page A4 landscape`, ~8pt font, teal headers (`#0f766e`), word-wrap/break table cells, blue links (`#1d4ed8`), page-number footer.

**VERIFY links are real clickable annotations** (not just blue text) with pypdf — iterate pages, `page['/Annots']` → `/Subtype '/Link'` → `/A /URI`; count and print a sample. Report the clickable-URI count.

---

## Key Principles

- **Strict A-bar** — quality over volume; honest short list > padded one.
- **Dedup every round** by name + profile URL.
- **Be honest** about which sources yielded nothing — don't hide dead ends.
- **Surface user-only levers** (creds, CAPTCHA, token rotation, warm-intro bridges).
- **Always produce both** the markdown and a verified clickable PDF.
