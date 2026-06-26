# /source — Reference Playbook

The depth manual behind `SKILL.md`. Read this when you need the source lanes, agent prompt templates, the Notion native-table procedure, the loop mechanics, or the verified PDF recipe. The skill turns a hiring need into an A-grade candidate list by chaining: WHO scorecard → competitor calibration (`/search`) → looped multi-source sweep with strict A-bar filtering → ranked Desktop markdown + clickable PDF.

Core principle threaded through everything below: **strict A-bar — an honest short list beats a padded one.** Dedup every round, be honest about dead sources, surface user-only levers, and always ship both the markdown and a verified clickable PDF.

---

## 1. Source Matrix

The lanes are **pluggable**. The core two — **Competitor employees** and **Web / Exa** — need only the Exa MCP (or `WebSearch`) and are always available. The rest are optional add-ons that activate only when their credential/tooling is present; if it is absent, report it as a user-only lever and move on. **Never fabricate hits to fill a lane.**

| Source | How to run | Auth needed | Typical yield | Gotchas |
|---|---|---|---|---|
| **Competitor employees** | Enumerate named engineers in the target function at each competitor firm from the `/search` calibration output + Exa `company_research_exa` / `web_search_exa` ("<competitor> <function> engineer linkedin"). Cross-check identity/warmth on LinkedIn if an enrichment provider is configured. | Exa (MCP); optional LinkedIn provider | **Highest-value pool.** Directly stack-matched people already doing the exact job. | EXCLUDE founders/CxO (not recruitable). Names harvested from the web need a second pass (LinkedIn/Exa) to confirm current employer + the A-bar legs. |
| **Web / Exa** | MCP: `mcp__exa__web_search_exa`, `mcp__exa__people_search_exa`, `mcp__exa__crawling_exa`, `mcp__exa__company_research_exa`; plus `WebSearch`. | Exa (MCP); nothing for WebSearch | Broad reach; surfaces blogs, conference talks, papers, personal sites. | **`people_search_exa` is FLAKY / times out → fall back to `web_search_exa` with `category="people"`.** Crawl personal sites to confirm legs. WebSearch is the free backstop. |
| **GitHub contributors** | Optional. Read `GITHUB_TOKEN` from the environment. Pull TOP CONTRIBUTORS of ~20–25 curated high-signal repos (`gh api repos/<owner>/<repo>/contributors`), then `gh api users/<login>` for company/location/blog. | `GITHUB_TOKEN` env var | Strong for technical roles — code is the evidence. | If no token is set, report it as a user-only lever and skip — do not stall. Curated-repo contributor lists >> noisy free-text `search`. Profiles often hide company/location → infer from repos + commit email domains. |
| **LinkedIn enrichment** | Optional. If a LinkedIn enrichment provider is configured (via its own env vars), use it to resolve headline/location/network-distance and warmth (mutual connections, 1st/2nd-degree). | Provider-specific key(s) | Good for headline/location/network-distance + warmth. Moderate for niche. | **Most such APIs return headline/location/network-distance but NOT full work history** → you CANNOT confirm A-bar legs from the provider alone; verify via Exa enrichment. The user's own graph may have ~zero overlap with niche talent → warm intros need a bridge hire. |
| **Job-board / community scrapers** | Optional, pluggable. If a candidate-scraper lane is wired into the environment (job boards, HN/Reddit/X, regional CV boards, hackathon rosters, etc.), run it and harvest genuine A-grade hits. Treat it as one more `Agent` lane. | Lane-specific (cookies/tokens/login) | **Often WEAK for niche roles — keys on generic SOFTWARE keywords.** Run it if present, but expect real yield from the core lanes. | Community RSS endpoints commonly 403/429; social bearer tokens may be stale; some regional boards are CAPTCHA-walled. Report honestly when a lane returns nothing rather than padding. Surface missing creds as user-only levers. |

---

## 2. Agent Prompt Templates (parallel sourcing subagents)

Dispatch these with the **Agent** tool, one per source lane, in parallel each loop round. Every template embeds: (a) the strict A-bar, (b) the running-list dedup instruction, (c) the "A-grade-only + evidence-per-leg + HOLD bucket" output contract.

