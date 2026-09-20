---
name: source
description: Turn a hiring need into a genuinely A-grade candidate list. Use when someone wants to source, recruit, or hire for a role — "find candidates", "build a candidate list", "who should we hire for X", "write a scorecard", "/source [role]". Runs the WHO method: scorecard first, then a parameterized multi-source sweep, then a strict A-bar filter where every claim carries an openable evidence link, then a ranked list.
---

# /source — hiring need → A-grade candidate list

**Prime directive: an honest short list beats a padded one.** Ten real A-players is a great outcome. Three is a fine outcome. Thirty names that "look decent" is a failure — it moves the filtering work onto the person who asked, which was the whole job.

Method spine: **WHO** (Geoff Smart & Randy Street, *Who: The A Method for Hiring*) — write the bar down before you see anyone, then score everyone against that same written bar.

Seven phases, in order. Do not start sourcing before the scorecard exists; a sweep without a bar produces a pile, not a list.

```
UNDERSTAND → SCORECARD → PROFILE → CALIBRATE → SWEEP → FILTER → DELIVER
```

Details live next door — read the reference file for the phase you are in, not all of them:
- `references/scorecard.md` — WHO scorecard template, how to write A-bar legs that are actually decidable
- `references/sources.md` — every source, what it really yields, credentials, the scripts
- `references/agents.md` — parallel sourcing subagent prompts, loop and depletion tracking
- `references/output.md` — output format, link verification, optional PDF, optional blind judge

---

## Runtimes

This skill runs in two places. Check which one you are in before planning the sweep.

| | Local (Claude Code, MCPs available) | Sandbox (shell, files, curl, env API keys) |
|---|---|---|
| Meeting/note context | MCP note + vault + calendar tools | ask the user, or work from what they pasted |
| Competitor calibration | `search` skill, Exa MCP | `curl` + `EXA_API_KEY` if set, else web reasoning + the WaaS jobs lane |
| Sweep scripts | all of `scripts/` | all of `scripts/` — standard library only, no install |
| Scorecard destination | a Notion/vault page if asked | a markdown file in the working directory |
| Output | working dir, plus `~/Desktop` if it exists | working directory |
| PDF | `make_pdf.sh` if pandoc + weasyprint present | usually absent — markdown is the deliverable |

**Rule:** every MCP-dependent step is optional and named as such. If a tool is missing, say so in the output and continue — never stall, and never quietly drop a lane without reporting it.

---

## Phase 1 — UNDERSTAND

Find the real mission: what is breaking, who owns the fix, what "shipped" looks like in 12 months.

Inputs, in order of preference: what the user says now → a JD or doc they point at → recent meeting/vault context (local only, optional) → the pain they described.

**Output:** one paragraph stating the role as *the failures it must eliminate*, not a job title. A title is not a mission. If you cannot name a failure the hire removes, ask one question before continuing.

## Phase 2 — SCORECARD

Write the scorecard: **Mission** (one paragraph) · **Outcomes** (3–8, ranked, each measurable and time-bound, set at the "an A-player has already shipped this exact thing" bar) · **Competencies** (technical + cultural) · **A-BAR legs**.

The A-bar legs are the part that matters. See `references/scorecard.md`. Rules:
- 3–6 legs, each **decidable from evidence a stranger can open**. "Strong engineer" is not a leg. "Has shipped an app to a public store and owned its crash budget" is.
- One leg must be geography/work authorization. One must be "≥2 distinct public evidence URLs, all resolving".
- Write the **exclusions** too: the adjacent-but-not profiles that will otherwise flood the results.

Show the scorecard to the user before sweeping. It is cheap to fix now and expensive to fix after 200 profiles.

## Phase 3 — PROFILE

Turn the scorecard into `scripts/profiles/<role>.json` — copy `scripts/profiles/TEMPLATE.json`. This is the only place role knowledge lives; no script hardcodes a stack, a company, or a country.

