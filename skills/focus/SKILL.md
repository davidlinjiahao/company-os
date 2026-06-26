---
name: focus
description: Transform brain dump capture lists into structured, prioritized action plans. Auto-enriches from Plaud, Obsidian, and Calendar. Also supports reading triage and time audits as subcommands.
user-invocable: true
disable-model-invocation: false
argument-hint: "[capture list]" | read [urls] | timeaudit
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, AskUserQuestion, WebFetch, WebSearch, mcp__obsidian__*, mcp__notion__*, mcp__plaud__*, mcp__gcal__*
---

# Focus Skill

Transform brain dump capture lists into structured, prioritized action plans.
Auto-enriches vague items with real context from Plaud transcripts, Obsidian vault, and Calendar.

Based on: GTD (David Allen) + "The One Thing" (Gary Keller)

## Quick Reference

```
/focus                              # Interactive mode (auto-saves to Focus/GTD/)
/focus "paste your list here"       # Direct input (auto-saves to Focus/GTD/)
/focus --notion                     # Also sync to Notion
/focus read "url1, url2"            # Reading Triage Mode
/focus read today                   # Reading Triage from Obsidian
/focus tools "tool1, tool2"         # Research & save tools to Notion + Obsidian
/focus timeaudit                    # Time Audit Mode
/focus timeaudit "this week"        # Time Audit from Google Calendar
```

## Mode Routing

Parse `$ARGUMENTS` to determine mode:

| First Argument | Mode | Description |
|----------------|------|-------------|
| `read` | Reading Triage | Analyze reading list, output prioritized brief |
| `timeaudit` | Time Audit | Analyze schedule for energy balance |
| `tools` | Tool Cataloging | Research & save tools to Notion DB + Obsidian |
| _(anything else)_ | Standard Focus | Brain dump → action plan (default) |

## Execution Flow

```
Input (raw capture list)
  │
  ├─ Step 1: Extract entities (people, tools, projects)
  │
  ├─ Step 2: Context Gathering (query all data sources)
  │    ├─ Plaud: search_transcripts for each person/topic
  │    ├─ Obsidian: search ERM, CRM, Decisions, Transcripts
  │    └─ Calendar: query Google Calendar MCP for upcoming events
  │
  ├─ Step 3: Enrichment (apply 7 patterns using gathered context)
  │
  ├─ Step 4: Prioritization (The One Thing)
  │
  ├─ Output (enriched, organized focus plan)
  │
  └─ Step 5: Auto-save to Obsidian (always, for standard focus sessions)
```

---

## Step 1: Extract Entities

Scan every capture item and extract:

- **People**: Any proper noun or first name
- **Tools/Skills**: Anything prefixed with `/` or referencing a tool/service
- **Projects**: platform, hardware, recruiting, etc.
- **Vague items**: Single words or two-word items that need expansion

Build a lookup table:

```
| Entity | Type | Raw Item |
|--------|------|----------|
| Alice | person | "Alice planning" |
| Bob | person | "Bob and Carol questions" |
| Carol | person | "Bob and Carol questions" |
| /decide | tool | "Decide skill" |
| CRM | project | "CRM" |
```

---

## Step 2: Context Gathering

**CRITICAL: Do not guess context. Pull real data before enriching.**

Query all available data sources for each extracted entity. Run these sequentially — check each source's availability first.

### Degradation Strategy

Before querying each source, check availability. If a source is down or returns empty, log it and move on. Never fabricate context for a missing source.

```
Source availability:
  Plaud:    [available / unavailable — requires Plaud Desktop running]
  Obsidian: [available / unavailable]
  Calendar: [available / unavailable — requires gcal MCP configured]
```

If only 1 of 3 sources returns data, proceed with what you have. Partial context is better than no context. Note which sources were unavailable in the output.

### Source 1: Plaud Transcripts

Check connection first:
```
mcp__plaud__check_connection()
```
If unavailable, skip and note it.

For each person entity:
```
mcp__plaud__search_transcripts(query="[person name]", days=30)
```

