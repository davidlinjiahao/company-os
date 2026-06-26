# /focus Skill — Eval Results

Last updated: 2026-02-05

## Methodology

**v1** = Original /focus skill (classify + group, no data sources)
**v2** = Upgraded /focus skill (auto-enrich from Plaud, Granola, Obsidian, Calendar)

### Scoring Rubric (7 criteria, 100 points total)

| Criteria | Weight | Description |
|----------|--------|-------------|
| person_context_injection | 25 | Vague names → Full Name (Title at Company) + role + relationship + last interaction context |
| vague_to_specific | 25 | Single-word items → actionable sub-tasks with specs, dollar amounts, dates |
| domain_grouping | 15 | Items grouped by operational context (WHO/WHERE), not generic categories |
| why_injection | 10 | Tasks have "so that [outcome]" or clear purpose |
| adjacency_surfacing | 15 | New tasks surfaced from transcript data that weren't in original capture |
| item_migration | 5 | All items leave Capture → Q1/Q2/Parked/Deleted appropriately |
| deduplication | 5 | No duplicate items; related items merged |

---

## Results Summary

| Session | Date | Input Items | v1 Score | v2 Score | Delta |
|---------|------|:-----------:|:--------:|:--------:|:-----:|
| **session-1** | 2026-02-05 | 17 | — | 97/100 | — |
| **session-2** | 2026-01-23 | 24 | **31/100** | **92/100** | **+61** |
| **session-3** | 2026-01-24 | ~35 | **8/100** | **86/100** | **+78** |

**Average** (scored sessions): v1 = 19.5/100 → v2 = 91.7/100 (+72.2 improvement)

---

## Key Insights

### What v2 adds that v1 cannot
1. **Real data backing**: v2 pulls actual transcript summaries, ERM status, meeting dates, and action items from 4 data sources. v1 can only rearrange what the user typed.
2. **Person context**: v2 surfaces full names, roles, companies, interview histories, and hiring decisions. v1 leaves vague names as-is.
3. **Adjacent tasks**: v2 discovers 6-8 hidden action items per session from transcript data. v1 surfaces zero.
4. **Strategic context**: v2 connects items to company strategy. v1 has no strategic awareness.

### Where v2 still falls short
1. **Calendar context**: Calendar MCP was unavailable for early test runs, so time-sensitive enrichment couldn't be applied.
2. **Question specificity**: Golden dataset had hyper-specific sub-questions from transcripts. v2 doesn't always generate that level of detail.
3. **WHY injection depth**: Golden has deeper purpose statements. v2's WHY injection is present but could be stronger.

### Recommendations for v3
- Get Calendar MCP working to enable time-sensitive prioritization
- Add deeper sub-question generation from transcript action items
- Consider adding a "confidence" indicator for each enrichment (high = from transcript, medium = from vault, low = inferred)

---

## File Index

| File | Description |
|------|-------------|
| `datasets/focus_golden.jsonl` | Golden eval: sanitized before/after + scoring rubric |
| `datasets/focus_examples.jsonl` | Session metrics only (scores, counts — no raw input/output) |
| `results/eval_results.md` | This file — scoring methodology and analysis |
