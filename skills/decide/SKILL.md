---
name: decide
description: Structured decision framework using AskUserQuestion. Routes to quick (10-15min) for 2-way doors or thorough (20-30min) for 1-way doors. Synthesizes final recommendation with confidence score.
user-invocable: true
disable-model-invocation: false
argument-hint: "[decision question]"
allowed-tools: AskUserQuestion, Read, Glob, Grep, Bash, mcp__obsidian__*, mcp__notion__*, mcp__plaud__*, mcp__council__*
---

# Decision Framework Skill

Structured decision-making using AskUserQuestion + Council of Advisors. Differentiates between:
- **2-way doors** (reversible): Quick 10-15 min process
- **1-way doors** (irreversible): Thorough 20-30 min process

## Quick Reference

```
/decide Should we sign this contract?     # 1-way door (thorough)
/decide Which framework should we use?    # 2-way door (quick)
/decide                                    # Interactive - asks for question
/decide synthesize Hardware Vendor           # Aggregate team decision docs
```

## Execution Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. GET DECISION QUESTION                               │
│     └── From args or ask user                           │
├─────────────────────────────────────────────────────────┤
│  2. CLASSIFY DOOR TYPE                                  │
│     ├── 1-way: sign, hire, invest, quit, fire, acquire  │
│     ├── 2-way: choose, try, test, pick, use            │
│     └── Confirm with user if ambiguous                  │
├─────────────────────────────────────────────────────────┤
│  3. GATHER CONTEXT                                      │
│     ├── Search Obsidian for related notes               │
│     ├── Check Plaud for relevant transcripts             │
│     └── Look for existing decision docs                 │
├─────────────────────────────────────────────────────────┤
│  4. ASK QUESTIONS (via AskUserQuestion)                 │
│     ├── 2-way door: 3-4 quick questions (~10 min)       │
│     └── 1-way door: 6-8 deep questions (~20-30 min)     │
├─────────────────────────────────────────────────────────┤
│  5. COUNCIL OF ADVISORS                                 │
│     ├── Call council_deliberate with question + context  │
│     ├── 1-way doors: all 6 personas                     │
│     ├── 2-way doors: auto-routed subset                 │
│     └── Get persona recommendations + confidence        │
├─────────────────────────────────────────────────────────┤
│  6. SYNTHESIZE OUTPUT                                    │
│     ├── 2-way door: Recommendation (GO/NO-GO/MODIFY)    │
│     │   with council vote + confidence + next steps      │
│     ├── 1-way door: ENRICHED DECISION BRIEF             │
│     │   NO pre-baked recommendation                      │
│     │   Steelman both sides equally                      │
│     │   Key tensions where sources disagree              │
│     │   Risk matrix across all paths                     │
│     │   All 10 Decision Questions with sub-questions     │
│     │   Let the team decide together                     │
├─────────────────────────────────────────────────────────┤
│  7. SAVE DECISION                                       │
│     ├── Always: Obsidian ($OBSIDIAN_VAULT/Decisions/)   │
│     ├── Always: Notion (Decisions database)             │
│     └── Always: Slack notification (#decisions)         │
└─────────────────────────────────────────────────────────┘
```

## Door Type Detection

### 1-Way Door Keywords (Irreversible)
- sign, contract, hire, fire, invest, acquire, merge
- quit, resign, terminate, shut down, pivot
- launch, announce, commit, promise
- buy (large purchase), sell (company/asset)

### 2-Way Door Keywords (Reversible)
- try, test, experiment, prototype
- choose, pick, select, prefer
- use, switch, adopt, implement
- schedule, plan, organize

## Question Framework

### 2-Way Door Questions (10-15 min total)

Ask questions in 1-2 batches using AskUserQuestion:

**Batch 1: Context & Goal**
```json
{
  "questions": [
    {
      "question": "What are the top 2-3 options you're considering?",
      "header": "Options",
      "options": [
        {"label": "Option A", "description": "First choice you're considering"},
        {"label": "Option B", "description": "Second choice you're considering"},
        {"label": "Option C", "description": "Third choice if applicable"}
      ],
      "multiSelect": false
    },
    {
      "question": "What's the main goal you're trying to achieve?",
      "header": "Goal",
      "options": [
        {"label": "Speed", "description": "Get to market/completion faster"},
        {"label": "Cost", "description": "Minimize spend or resource usage"},
        {"label": "Quality", "description": "Best possible outcome regardless of speed"},
        {"label": "Learning", "description": "Gain knowledge for future decisions"}
      ],
      "multiSelect": false
    }
  ]
}
```

**Batch 2: Constraints & Lean**
```json
{
  "questions": [
    {
      "question": "What's your biggest constraint right now?",
      "header": "Constraint",
      "options": [
        {"label": "Time", "description": "Deadline pressure or urgency"},
        {"label": "Budget", "description": "Cost or resource limits"},
        {"label": "Expertise", "description": "Team skills or knowledge gaps"},
        {"label": "Risk", "description": "Need a safe, proven choice"}
      ],
      "multiSelect": false
    },
    {
      "question": "If you had to decide right now, which way would you lean?",
      "header": "Gut feel",
      "options": [
        {"label": "Option A", "description": "Leaning toward first choice"},
        {"label": "Option B", "description": "Leaning toward second choice"},
        {"label": "Undecided", "description": "Genuinely 50/50"}
      ],
      "multiSelect": false
    }
  ]
}
```

### 1-Way Door Questions (20-30 min total)

Ask questions in 3-4 batches using AskUserQuestion:

**Batch 1: Stakes & Timeline (5 min)**
```json
{
  "questions": [
    {
      "question": "What makes this decision hard to reverse?",
      "header": "Stakes",
      "options": [
        {"label": "Financial", "description": "Large money at stake that can't be recovered"},
        {"label": "Reputation", "description": "Public commitment or relationship impact"},
        {"label": "Legal", "description": "Contracts, agreements, or obligations"},
        {"label": "Opportunity", "description": "Closes off other paths or options"}
      ],
      "multiSelect": true
    },
    {
      "question": "What's the timeline for this decision?",
      "header": "Timeline",
      "options": [
        {"label": "Urgent (days)", "description": "Need to decide within a week"},
        {"label": "Soon (weeks)", "description": "Have 2-4 weeks to decide"},
        {"label": "Can wait (months)", "description": "No immediate pressure"},
        {"label": "No deadline", "description": "Decide when ready"}
      ],
      "multiSelect": false
    }
  ]
}
```

**Batch 2: Options & Outcomes (8 min)**
```json
{
  "questions": [
    {
      "question": "What's the BEST case outcome if you proceed?",
      "header": "Upside",
      "options": [
        {"label": "10x growth", "description": "Transformative positive impact"},
        {"label": "2x improvement", "description": "Significant but incremental gain"},
        {"label": "Small win", "description": "Modest positive outcome"},
        {"label": "Parity", "description": "Maintain current position"}
      ],
      "multiSelect": false
    },
    {
      "question": "What's the WORST case outcome if you proceed?",
      "header": "Downside",
      "options": [
        {"label": "Existential", "description": "Could end the company/project"},
        {"label": "Major setback", "description": "Significant but recoverable loss"},
        {"label": "Minor loss", "description": "Small cost, easily absorbed"},
        {"label": "Neutral", "description": "Worst case is just wasted time"}
      ],
      "multiSelect": false
    }
  ]
}
```

**Batch 3: Values & Stakeholders (8 min)**
```json
{
  "questions": [
    {
      "question": "Which principle should guide this decision?",
      "header": "Principle",
      "options": [
        {"label": "Optimize for learning", "description": "Choose what teaches the most"},
        {"label": "Bias toward action", "description": "Default to doing vs waiting"},
        {"label": "Protect optionality", "description": "Keep doors open"},
        {"label": "Think long-term", "description": "10-year view over short-term"}
      ],
      "multiSelect": false
    },
    {
      "question": "Who else is significantly affected by this decision?",
      "header": "Stakeholders",
      "options": [
        {"label": "Just me", "description": "Personal decision only"},
        {"label": "My team", "description": "Direct reports or collaborators"},
        {"label": "Company-wide", "description": "All employees affected"},
        {"label": "External", "description": "Customers, investors, partners"}
      ],
      "multiSelect": true
    }
  ]
}
```

**Batch 4: Regret & Confidence (5 min)**
```json
{
  "questions": [
    {
      "question": "What would you regret more?",
      "header": "Regret test",
      "options": [
        {"label": "Doing it and failing", "description": "Regret taking the risk"},
        {"label": "Not doing it", "description": "Regret missing the opportunity"},
        {"label": "Equal", "description": "Would regret both equally"}
      ],
      "multiSelect": false
    },
    {
      "question": "How confident are you in your current lean?",
      "header": "Confidence",
      "options": [
        {"label": "Very confident (8-10)", "description": "Strong conviction"},
        {"label": "Somewhat (5-7)", "description": "Leaning but unsure"},
        {"label": "Uncertain (1-4)", "description": "Genuinely don't know"}
      ],
      "multiSelect": false
    }
  ]
}
```

## Step 5: Council of Advisors

After gathering user context, call the Council for multi-persona deliberation.

**Call `mcp__council__council_deliberate`** with:
- `query`: The decision question + summarized context from user's answers
- `personas`: For 1-way doors, use all 6: `["elon", "ilya", "bezos", "sam", "founder", "pg"]`. For 2-way doors, omit the field (auto-routes to most relevant personas).

**If Council MCP is unavailable**, skip this step. Use the gathered context + user answers to synthesize directly. Note "Council unavailable" in the output. The decision framework is still valuable without the council — the questions and structured thinking are the core value.

The council returns:
- `response`: Synthesized recommendation
- `confidence`: 0-1 confidence score
- `persona_responses`: Dict of each persona's analysis
- `selected_personas`: Which personas were consulted
- `citations`: Sources from the knowledge base
- `routing_decision`: How the question was classified

**Extract from each persona response**:
- Their recommendation (Go / No-go / Modify)
- One sentence of key reasoning
- Any unique insight or disagreement

## Output Format

### 2-Way Door Synthesis Template

For reversible decisions, use this lighter format with a clear recommendation:

```markdown
# Decision: [Question]

## Recommendation: [GO / NO-GO / MODIFY]
**Confidence:** [X]%  |  **Door Type:** 2-way

---

## Council of Advisors

| Advisor | Vote | Key Reasoning |
|---------|------|---------------|
| Elon    | Go   | First principles: [1 sentence] |
| Ilya    | Modify | Technical concern: [1 sentence] |
| Bezos   | Go   | Customer impact: [1 sentence] |

**Consensus:** [X/Y] Go ([Z]%)

---

## Summary

[2-3 sentences incorporating best insights from council + user Q&A]

---

## Next Steps

1. [First action]
2. [Second action]
3. [Third action]

---

*Decision made: [timestamp]*
*Saved to: Obsidian | Notion*
*Team notified: #decisions*
```

### 1-Way Door Synthesis Template

For irreversible decisions, use this enriched format. **CRITICAL: Do NOT pre-bake a recommendation.** Present both sides objectively and let the team decide.

Reference implementation: `Decisions/Data Collection/2026-02-14-Quantity-vs-Quality.md`

```markdown
---
query: "[decision question]"
recommendation: PENDING TEAM DECISION
door_type: 1-way
confidence: null
date: YYYY-MM-DD
sources:
  - "[Source 1]"
  - "[Source 2]"
tags: [decision, ...]
---

# Decision: [Question]

**Date:** [date] | **Door Type:** 1-way | **Timeline:** [urgency]

---

## Context

[Brief situational summary: where the company is, what triggered the decision,
what's at stake. Include timeline pressures and key actors.]

---

## The Case for [Option A]

### 1. [Strongest argument]
[Steelmanned argument with direct quotes from source material]

### 2. [Next argument]
[Include data tables where available]

### 3-7. [Continue with 5-8 total arguments]
[Cite specific sources inline. Use verbatim quotes when powerful.]

---

## The Case for [Option B]

### 1. [Strongest argument]
[EQUALLY steelmanned — same depth, same quality of evidence as Option A]

### 2-8. [Continue with 5-8 total arguments]
[Same standard. No bias toward either side.]

---

## Key Tensions

### Tension 1: [Where sources disagree with each other]
[Use tables to show conflicting recommendations from different sources]

### Tension 2: [Chicken-and-egg problem]
[Name it explicitly]

### Tension 3-5: [Continue with 3-5 genuine tensions]
[The most valuable section — this is where the real tradeoffs live]

---

## Risk Matrix

| Risk | If we go [Option A] | If we go [Option B] | If we split focus |
|------|---------------------|---------------------|-------------------|
| **[Risk 1]** | HIGH/MED/LOW — [why] | HIGH/MED/LOW — [why] | HIGH/MED/LOW |
| **[Risk 2]** | ... | ... | ... |
| **[Risk 3]** | ... | ... | ... |

---

## Decision Questions for the Team

*Based on our Decision Making Principles:*

### 1. Do I have to make this decision right now?
[Applied specifically to THIS decision with real dates and stakes]

### 2. What is the goal?
[Frame as: "Is the goal X (Option A thesis) or Y (Option B thesis)?"]

### 3. Is this a 1-way door or 2-way door?
- 3a. **Is there a third door / win-win scenario?**

### 4. Does this eliminate future decisions?
- 4a. **What is the input/outcome symmetry?**
- 4b. **What is the decision half-life?**
- 4c. **Does it pay dividends or does it decay?**

### 5. What's the ONE thing that would make this easier or unnecessary?
- 5a. **What are the dependencies?**
- 5b. **What is optimal sequencing?**
- 5c. **Counteract troughs with inverse peaks**

### 6. What is best for the long term?
- 6a. **What do the option vectors look like?**
- 6b. **What are the 2nd order consequences?**
- 6c. **How does this change at the limits?**

### 7. Can you simplify or inverse the problem?
- 7a. **What are the first principles?**
- 7b. **What are the constraints?**
- 7c. **What is the anti-vision?**

### 8. What are you afraid of?
- 8a. **Probability × Impact** for each fear
- 8b. **Will you regret this?** Frame both regrets explicitly.
- 8c. **Is this going up or down in difficulty?**

### 9. Does this align with our values/mission?
- 9a. **Is this high integrity?**
- 9b. **What would you do if it was your last year on earth?**
- 9c. **Would 10-year-old me and 80-year-old me be proud?**

### 10. What is your single decisive reason?
[Map different decisive reasons to different outcomes:]
- If your single decisive reason is **"[reason X]"** → Option A
- If your single decisive reason is **"[reason Y]"** → Option B
- If your single decisive reason is **"[reason Z]"** → Modified path

---

## Sources

| Source | Key Contribution to This Decision |
|--------|----------------------------------|
| **[Source 1]** | [What it adds] |
| **[Source 2]** | [What it adds] |

---

*Prepared: [timestamp]*
*Status: Pending team discussion*
*Saved to: Obsidian*
```

### Key Principles for 1-Way Door Docs

1. **No pre-baked recommendation** — Set `recommendation: PENDING TEAM DECISION`. The team decides together.
2. **Steelman both sides equally** — Same number of arguments, same quality of evidence, same depth for each option.
3. **Surface tensions explicitly** — Where sources contradict each other is the most valuable section.
4. **Direct quotes from source material** — Verbatim quotes > paraphrases. Use `>` blockquotes with source attribution.
5. **Data tables over prose** — Ablation results, pricing tiers, risk matrices, sequencing comparisons.
6. **Decision questions are specific, not generic** — Each question must reference the actual options, numbers, and tradeoffs of THIS decision.
7. **Question 10 maps decisive reasons to outcomes** — "If your single decisive reason is X → Option A. If Y → Option B."
8. **Include all sub-questions** — 3a, 4a-4c, 5a-5c, 6a-6c, 7a-7c, 8a-8c, 9a-9c. These force depth.
9. **Gather context exhaustively before writing** — Read all relevant Obsidian notes, Plaud transcripts, papers, and memos. The doc should synthesize ALL available context, not just what's top of mind.
10. **Sources table at the end** — Every source cited in the doc gets a row mapping it to its specific contribution to this decision. No orphan citations.

## Context Gathering (Before Questions)

Search for relevant context to inform questions. **Check each source's availability first — if unavailable, skip and move on. Partial context is fine.**

```python
# Search shared vault via obsidian MCP (if configured)
mcp__obsidian__search(query=decision_topic, folder="decisions")
mcp__obsidian__search(query=decision_topic, folder="")

# Or search local Obsidian vault directly via Glob/Grep
Grep(pattern=decision_topic, path="~/Documents/ObsidianVault/Decisions/")
Grep(pattern=decision_topic, path="~/Documents/ObsidianVault/Transcripts/")

# Plaud transcripts (if configured)
mcp__plaud__search_transcripts(query=decision_topic, days=30)

```

**Graceful degradation**: If Council, Obsidian, or Plaud MCPs are unavailable, use local file search (Glob/Grep on the Obsidian vault) as a fallback. Never fail the decision because a data source is down.

## Step 7: Save Decision

### 7a. Save to Obsidian (always)

Save to: `decisions/[YYYY-MM-DD] [Decision Title].md` (in the shared vault via obsidian MCP)

Use the full synthesis template output as the file content.

### 7b. Save to Notion (if available)

Add a row to the **Team Decisions** database via `mcp__notion__create_database_row`. Search for the database first via `mcp__notion__search_pages(query="Team Decisions", filter_type="database")`.

Call the Notion MCP to create a page in this database with properties:
- **Decision** (title): The question
- **Door Type** (select): "1-way" or "2-way"
- **Recommendation** (select): "Go", "No-go", or "Modify"
- **Confidence** (number): 0-100 (as decimal, e.g. 0.85 for 85%)
- **Status** (select): "Concluded"
- **Category** (select): "Technical", "Business", "People", "Product", "Personal", or "Startups"
- **Council Vote** (rich_text): e.g. "5/6 Go (83%)"
- **Sources** (rich_text): Citation references from council

**Decision title**: Use short 2-4 word names (e.g. "Hire Senior Engineer", "Cloud Provider", "New Office") — match the style of existing entries like "Office Location", "Team Lead".

**Page body**: After creating the database row, format the page body with native Notion tables and colored headings using `append_blocks` then `update_block`. Use the **simplified MCP format** (NOT raw Notion API block format).

```
# Step 1: Append blocks using simplified format
mcp__notion__append_blocks(page_id=page_id, blocks=[
  {"type": "heading_3", "text": "What is the decision?"},
  {"type": "table", "rows": [
    ["Decision", "<decision question>"],
    ["1 Way or 2 Way", "<door type and why>"]
  ], "has_column_header": false, "has_row_header": true},

  {"type": "heading_3", "text": "What are the trade offs?"},
  {"type": "table", "rows": [
    ["Options", "Effort (1-5)", "Pros", "Cons"],
    ["<Option A>", "<1-5>", "<pros>", "<cons>"],
    ["<Option B>", "<1-5>", "<pros>", "<cons>"]
  ], "has_column_header": true, "has_row_header": true},

  {"type": "heading_3", "text": "What is our single decisive reason?"},
  {"type": "table", "rows": [
    ["Decision", "<chosen option or PENDING>"],
    ["Rationale", "<single decisive reason>"]
  ], "has_column_header": false, "has_row_header": true},

  {"type": "heading_3", "text": "What did we learn?"},
  {"type": "bulleted_list_item", "text": "<learning 1>"},
  {"type": "bulleted_list_item", "text": "<learning 2>"},
  {"type": "bulleted_list_item", "text": "<learning 3>"},

  {"type": "heading_3", "text": "Decision checklist"},
  {"type": "table", "rows": [
    ["Do I have to make this decision right now?", "<answer>"],
    ["What is the Goal?", "<answer>"],
    ["Does this eliminate future decisions?", "<answer>"],
    ["Is this a 1 way door or 2 way door?", "<answer>"],
    ["Is there a third door / win-win scenario?", "<answer>"],
    ["What's the ONE thing that makes everything else easier or unnecessary?", "<answer>"],
    ["What is best for the long term?", "<answer>"],
    ["Can you simplify or inverse the problem?", "<answer>"],
    ["What are you afraid of?", "<answer>"],
    ["Does this align with our values / mission?", "<answer>"]
  ], "has_column_header": false, "has_row_header": true}
])

# Step 2: Color the heading blocks (positions 0, 2, 4, 6, N in returned block_ids)
# Use update_block with rich_text annotations for each heading:
heading_colors = {
  "What is the decision?": "red",
  "What are the trade offs?": "yellow",
  "What is our single decisive reason?": "green",
  "What did we learn?": "orange",
  "Decision checklist": "purple"
}
# For each heading block_id:
mcp__notion__update_block(block_id=heading_id, fields={
  "heading_3": {
    "rich_text": [{"type": "text", "text": {"content": "<heading text>"}, "annotations": {"color": "<color>"}}]
  }
})
```

**Important MCP format notes:**
- The `append_blocks` MCP tool uses a **simplified interface** — pass `{"type": "table", "rows": [...]}` NOT raw Notion API format with nested `table`/`table_row` objects
- Heading colors require a **separate `update_block` call** after creation — the simplified `append_blocks` format doesn't support color annotations
- The heading block IDs are at even positions in the returned `block_ids` array (0, 2, 4, 6) plus the last heading which depends on bullet count

If the Notion MCP is unavailable or errors, skip with a note. Don't block the decision.

### 7c. Notify via Slack (always)

Post to `#decisions` channel using Slack webhook:

```bash
curl -s -X POST "$SLACK_DECISIONS_WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "*Decision: [Question]*\n*Recommendation:* [GO/NO-GO/MODIFY] ([X]% confidence)\n*Door Type:* [1-way/2-way]\n*Council:* [X/Y] Go\n*Summary:* [1 sentence]"
  }'
```

If `$SLACK_DECISIONS_WEBHOOK` is not set (check with `echo $SLACK_DECISIONS_WEBHOOK`), skip with a note. Don't error.

## Multi-Person Synthesis

For team decisions, aggregate multiple decision docs:

```
/decide synthesize Hardware Vendor
```

1. Search `Decisions/` folder for matching docs
2. Extract each person's recommendation and confidence
3. Calculate consensus and dissent
4. Produce team synthesis with vote breakdown

## Examples

### 2-Way Door Example

```
/decide Which database should we use for the new service?

[Batch 1: 2 questions about options and goals]
[Batch 2: 2 questions about constraints and gut feel]
[Council: auto-routes to Elon + Ilya + Bezos]

# Decision: Database Selection

## Recommendation: GO with PostgreSQL
**Confidence:** 85%  |  **Door Type:** 2-way

## Council of Advisors

| Advisor | Vote | Key Reasoning |
|---------|------|---------------|
| Elon    | Go (Postgres) | First principles: relational model has decades of proven reliability |
| Ilya    | Go (Postgres) | Theoretical foundation of ACID is mathematically sound |
| Bezos   | Go (Postgres) | Customer data integrity is non-negotiable |

**Consensus:** 3/3 Go (100%)

## Summary

PostgreSQL matches your goals (reliability) and constraints (team expertise).
It's battle-tested, your team knows it, and migration is possible if needs change.

**Next Steps:**
1. Set up PostgreSQL 16 on primary instance
2. Configure connection pooling
3. Revisit in 6 months if query patterns change
```

### 1-Way Door Example

```
/decide Should we scale data quantity in India or scale data quality in SF?

[Batch 1-4: 8 deep questions]
[Context gathered from Obsidian, Plaud]
[Council: all 6 personas consulted]

→ Output uses the enriched 1-Way Door Synthesis Template:
  - recommendation: PENDING TEAM DECISION (no pre-baked answer)
  - The Case for India Quantity (7 steelmanned arguments with direct quotes)
  - The Case for SF Quality (8 steelmanned arguments with direct quotes)
  - Key Tensions (5 genuine tensions where sources disagree)
  - Risk Matrix (6 risks scored across all paths)
  - Decision Questions (all 10 from Decision Making Principles with sub-questions)
  - Sources table

See canonical example:
Decisions/Data Collection/2026-02-14-Quantity-vs-Quality.md
```

## Integration Notes

This skill can be invoked by:
- User directly: `/decide [question]`
- Council agent: When routing 1-way door decisions
- Decision docs: Reference past `/decide` outputs

For team decisions, each member runs `/decide` independently, then someone runs `/decide synthesize [topic]` to aggregate.