For the most recent match, pull the summary:
```
mcp__plaud__get_summary(file_id="[id]")
```

**Extract**: Full name, role/title (from speaker labels), last discussion topics, open action items, decisions made.

### Source 2: Obsidian Vault

Search these locations for each entity using `mcp__obsidian__search_files` then `mcp__obsidian__read_text_file` for matches:

```
People context:
  Notion/Company/Team/ERM.md       → employee/candidate profiles
  Notion/Company/Sales/CRM.md      → customer/partner profiles
  Notion/Company/Fundraising/                → investor profiles

Recent transcripts (search by name):
  Transcripts/Plaud/                           → voice recordings
  Transcripts/Vidline/                         → video calls

Decision context:
  Decisions/                                   → past decisions relevant to items
```

Note: All paths are relative to the Obsidian vault root. Use `mcp__obsidian__list_allowed_directories()` to confirm the vault path if needed.

### Source 3: Google Calendar

Query the Google Calendar MCP for upcoming events:
```
mcp__gcal__get_today_schedule()
mcp__gcal__get_week_schedule()
```

For specific people, search events:
```
mcp__gcal__list_events(query="[person name]", time_min="[today]", time_max="[7 days from now]")
```

If the gcal MCP is unavailable, skip calendar context and note it.

**Extract**: Meetings scheduled with any person entity (date, time, location, attendees), meetings happening today/tomorrow (flag as time-sensitive).

### Context Assembly

After querying all sources, build a **Context Map**:

```
CONTEXT MAP
===========
Sources: Plaud (available, 30 matches), Obsidian (available),
         Calendar (unavailable — file not found)

Alice:
  Full name: Alice Torres
  Role: Engineering lead
  Last meeting: 2026-02-02 (Plaud: "Alice 1 on 1")
    Discussed: Q1 OKRs, vendor evaluation
    Action items: Prioritize vendors, prepare meeting questions
  Plaud mentions (last 30 days): 30 transcripts
  ERM status: A-level team member

Bob:
  Full name: Bob Nakamura
  Role: CEO of AcmeCorp
  Last meeting: Vidline transcript V0XXXXXXXXX
    Discussed: product integration, API design, deployment timeline
  Open questions: How many endpoints? Versioning strategy?
```

---

## Step 3: Enrichment (7 Patterns)

Apply all patterns using the Context Map. Do not guess — use the data gathered in Step 2.

### Pattern 1: Person + Context Injection

For each capture item containing a person name, replace with: **Full Name (Title at Company)** + when the next interaction is + what was last discussed.

**Rule**: Expand every person reference with full name, role/title, company/org, when the interaction happens, and what specifically to discuss.

```
BEFORE: "Bob and Carol questions"
AFTER:
  - Questions for Carol Wu (Head of evals at PartnerCo, meeting tomorrow)
    - What do you think of the new API design
  - Questions for Bob Nakamura (CEO of AcmeCorp)
    - How many concurrent users can the system handle?
    - How important is backwards compatibility?
```

### Pattern 2: Vague → Specific Sub-tasks

For items that are 1-3 words, use the Context Map to expand into concrete sub-tasks with specs.

**Rule**: Ask: What specifically needs to change? Who is this for? What's the ideal end state? What are the sub-components?

```
BEFORE: "Alice planning"
AFTER (using Context Map — last meeting discussed vendor evaluation):
  - Help Alice prioritize vendor evaluation
  - Help Alice come up with questions for the partner meeting
  - Help Alice learn the decision making framework

BEFORE: "Decide skill"
AFTER:  "/decide — Improve user form experience, 1-way/2-way selection,
         context retrieval, slack message UI, match system to decision
         making principles and add multiplayer functionality"

BEFORE: "Sync skill"
AFTER:  "/sync — make it so that anyone on the team can use it to sync
         all their plaud and tella.tv context into the company vault"
```

### Pattern 3: WHY Injection

Add "so that [outcome]" or "to [goal]" to every task using context from strategy docs, recent decisions, and meeting action items.

**Rule**: If you can't state the WHY, the item might not be actionable yet — park it or ask.

