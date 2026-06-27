---
name: search
description: Deep research skill using qmd local search, Vault team knowledge, Firecrawl, Parallel.ai, Reddit+X social search, and subagents. Searches local docs + team vault first, then falls back to web if needed. Run with "/search [topic]" for multi-source research synthesis.
user-invocable: true
disable-model-invocation: false
argument-hint: "[topic] [--local-only] [--web-only] [--social] [--depth shallow|medium|deep] [--sources N] [--save]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, WebFetch, WebSearch, mcp__vault__*
---

# Deep Research Skill

**Local-first** research using qmd + Vault (team shared knowledge) for personal and company knowledge, with web fallback via Firecrawl, Parallel.ai, Reddit+X social search, and parallel subagents.

## Quick Reference

```
/search "hardware vendor decision"             # Local first, then web
/search "my principles on hiring" --local-only # Only search local docs
/search "AI agent frameworks 2026" --web-only  # Skip local, go straight to web
/search "AISI eval frameworks" --save         # Save to Obsidian
/search "Claude Code tips" --social           # Include Reddit + X discussions
/search "prompt engineering" --social --recent 30  # Social + last 30 days
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       /search [topic]                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│  STEP 1a: LOCAL (qmd)     │   │  STEP 1b: VAULT               │
│                           │   │  (Team Shared Knowledge)      │
│  qmd query "[topic]" -n10 │   │                               │
│  • Obsidian vault         │   │  vault_search(query=topic)    │
│  • Transcripts            │   │  • decisions                  │
│  • Decisions, Code        │   │  • code, transcripts          │
│                           │   │  • team-docs, reading         │
│  BM25 + Vector + Rerank   │   │  BM25 keyword search          │
└───────────────────────────┘   └───────────────────────────────┘
                │                               │
                └───────────────┬───────────────┘
                                │
               ┌────────────────┴────────────────┐
               │                                 │
     Results found (score > 0.5)?         No results / low score
               │                                 │
               ▼                                 ▼
    ┌─────────────────┐          ┌─────────────────────────────────┐
    │ Return Local    │          │  STEP 2: WEB SEARCH             │
    │ Results + Ask   │          │                                 │
    │ if web needed   │          │  ┌───────────┬───────────┐      │
    └─────────────────┘          │  │Parallel.ai│ Firecrawl │      │
                                 │  │Deep Res.  │ URL Scrape│      │
                                 │  └───────────┴───────────┘      │
                                 │         │                       │
                                 │         ▼                       │
                                 │  ┌─────────────────┐            │
                                 │  │ WebSearch       │            │
                                 │  │ (Claude native) │            │
                                 │  └─────────────────┘            │
                                 └─────────────────────────────────┘
                                                │
                          (if --social or --depth deep)
                                                │
                                                ▼
                                 ┌─────────────────────────────────┐
                                 │  STEP 2.5: SOCIAL SEARCH        │
                                 │  (last30days - Reddit + X)      │
                                 │                                 │
                                 │  scripts/last30days.py          │
                                 │  • Reddit via OpenAI web_search │
                                 │  • X via xAI x_search           │
                                 │  • Engagement-weighted scoring  │
                                 └─────────────────────────────────┘
                                                │
                                                ▼
                                 ┌─────────────────────────────────┐
                                 │  STEP 3: SYNTHESIS              │
                                 │  • Merge local + vault + web    │
                                 │  • Deduplicate                  │
                                 │  • Rank by relevance + recency  │
                                 │  • Weight social by engagement  │
                                 └─────────────────────────────────┘
                                                │
                                                ▼
                                      ┌─────────────────┐
                                      │ Research Report │
                                      └─────────────────┘
```

## Step 1: Local Search with qmd

**qmd** is a local hybrid search engine that combines:
- **BM25** (keyword matching via SQLite FTS5)
- **Vector search** (semantic similarity via embeddings)
- **LLM reranking** (Qwen3 0.6B for relevance scoring)

### Indexed Collections