Keywords fall out of the legs: `must` = phrases only a plausible candidate writes about themselves; `stack` = supporting technology; `location` = cities, remote phrasing, work-authorization phrasing. `curated_repos` is the highest-signal field in the file — 15–25 repos a right-fit person would plausibly have touched.

## Phase 4 — CALIBRATE

Find who else is hiring this exact role, and what they call it. Purpose: (a) sanity-check the role design — one hire or two? (b) harvest the real keyword taxonomy, (c) get the comp band and geography, (d) name competitor employees as a seed pool.

Local: the `search` skill or Exa. Sandbox: `python3 scripts/yc_waas.py --mode jobs --profile <p>` gives a free read on comparable roles and pay. Feed everything learned back into the scorecard and the profile before sweeping.

## Phase 5 — SWEEP

```bash
bash scripts/sweep.sh --profile scripts/profiles/<role>.json          # all lanes + merge
bash scripts/sweep.sh --profile <p> --only github,hn                  # one or two lanes
bash scripts/sweep.sh --profile <p> --dry-run                         # show the queries, no network
```

Lanes: `hn` · `reddit` · `v2ex` (off by default) · `github` (curated repos = best lane) · `waas-jobs` · `waas-candidates` (needs `WAAS_COOKIE`). A lane without credentials skips itself and is reported; it is never silently dropped.

Run the script lanes **in parallel with agent lanes** — competitor employees, LinkedIn graph, targeted web search — using the prompts in `references/agents.md`. Scripts find people who are *publicly looking*; agents find people who are *good*. Both matter, and the second group is usually where the A-players are.

**Merge** combines the lanes and flags anyone appearing in two independent sources. Merged output is **raw sweep material, not a candidate list.**

## Phase 6 — FILTER (this phase is the product)

For each candidate, map **every A-bar leg** to a specific quotable piece of evidence with an openable URL.

- **All legs pass with evidence → list them.**
- **Exactly one leg missing but plausible → HOLD**, naming the missing leg and what would settle it.
- **Two or more missing, or an exclusion matches → excluded, with the reason written down.**

Non-negotiable: absence of evidence is *absence*, never "probably has it". Being on a team that shipped X is not shipping X. Do not average across legs. Do not let a famous employer substitute for a leg.

Then verify the evidence actually resolves:

```bash
python3 scripts/verify_links.py --input <candidates.md>
```

Any link that does not return 200 is not evidence — replace the citation or drop the claim. A candidate whose only evidence is behind a login wall does not go on the list.

## Phase 7 — DELIVER

Write `<Role>_Candidates.md` (working directory; also `~/Desktop` locally if it exists), containing:

1. **Top picks** — the 3–5 to contact first, and why each, in one line.
2. **Ranked candidates** — per candidate: the leg-by-leg evidence table with links, warmth/route-in, and the single strongest reason they are A.
3. **HOLD** — with the missing leg named.
4. **Excluded** — grouped by reason. This section is evidence of a real filter; do not omit it.
5. **Source-depletion tracker** — swept / pending / blocked-needing-you (missing credentials, bot-walled sites, warm intros only the user can make).

Optional extras: `bash scripts/make_pdf.sh <md>` for a clickable PDF, and `python3 scripts/judge_list.py --list <md> --scorecard <scorecard>` to have a different model family grade the list blind against the same legs before you hand it over.

If the sweep did not find enough A-players, **say so** and name what would unlock more — a missing credential, a different geography, a split role, or a lowered bar the user must consciously choose. Never pad the list to hit a number.

---

## Key principles

- The scorecard is written before anyone is seen, and never edited to fit a candidate you like.
- Every claim carries a link a stranger can open. Unopenable evidence is not evidence.
- Report dead-end sources honestly; a hidden blind spot is worse than an empty lane.
- Surface the levers only the user can pull, explicitly, at the end.
- Quality over volume, every single time.

## Usage tracking (company convention)

Optionally record one memory fact: `used source for <5-word purpose>`. Skip if no memory tool exists.