```
BEFORE: "Slack auto translate"
AFTER:  "Setup Slack auto translate so that partner messages are
         auto translated to english and posted in the team channel"

BEFORE: "Claude analytics"
AFTER:  "Figure out a way to track Claude analytics across multiple
         teammates to see which skill / mcp / agent is most used"
```

### Pattern 4: Expand + Deduplicate

Single-word or two-word items are NEVER actionable. Expand into verb + object + context. If multiple items refer to the same thing, merge them.

**Rule**: Expand vague items using Context Map data. Merge related items into one.

```
BEFORE: "Calendar sync" (vague)
AFTER:  "Migrate your-personal@email.com and your-work@email.com historical
         events to team@yourcompany.com calendar"

BEFORE: "CRM" (vague)
AFTER:  "Update Notion Sales CRM to be a single table"

BEFORE: "New hire ERM" (vague)
AFTER:  "Add [new hire name] to ERM"
```

### Pattern 5: Domain Grouping

Group items by operational context — WHO it affects and WHERE it happens.

**Rule**: The grouping should make it obvious which "mode" you need to be in to do the work. Adapt domains to the actual content.

```
Typical domains:
├── Research       # Questions for specific people, investigation
├── Hardware       # Manufacturing, hardware partners, suppliers
├── Software       # Product, architecture, platform
├── Tooling        # Claude Code skills, MCPs, agents, analytics
├── HR/Team        # 1-on-1s, hiring, onboarding
├── Content        # X, writing, media
└── MISC           # Admin, calendar, CRM, onboarding
```

### Pattern 6: Item Migration

Capture is the inbox. After enrichment, every item must leave Capture.

**Rule**: Actionable + urgent → Q1. Actionable + not urgent → Q2. Not actionable → Parked or deleted. Capture should be EMPTY after processing.

Using Calendar context: items with meetings today/tomorrow → flag as time-sensitive.

### Pattern 7: Surface Adjacencies

Check transcript action items and meeting summaries for work that wasn't in the capture list.

**Rule**: When enriching an item, ask "what else does this imply?" Adjacent tasks often hide behind vague captures.

```
NEW (emerged from "Alice planning"):
  - "Help Alice learn the decision making framework"
  - "Help Alice come up with questions for the partner meeting"

NEW (emerged from processing the GTD system):
  - "Add GTD system to Onboarding"
```

---

## Step 4: Prioritization (The One Thing)

Ask: "What's the ONE thing that makes everything else easier or unnecessary?"

**P1 Criteria** (Run now):
- High leverage — unblocks other work
- Time-sensitive — meeting today/tomorrow (from Calendar), hiring deadline
- Foundational — infrastructure that multiplies team output
- Requires focus / Claude Code session

**P2 Criteria** (Do while P1 runs):
- Can be done in parallel
- Requires waiting / human interaction
- Administrative tasks
- Less urgent

**Key principle**: Prefer items that multiply the TEAM (5x) over items that optimize YOU (1.2x).

**Note**: Use context from the Context Map to determine priority, not just keywords. A task containing "agent" could be P2 if it's exploratory, while a task with no keywords could be P1 if there's a meeting tomorrow.

---

## Step 5: Auto-save to Obsidian

**Always runs automatically** at the end of every standard focus session (not reading triage or time audit).

### Save Location

```
Focus/GTD/YYYY-MM-DD-focus.md
```

Where `YYYY-MM-DD` is the current date.

### Implementation

After rendering the full focus plan output to the user:

1. Save the complete rendered focus plan as an Obsidian note:
```
mcp__obsidian__create_note(
  path="Focus/GTD/YYYY-MM-DD-focus.md",
  content="[full rendered focus plan markdown]"
)
```

2. If a note already exists for today (create_note returns an error), update it instead:
```
mcp__obsidian__update_note(
  path="Focus/GTD/YYYY-MM-DD-focus.md",
  content="[full rendered focus plan markdown]"
)
```

3. Confirm save to the user: `Saved to Focus/GTD/YYYY-MM-DD-focus.md`

### Content