| Collection | Path | Content |
|------------|------|---------|
| `decisions` | ObsidianVault/Decisions | Team decision docs |
| `code` | ObsidianVault/Code | API keys, prompts, evals |
| `transcripts` | ObsidianVault/Transcripts | Plaud, Loom |
| `ceo` | ObsidianVault/Notion/CEO | CEO principles, network |
| `team-docs` | ObsidianVault/Notion/Company | Company docs |
| `reading` | ObsidianVault/Reading | Reading list, materials |

### qmd Commands

```bash
# Hybrid search with query expansion + reranking (best quality)
qmd query "hardware vendor decision" -n 10

# Fast keyword search (BM25 only)
qmd search "Acme V5 contract"

# Semantic search (vector only)
qmd vsearch "principles for hiring decisions"

# Search specific collection
qmd query "eval framework" -c code -n 5

# Get full document content
qmd get "qmd://decisions/Hardware Decision.md"
```

### Scoring Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| 0.8 - 1.0 | High relevance | Return as primary source |
| 0.5 - 0.8 | Moderate relevance | Include, may need web supplement |
| < 0.5 | Low relevance | Skip, proceed to web search |

## Step 1b: Vault Search (Team Shared Knowledge)

Runs **in parallel** with qmd. Vault-mcp searches the team's shared knowledge base — documents that teammates have contributed but may not be in your local qmd index yet.

**When it runs:**
- Auto for all depths (shallow, medium, deep)
- Included under `--local-only` (vault is company-internal data)
- Skipped under `--web-only`

**How to call:**
```
mcp__vault__vault_search(query=topic)
```

Then for any promising results, fetch full content:
```
mcp__vault__vault_read(uri="vault://collection/document.md")
```

**Collections:**

| Collection | Content |
|------------|---------|
| `decisions` | Team decision docs |
| `code` | Code docs, prompts, evals |
| `transcripts` | Shared meeting transcripts |
| `team-docs` | Company docs |
| `reading` | Reading materials |

**Coverage comparison (qmd vs Vault):**

| Source | qmd | Vault |
|--------|-----|-------|
| Obsidian vault files (local) | Yes | No |
| Team shared docs (remote) | No | Yes |
| Plaud transcripts | Yes | Yes |

**Graceful fallback:** If vault MCP is not configured or unavailable (ngrok tunnel down, not authenticated), continue with qmd results only. Do not fail the search. Log "Vault unavailable — using local search only".

## Step 2: Web Search (Fallback)

Only triggered when:
1. `--web-only` flag is set, OR
2. Local search returns no results (or all scores < 0.5), OR
3. User explicitly requests web search after seeing local results

### Data Sources

#### 1. Parallel.ai Search API

**Best for**: High-quality web search with structured dates, LLM-optimized excerpts, domain filtering.

```python
# scripts/lib/parallel.py
from lib import parallel
results = parallel.search(api_key, topic, max_results=10, after_date="2026-01-01")
items = parallel.normalize_results(results)  # → List[WebSearchItem]
```

Key advantage: returns `publish_date` per result → date_confidence = "high" → +10 scoring bonus.

**Env var**: `PARALLEL_API_KEY`
**Endpoint**: `POST https://api.parallel.ai/v1beta/search`
**Auth header**: `x-api-key`

#### 2. Firecrawl Search + Scrape

**Best for**: Web search with optional full-page markdown scraping for deep content extraction.

```python
# scripts/lib/firecrawl.py
from lib import firecrawl
results = firecrawl.search(api_key, topic, limit=10, time_filter="qdr:m")
items = firecrawl.normalize_results(results)  # → List[WebSearchItem]
```

Two modes: search-only (cheap, 2 credits/10 results) or search+scrape (gets full markdown content).

**Env var**: `FIRECRAWL_API_KEY`
**Endpoint**: `POST https://api.firecrawl.dev/v2/search`
**Auth header**: `Authorization: Bearer`

#### 3. Greptile Code Search (PLANNED)

**Best for**: Searching across GitHub repos for code examples. *Not yet implemented — planned integration.*

#### 4. WebSearch (Built-in)

**Best for**: Quick web searches, finding URLs to scrape