**Shared header** — prepend to EVERY agent prompt, filling the brackets from the scorecard (Phase 2):

```
ROLE: <role title>. MISSION: <one-line mission>. LOCATION BULLSEYE: <e.g. SF / remote-OK / city>.

A-BAR (MUST-HAVE LEGS — ALL required to list someone):
  LEG 1: <e.g. has shipped a production system of the relevant class on a real product>
  LEG 2: <e.g. >=1 of a small, role-specific skill set named in the scorecard>
  [add legs as defined in the scorecard]

FILTER DISCIPLINE:
  - List a candidate ONLY if EVERY leg is met on first glance, with a concrete evidence pointer per leg.
  - Borderline / a leg unconfirmed → put in HOLD with the exact missing leg named.
  - Adjacent-but-not (wrong specialty, pure adjacent discipline, tuning-only, FOUNDERS/CxO) → EXCLUDE with a one-line reason.

DEDUP: Here is the running candidate list (names + profile URLs): <PASTE RUNNING LIST>.
  Do NOT return anyone already on it. Only return NET-NEW people.

OUTPUT CONTRACT (return exactly this, nothing else):
  ## A-GRADE
  - **Name** — current role @ company | location | <profile URL> | warmth/network-distance if known
    - LEG 1: <evidence + link>
    - LEG 2: <evidence + link>
  ## HOLD
  - **Name** — <profile URL> — MISSING: <which leg(s)>
  ## EXCLUDED (counts + notable near-misses with reason)
  ## SOURCE STATUS: <Swept fully | Partially swept, more available | Dead-ended (reason) | Blocked (user action needed: ...)>
```

### 2a. Competitor-employees agent
```
[SHARED HEADER]
SOURCE: Named engineers at these competitors: <competitor list from /search calibration>.
HOW: For each firm, use mcp__exa__company_research_exa and mcp__exa__web_search_exa
("<firm> <function> engineer site:linkedin.com/in", conference talks, GitHub orgs) to
enumerate INDIVIDUAL engineers (NOT founders/CxO). Confirm current employer and each
A-bar leg via a second pass (LinkedIn enrichment if available + Exa crawl of any personal site/talk).
This is the highest-value pool — be exhaustive per firm before moving on.
```

### 2b. LinkedIn-enrichment agent (optional)
```
[SHARED HEADER]
SOURCE: LinkedIn via the configured enrichment provider (only if its env vars are set).
HOW: Resolve the account/handle, then search people by the taxonomy keywords from /search,
filtered to 1st/2nd-degree where the provider supports it. For each hit, pull headline/location/
network-distance and any mutual-connection (warmth) signal.
CRITICAL: most providers do NOT return full work history → you CANNOT confirm A-bar legs from
the provider alone. For every promising hit, verify the legs via mcp__exa__web_search_exa /
crawling_exa before listing. Capture network-distance as warmth for the output.
If no provider is configured, report it in SOURCE STATUS as a user-only lever and skip.
If the user's graph shows ~zero overlap, say so in SOURCE STATUS (signals a bridge-hire need).
```

### 2c. GitHub-contributors agent (optional)
```
[SHARED HEADER]
SOURCE: Top contributors of these ~20-25 curated high-signal repos: <repo list>.
HOW: Read GITHUB_TOKEN from the environment. If no token is set, report it in SOURCE STATUS
  as a user-only lever and skip — do not stall. For each repo:
  gh api repos/<owner>/<repo>/contributors --paginate
Take top contributors, then gh api users/<login> for name/company/location/blog/email.
Code in these repos IS the evidence — map specific repos/commits to each A-bar leg.
Infer company/location from repos + commit email domains when the profile hides them.
Prefer curated-repo contributor lists over noisy free-text search.
```