Save the **entire** focus plan output including all sections:
- The ONE Thing
- Context sources
- Capture (Enriched) with all domains
- Q1 and Q2
- Surfaced from Transcripts
- Parked
- Questions to Resolve

---

## Output Format

```markdown
# Focus Plan: [Date]

**The ONE Thing**: [Single most important task + why it's the ONE thing]

**Context sources**: Plaud ([status]), Obsidian ([status]), Calendar ([status])

---

## Capture (Enriched)

### [Domain 1: e.g., Research]
- [ ] **Enriched task** — so that [outcome]
  - Sub-task with spec (source: Plaud transcript [date])
  - Sub-task with spec (source: Plaud transcript [date])

### [Domain 2: e.g., China / Hardware]
- [ ] **Enriched task**
  - Context from last meeting: [summary]
  - Next meeting: [date from calendar]

---

## Q1 — Urgent + Important

### [Category]
- [ ] **Task with full context**
  1. Sub-task
  2. Sub-task

---

## Q2 — Important, Not Urgent

### [Category]
- [ ] Task
- [ ] Task

---

## Surfaced from Transcripts
Items found in recent meetings that weren't in the capture list:
- [ ] [Action item] (source: [meeting name, date])

## Parked (Not Now)
- Item with reason

## Questions to Resolve
- [ ] Question?
```

---

## Integration

### Auto-save to Obsidian (default for standard focus)

Standard focus sessions **always** auto-save to `Focus/GTD/YYYY-MM-DD-focus.md` via Step 5. No flag needed.

The `--save` flag is no longer required for standard focus sessions. It is kept as an alias for backwards compatibility but has no additional effect.

### Save to Notion (`--notion`)

When the user passes `--notion` or asks to sync to Notion:
1. Search for the team lead page: `mcp__notion__search_pages(query="Team Lead")`
2. Update the Capture section blocks with enriched content via `mcp__notion__append_blocks`

If the Notion MCP is unavailable, skip and note it.

---

## Reading Triage Mode (`/focus read`)

Optimizes daily reading by analyzing content and recommending what to read fully, skim, or skip.

### Input Sources

- `/focus read "url1, url2, url3"` — Analyze specific URLs
- `/focus read today` — Pull reading list from Obsidian `/Reading/today.md`
- `/focus read --calibrate` — Set reading preferences (stored at `/Reading/reading-preferences.md`)

### Context Loading

Before scoring, load:
1. **GTD Priorities**: `/GTD/GTD.md` — Q1/Q2 tasks (via `mcp__obsidian__read_text_file`)
2. **Active Projects**: Current focus areas from Obsidian/Notion
3. **Reading Preferences**: Calibrated style and topic priorities (if exists)

### Scoring Algorithm

| Factor | Weight | Description |
|--------|--------|-------------|
| **Relevance** | 40% | Match to active projects and GTD priorities |
| **Novelty** | 25% | New information vs. already known |
| **Actionability** | 20% | Can inform decisions this week |
| **Quality** | 10% | Source credibility, depth |
| **Timeliness** | 5% | Time-sensitive information |

### Decision Thresholds

```python
score = relevance*0.40 + novelty*0.25 + actionability*0.20 + quality*0.10 + timeliness*0.05

if score >= 0.7: category = "FULL READ"
elif score >= 0.4: category = "SKIM"
else: category = "SKIP"
```

### Execution Flow

1. **Fetch content** — Use WebFetch for each URL (in parallel via Task subagents)
2. **Score each item** — Apply scoring algorithm against loaded context
3. **Rank and categorize** — Sort by score, assign FULL READ / SKIM / SKIP
4. **Extract key sections** — For FULL READ items, identify which sections matter most
5. **Estimate time** — Based on word count and reading speed

### Output: Reading Brief

```markdown
# Reading Brief - [Date]

**Items analyzed**: N
**Time budget**: ~X minutes
**Context**: [Active projects/priorities informing triage]

---

## FULL READ (N items) - ~X min

### 1. [Title](url)
**Why**: [Relevance to active work]
**Key sections**: [Specific sections to focus on]
**Time**: ~X min

---

## SKIM (N items) - ~X min

### 1. [Title](url)
**Why**: [Background context]
**Read only**: [Introduction, Conclusion, etc.]
**Time**: ~X min

---

## SKIP (N items)

### 1. [Title](url)
**Reason**: [Why not worth reading now]
```