Uses Claude's built-in WebSearch tool for initial discovery.

#### 5. last30days (Reddit + X Social Search)

**Best for**: Current community discussions, trending opinions, prompt techniques, tool recommendations from the last 30 days

```bash
# Social search (optional)
OPENAI_API_KEY=your-openai-key    # For Reddit search via OpenAI Responses API
XAI_API_KEY=your-xai-key          # For X search via xAI Responses API
```

**Three operational modes:**
- **Full Mode** (both keys): Reddit + X with engagement metrics (upvotes, likes, RTs)
- **Partial Mode** (one key): Reddit-only or X-only + WebSearch supplement
- **Web-Only Mode** (no keys): Falls back to WebSearch (still useful)

**Output**: Scored results with engagement signals, deduplicated across sources.

```bash
# Run social search
python3 scripts/last30days.py "$TOPIC" --emit=compact

# With options
python3 scripts/last30days.py "$TOPIC" --emit=json    # JSON output
python3 scripts/last30days.py "$TOPIC" --sources=reddit  # Reddit only
```

## Execution Flow

### Default Flow (local-first)

```python
# 1. Search local + team sources in parallel
qmd_results, vault_results = await asyncio.gather(
    qmd_query(topic, n=10),
    vault_search(query=topic) if not web_only else None,
)

# 2. Merge and filter by score
local_results = merge_and_dedupe(qmd_results, vault_results)
good_results = [r for r in local_results if r.score >= 0.5]

if good_results:
    # 3a. Show local results, ask if web needed
    display_results(good_results)
    if user_wants_web:
        web_results = search_web(topic)
        merged = merge_and_dedupe(good_results, web_results)
        return merged
    return good_results
else:
    # 3b. No local results, go to web
    web_results = search_web(topic)
    return web_results
```

### Parallel Web Search

For `--depth deep` or `--social`, spawn parallel searches:

```python
# Run in parallel (local sources already completed in Step 1)
results = await asyncio.gather(
    parallel_ai_research(topic),
    firecrawl_search(topic),
    greptile_search(topic) if is_code_related else None,
    web_search(topic),
    social_search(topic) if social_flag or depth == "deep" else None,
)

# Synthesize — merge with local + vault results, weight social by engagement
synthesis = synthesize_research(local_results, vault_results, results)
```

### Social Search

Triggered when `--social` flag is set, or automatically for `--depth deep`.

**Synthesis rules for social sources:**
- Weight Reddit/X results HIGHER than generic web (they have engagement signals)
- Identify cross-source patterns (mentioned on both Reddit AND X = strong signal)
- Note contradictions between community opinion and official docs
- Extract top 3-5 actionable insights grounded in actual discussions

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--local-only` | Only search local qmd + Vault | false |
| `--web-only` | Skip local, go straight to web | false |
| `--social` | Include Reddit + X search (last 30 days) | false (auto for deep) |
| `--depth` | shallow, medium, deep | medium |
| `--sources` | Max web sources to analyze | 15 |
| `--save` | Save results to Obsidian vault | false |
| `--format` | markdown, json | markdown |
| `--collection` | Search specific qmd collection | all |
| `--academic` | Prioritize academic sources (web) | false |
| `--recent` | Only web sources from last N days | none |

## Depth Levels

| Depth | Local | Vault | Web Sources | Social | Subagents | Time | Use Case |
|-------|-------|-------|-------------|--------|-----------|------|----------|
| `shallow` | qmd only | Yes | 0 (unless no local) | No | 0 | ~5s | Quick local lookup |
| `medium` | qmd first | Yes | 10-20 | If `--social` | 1 | ~1min | Standard research |
| `deep` | qmd + all | Yes | 20-50 | Yes (auto) | 4 | ~5min | Comprehensive analysis |

## Output Format

```markdown
# Research Report: [Topic]

**Generated**: 2026-01-24 15:00
**Depth**: medium
**Local Sources**: 5
**Vault Sources**: 3
**Web Sources**: 12

---

## Local Findings (from your vault)