### 2d. Web / Exa agent
```
[SHARED HEADER]
SOURCE: Open web via Exa + WebSearch.
HOW: mcp__exa__web_search_exa for blogs/talks/papers/personal sites matching the taxonomy;
mcp__exa__crawling_exa to read candidate sites and confirm legs. Try people_search_exa but
if it times out FALL BACK to web_search_exa with category="people". Use WebSearch as a free
backstop. Every listed candidate needs a crawlable source confirming each leg.
```

### 2e. Scraper / community agent (optional)
```
[SHARED HEADER]
SOURCE: A candidate-scraper lane, only if one is wired into the environment
(job boards, HN/Reddit/X, regional CV boards, hackathon rosters, etc.).
HOW: Run whatever scraper entrypoints exist; collect results.
HONEST EXPECTATION: these often key on generic SOFTWARE keywords and yield ~zero signal for
niche roles. Community RSS may 403/429; social bearer tokens may be stale; some boards are
CAPTCHA-walled. Run it, harvest any genuine A-grade hit, and in SOURCE STATUS report exactly
what ran, what was blocked (name the exact missing credential), and the (likely low) yield.
If no scraper lane is configured, say so and skip. Do NOT pad the list to look productive.
```

---

## 3. WHO Scorecard Construction Guide (Geoff Smart, *Who: The A Method for Hiring*)

Build the scorecard from the Phase-1 pain/context (the provided JD/brief, optional transcripts). Derive the mission from the failures the role must fix.

**Structure:**
1. **Mission** — one paragraph. Why the role exists, in terms of the outcomes it produces (not a duties list).
2. **Outcomes** — 3–8, RANKED, each MEASURABLE and time-bound, at the "an A-player has shipped this exact thing" bar. Score column 1–5.
3. **Competencies** — two groups: **A. role-specific / technical** and **B. cultural / values**. Score column 1–5.
4. **A-BAR (must-have legs)** — define explicitly here; this is the Phase-4 filter. A small set of non-negotiable legs. *Example (generic):* (1) has personally shipped a production system of the relevant class on a real product AND (2) ≥1 of a small, role-specific skill set named in the scorecard.

**Mirror a sibling role page** — if a sibling role page exists in Notion, replicate its EXACT block structure (headings, table shapes, ordering) so the family stays consistent.

### Notion native-table procedure (this cost a rework — follow exactly)

`create_page` and `append_markdown` **flatten GFM tables into raw `| ... |` text paragraphs**, and literal `**bold**` / `*italic*` markers survive as text. To get real Notion tables and formatting:

1. **Prose first.** `mcp__notion__create_page` with the Mission paragraph and the section headings (Outcomes, Competencies, etc.) — prose and headings only, NO markdown tables.
2. **Locate the heading.** `mcp__notion__get_block_children` on the page to get the block id of the heading a table should follow.
3. **Insert the native table.** `mcp__notion__append_blocks` with, for each table, a block:
   ```json
   {"type":"table","has_column_header":true,
    "rows":[["Outcome","Metric","Deadline","Score 1-5"],
            ["...","...","...","..."]]}
   ```
   passing `after_block_id` = the heading's id so it lands in the right spot.
4. **Fix surviving markup.** Where any `**bold**`/`*italic*` text leaked into paragraphs, `mcp__notion__update_block` setting `paragraph.rich_text` with `annotations {bold:true}` / `{italic:true}` instead of literal markers.
5. **Delete the flattened text.** `mcp__notion__delete_block` on the raw `| ... |` text paragraphs left behind by any markdown table that was created via create_page/append_markdown.
6. **Re-fetch to verify — always.** `append_blocks` responses **echo following-sibling IDs (misleading counts)**. Do NOT trust the response; re-run `mcp__notion__get_block_children` to confirm the true block state BEFORE deleting anything, and again after, to confirm the final page.

Net rule: **create_page for prose/headings → append_blocks for each table after its heading → update_block to fix bold/italic → delete_block the flattened text → re-fetch get_block_children to verify.**

---

## 4. /loop Mechanics

The Phase-4/5 sweep is a self-paced `/loop`. Each round:

1. **Dispatch** the remaining/unresolved source agents (Section 2) in parallel via the Agent tool, each passed the current running list for dedup.
2. **Dedup** every returned candidate against the running list (match on name + profile URL; normalize handles).
3. **Append** net-new A-grade candidates to `~/Desktop/<Role>_Candidates.md`, slotting into tiers (bullseye location/pedigree first). Merge HOLD entries.
4. **Update the source-depletion tracker** (below).
5. **Pace.** If the user launched this as `/loop /source …`, the `/loop` skill drives cadence — run one round per turn and stop. If self-pacing, call `ScheduleWakeup` with `prompt = "/loop /source <original args>"` **verbatim** (the `/loop ` prefix re-enters the loop next firing), `delaySeconds` 1200–1800, and a one-line `reason`. Optionally arm a `Monitor` (`persistent:true`) as the primary wake signal with `ScheduleWakeup` as the fallback heartbeat. The next round resumes with the updated running list.

### Source-depletion tracker format
Maintain at the bottom of the Desktop file:
```
## Source Depletion Tracker  (round N)
| Source            | Status   | Notes / next action |
|-------------------|----------|---------------------|
| Competitor empl.  | Swept    | all N firms enumerated |
| Web/Exa           | Pending  | people_search timing out, web fallback running |
| GitHub            | Swept    | 23 repos contributor-pulled |
| LinkedIn enrich.  | Pending  | 2 keyword variants left |
| Scraper/community | Dead-end | generic-keyword bias, 0 niche hits |

### Blind spots needing user action
- LinkedIn provider key missing → enables warmth/network-distance lane
- GITHUB_TOKEN absent → set it in the environment to enable the contributor lane
- Regional CV board CAPTCHA-walled
- Social bearer token may be stale → rotate
- Warm-intro bridge: user graph ~0 overlap with niche talent
```
Status vocabulary: **Swept** (fully exhausted) · **Pending** (more available) · **Dead-end** (ran, no signal) · **Blocked** (user-only lever).

### Convergence rule
Stop when **two consecutive rounds add no new Tier-1/2 candidate**, OR all named sources are Swept/Dead-end/Blocked. Then **omit the ScheduleWakeup** to end the loop, `TaskStop` any Monitor you armed, write a closing summary, and `PushNotification` it.

### "User-only levers" concept
Anything you cannot resolve autonomously — missing creds for an optional lane (a LinkedIn provider key, a scraper cookie), an absent `GITHUB_TOKEN`, CAPTCHA-walled boards, stale token rotation, warm-intro bridges where the user's graph has no overlap. Track these explicitly so the loop converges honestly instead of spinning, and surface them in the final output as the user's highest-leverage next actions.

---

## 5. Output + PDF Recipe

### Output location
- Markdown: `~/Desktop/<Role>_Candidates.md` — tiers, per-candidate evidence mapped to each A-bar leg, clickable profile links, warmth/network-distance, a **Top-Picks shortlist** at the top, and the source-depletion tracker at the bottom.
- PDF: alongside it on `~/Desktop`.

### PDF generation (verified working — weasyprint + pandoc, via homebrew)
```bash
pandoc "<md>" -f gfm -t html5 --standalone \
  --css "<style.css>" --pdf-engine=weasyprint \
  -o "<pdf>"
```
`scripts/style.css` styling: `@page A4 landscape` (wide candidate tables), small font (~8pt), teal headers (`#0f766e`), table styling with `word-wrap: break-word` / `overflow-wrap`, blue links (`#1d4ed8`), and a page-number footer.

### Link-annotation verification (pypdf)
Blue text is NOT enough — confirm the links are real clickable PDF annotations:
```python
from pypdf import PdfReader
r = PdfReader("<pdf>")
uris = []
for page in r.pages:
    for a in page.get("/Annots", []) or []:
        o = a.get_object()
        if o.get("/Subtype") == "/Link":
            act = o.get("/A")
            if act and act.get("/URI"):
                uris.append(act["/URI"])
print(f"{len(uris)} clickable URIs")
print(uris[:5])
```
Expect a count in the dozens. If the count is ~0, the links rendered as styled text only — re-check that the markdown uses real `[text](url)` links and that pandoc emitted `<a href>` in the HTML.