### Calibration

Run `/focus read --calibrate` to set:
- Reading speed (fast/medium/slow)
- Preferred depth (technical detail / high-level / actionable only)
- Topics of interest
- Topics to avoid

---

## Time Audit Mode (`/focus timeaudit`)

Analyze weekly schedule to optimize energy and productivity.

### Data Source — `gog` CLI

Use the `gog` CLI (installed at `/opt/homebrew/bin/gog`) to fetch Google Calendar data. **NEVER use screenshots** — LLMs cannot reliably distinguish Google Calendar green vs red from compressed images.

**Available accounts:**
Use `gog calendar list` to see configured accounts. Typically one work and one personal account.

**Fetch events:**
```bash
gog calendar events --account=YOUR_ACCOUNT@gmail.com --from=YYYY-MM-DD --to=YYYY-MM-DD --max=100 --json
```

**Fetch color map:**
```bash
gog calendar colors --account=YOUR_ACCOUNT@gmail.com
```

**Color mapping:**
- `colorId 10` = GREEN (`#51b749`) → **Energy Giving**
- `colorId 11` = RED (`#dc2127`) → **Energy Draining**
- No `colorId` = **Uncategorized**

### Energy Classification

Use the **actual Google Calendar colorId** from the API data. Do NOT subjectively classify events — the user's calendar colors are the source of truth.

- **Green (colorId 10)** = Energy Giving
- **Red (colorId 11)** = Energy Draining
- **No colorId** = Uncategorized (report separately)

There is no yellow/mixed category.

### Target Ratios

```
Energy Giving:   60%+
Energy Draining: 40% max
Rest Days:       1+ per week
Latest Meeting:  7pm
```

### Category Detection Rules

Map event summaries to categories using these rules (checked in order):

| Rule | Category |
|------|----------|
| `'Meditate'` in summary | Meditate |
| `'Gym'` or `'Sauna'` in summary | Gym & Sauna |
| starts with `'Team'` or equals `'Standup'` | Team |
| starts with `'Strategy'` | Strategy |
| `'Information Processing'` in summary | Info Processing |
| starts with `'Relationship'` or `'Couples Coach'` | Relationship |
| starts with `'Travel'` or `'Visa'` or `'VFS'` or `'Walk to'` | Travel/Admin |
| starts with `'Code'` | Code |
| `'Learning'` or `'Research'` in summary | Learning |
| starts with `'Recruiting'` | Recruiting |
| `'Hardware'` in summary | Hardware |
| `'Finance'` or `'Accounting'` in summary | Finance |
| equals `'Haircut'` | Personal |
| equals `'Rest'` | Rest |
| `'Ops'` in summary | Ops |
| Otherwise | Use the summary as the category name |

### Execution Flow

1. **Fetch events** — Run `gog calendar events --json` for the date range
2. **Save raw JSON** — Write to `/tmp/gcal_events.json`
3. **Run analysis script** — Execute `/tmp/analyze_calendar.py` to parse events, categorize by summary name, compute green/red totals per category and per day
4. **Generate HTML dashboard** — Build the dashboard (see layout below)
5. **Save audit to Obsidian** — Copy files to the Focus folder (see Saving to Obsidian below)
6. **Open dashboard in browser** — `open` the HTML file

### HTML Dashboard Layout

All sizing uses `clamp()` and `vh`/`vw` for dynamic viewport adaptation — fills exactly one screen.

**Body:**
```css
display: flex;
flex-direction: column;
height: 100vh;
overflow: hidden;
background: #0a0a0a;
```

**Row 1 (top)** — 4 large metrics:
- Energy Draining (red text)
- Energy Giving (green text)
- Hours Scheduled (white text)
- Rest Days (white text)
- Big numbers: `clamp(28px, 4.5vh, 56px)` with small uppercase labels above