### 1. [Document Title]
**Source**: qmd://decisions/hardware-decision.md (score: 0.87)
[Relevant excerpt...]

### 2. [Document Title]
**Source**: qmd://transcripts/plaud/meeting-2026-01-20.md (score: 0.72)
[Relevant excerpt...]

---

## Vault Findings (from Team Shared Knowledge)

### 1. [Document Title]
**Source**: vault://decisions/hardware-vendor.md | BM25 match
[Relevant excerpt from team shared document...]

---

## Web Findings

### 1. [Finding Title]
**Source**: [Title](url) | Type: Industry | Credibility: High
[Details with source citations]

### 2. [Finding Title]
**Source**: [Title](url) | Type: Academic | Credibility: High
[Details with source citations]

---

## Social Findings (Reddit + X, last 30 days)

### 1. [Discussion Title]
**Source**: Reddit r/[subreddit] | Upvotes: X | Comments: Y
[Key insights from community discussion]

### 2. [Discussion Title]
**Source**: X @[handle] | Likes: X | RTs: Y | Bookmarks: Z
[Key insights from tweet/thread]

---

## Synthesis

[Combined analysis merging local knowledge + web research + social discussions]

## Gaps & Uncertainties

- [What we couldn't find]
- [Conflicting information between local and web]

---

*Research by /search skill using qmd, Vault, Parallel.ai, Firecrawl, and Claude*
```

## Environment Variables

Optional (set in shell environment or `~/.claude/.env` if it exists):

```bash
# Web search (pulled from 1Password via setup.sh)
PARALLEL_API_KEY=...    # Parallel.ai — structured search with dates
FIRECRAWL_API_KEY=...   # Firecrawl — search + optional page scraping
GREPTILE_API_KEY=...    # Greptile — GitHub code search (planned)

# Social search (optional)
OPENAI_API_KEY=your-openai-key    # Reddit search via OpenAI Responses API
XAI_API_KEY=your-xai-key          # X search via xAI Responses API

# qmd uses local models, no API keys needed
```

## Examples

### Local Knowledge Lookup

```
/search "what did we decide about hardware vendor" --local-only
```

### Personal Principles

```
/search "my principles on hiring" --local-only --collection ceo
```

### Past Conversations

```
/search "discussion with Jane Smith" --local-only --collection transcripts
```

### Full Research (Local + Web)

```
/search "developer tools market trends" --depth deep --save
```

### Web-Only Research

```
/search "Claude Agent SDK best practices 2026" --web-only --academic
```

### Code Examples

```
/search "browser automation with playwright" --web-only
```

### Social / Community Research

```
/search "Claude Code tips and tricks" --social
```

### Trending Discussions (last 30 days)

```
/search "best AI coding tools 2026" --social --recent 30
```

### Comprehensive (everything)

```
/search "CI/CD pipeline best practices" --depth deep --save
```
This runs local + web + social (Reddit/X) in parallel, saves to Obsidian.

## Managing qmd Collections

```bash
# List all collections
qmd collection list

# Add new collection
qmd collection add /path/to/folder --name myname

# Remove collection
qmd collection remove myname

# Re-index all collections
qmd update

# Re-generate embeddings (after adding new docs)
qmd embed

# Check status
qmd status
```

## Comparison with Other Tools

| Tool | Local | Vault | Web | Social | Quality | Speed | Best For |
|------|-------|-------|-----|--------|---------|-------|----------|
| WebSearch | No | No | Yes | No | Basic | Fast | Quick web lookups |
| WebFetch | No | No | Yes | No | Variable | Fast | Known URLs |
| qmd query | Yes | No | No | No | High | Fast | Local vault knowledge |
| vault_search | No | Yes | No | No | High | Fast | Team shared knowledge |
| last30days | No | No | Yes | Yes | High | Medium | Reddit + X trends |
| **/search** | Yes | Yes | Yes | Yes | High | Medium | Comprehensive research |

Use `/search` when you need:
- Local knowledge first (your vault, transcripts, decisions)
- Web fallback for external research
- Social media pulse (Reddit + X community discussions)
- Multiple sources synthesized
- Structured findings with citations