**Row 2 (middle, `flex: 1`)** — Full-width "Time by Category" card:
- Single column of horizontal bars sorted by total hours descending
- Each bar shows green/red split proportional to max category
- Hours labels inside bars, totals on right
- Legend at bottom: Energy Giving (green dot), Energy Draining (red dot)

**Row 3 (bottom, 2-col grid)**:
- **Left** = "Energy by Day" vertical stacked bar chart (red on top, green on bottom, day labels below)
- **Right** = "Top Recommendations" numbered list with green circle numbers, bold titles, one-line descriptions

**Styling:**
- Font: Inter, tight letter-spacing
- Glassmorphism cards with `rgba(255,255,255,0.03)` background

### Saving to Obsidian

After generating the dashboard, ALWAYS perform these steps:

1. **Copy HTML** — Save to `~/Documents/ObsidianVault/Focus/time-audit-YYYY-MM-DD.html`
2. **Take screenshot** — Use Playwright headless: `npx playwright screenshot --viewport-size="1440,900" file:///path/to/dashboard.html ~/Documents/ObsidianVault/Focus/time-audit-YYYY-MM-DD.png`
3. **Save markdown summary** — Write to `~/Documents/ObsidianVault/Focus/time-audit-YYYY-MM-DD.md` containing:
   - Date range, total hours, green/red percentages
   - Category breakdown table
   - Daily breakdown table
   - Top 5 recommendations
   - Link to the HTML dashboard and screenshot

---

## Tool Cataloging Mode (`/focus tools`)

Save researched tools to both Notion and Obsidian.

### Input

- `/focus tools "tool1, tool2, tool3"` — Research and save a list of tools
- `/focus tools "tool1, tool2" --notion-only` — Save only to Notion
- `/focus tools "tool1, tool2" --obsidian-only` — Save only to Obsidian

### Execution Flow

1. **Research each tool** — Use WebSearch via Task subagents (parallel) to identify what each tool/company is
2. **Classify** — Assign tags from the existing Notion DB tag set, determine category (Dev/Infra, AI/ML/Research, Finance/Analytics/Health, etc.)
3. **Save to Notion** — Add rows to the "Tools" database (ID: `YOUR_DATABASE_ID`) under Tools > Team Tools
   - Schema: `Tool Name` (title), `Description` (rich_text), `URL` (url), `Tags` (multi_select), `Rating` (number, leave null)
   - Rating scale: 1 = No Use, 2 = Could Use, 3 = Using
4. **Save to Obsidian** — Create/update `Notion/Tools/Team Tools.md` with grouped markdown
5. **Report** — Show user a summary of what was saved

### Notion Database Details

- **Database ID**: `YOUR_DATABASE_ID`
- **Parent page**: Tools > Team Tools (`YOUR_PAGE_ID`)
- **Available tags**: See the `Tags` multi_select options in the database schema (Backend, Frontend, AI, DevOps, Research, Infrastructure, etc.)

### Obsidian Save Location

```
Notion/Tools/Team Tools.md
```

Group tools by category with each tool having: name, URL, tags, and description.

---

## Eval Dataset

This skill tracks session metrics in `evals/datasets/focus_examples.jsonl`.

**IMPORTANT: Never save raw input (capture lists) or raw output (enriched plans) to the eval dataset. These contain personal tasks, names, and sensitive context. Only save aggregate metrics.**

Each run appends:
```json
{
  "id": "focus-session-N",
  "scores": {"v2": 92},
  "metadata": {
    "date": "2026-02-05",
    "items_before": 17,
    "items_after": 15,
    "domains_created": 5,
    "tasks_surfaced": 3,
    "deduplication_merges": 2,
    "sources_queried": {
      "plaud": "available",
      "obsidian": "available",
      "calendar": "unavailable"
    },
    "patterns_applied": ["person_context_injection", "vague_to_specific"],
    "entities_extracted_count": 5
  }
}
```

The golden dataset (`focus_golden.jsonl`) contains fictional reference examples for eval scoring. It does not contain real user data.
