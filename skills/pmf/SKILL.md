---
name: pmf
description: The product/market-fit loop. Use when preparing customer-discovery interviews, when a call transcript needs turning into evidence, or when validating a problem, persona, price or positioning. `/pmf questions` builds a past-behaviour question bank grounded in a named persona and falsifiable hypotheses; `/pmf log` extracts quote-backed insights from transcripts, excludes compliment-zone material, updates a running hypothesis scoreboard, and emits the next interview's sharpened questions.
user-invocable: true
disable-model-invocation: false
argument-hint: "questions <persona or hypothesis> | log <transcript path or url> [more…] | board"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, AskUserQuestion
---

# PMF

One loop, run over and over until the surprises stop:

```
questions ─▶ interview ─▶ log ─▶ scoreboard ─▶ sharper questions ─▶ …
```

Grounded in *The Mom Test* (Fitzpatrick), *The Lean Startup* (Ries — the hypothesis
scoreboard), and Jason Cohen's asmartbear essays (problem selection, willingness-to-pay,
iterative-hypothesis customer development). Distilled in `references/`.

## Commands

```
/pmf questions <persona or hypothesis>     Build the bank for the next interview
/pmf log <transcript…>                     Transcripts → insights + scoreboard + next questions
/pmf board                                 Print the current scoreboard, nothing else
```

## Runtimes

This skill must work in two places. Nothing below requires an MCP server.

| Capability | Local Claude Code | restricted sandbox |
|---|---|---|
| Read a transcript from a path | Read | Read |
| Fetch a public transcript URL | WebFetch | `curl` |
| Pull a recording from a recorder MCP | **optional** — use it if `mcp__plaud__*` is present | not available — ask for a file or a URL, then continue |
| Write `INSIGHTS.md` / `SCOREBOARD.md` | Write, into the project or vault | Write, into the working directory |
| Push to Notion / Obsidian | **optional** — only if those MCP tools exist | skip silently; the local files are the source of truth |

Rule: if an optional tool is unavailable, say so in one line and carry on with files. Never
stall, and never invent a transcript you could not read.

## `/pmf questions <persona or hypothesis>`

1. **Lock one persona.** A who-where pair — a specific person *and* where you can find them.
   If the segment is broad, slice it (`references/frameworks.md` → Customer slicing) and state
   the locked persona in 3 lines. Ask at most one `AskUserQuestion` if the slice genuinely
   changes the questions; otherwise pick, say so, and offer to regenerate.
2. **Write 5–10 falsifiable hypotheses**, one or more per thing you need to learn — written as
   predictions you could lose (`references/frameworks.md` → Iterative-hypothesis method). If an
   unexpected answer would not change the plan, cut the hypothesis.
3. **Generate the bank** — 35–50 questions across the categories in
   `references/question-banks.md`, every one laddering up to a hypothesis. Reuse the
   domain banks there when the persona matches; otherwise instantiate the category skeleton.
4. **Run the form filter** before emitting. Every question must be past-behaviour
   (`references/ground-rules.md` → The form filter). A hypothetical is allowed only as a setup
   immediately pinned to a real instance in the same breath.
5. **Emit**: persona block · hypotheses · questions grouped by category · a screener ·
   the commitment ask you will make · a 5-line field card (deflect compliments, anchor fluff,
   capture numbers, do not pitch, talk less than they do).

Self-check: `python3 scripts/pmf_lint.py questions <file>` — it counts unanchored
hypotheticals and refuses a bank over 20%.

## `/pmf log <transcript…>`

1. **Read every transcript in full** before writing anything. Large ones: read in chunks; do
   not skim. Note speaker labels — diarizers split one person across several labels.
2. **Find the contamination boundary.** Locate the moment the interviewer first describes,
   demos or prices the product. Everything after it is compliment-zone. Record the timestamp.
   Also note structural bias: who the interviewee is to you (advisor, friend, investor,
   someone who wants in) changes the weight of everything they said.
3. **Extract candidate insights**, each with a verbatim quote + speaker + timestamp. Before filtering, list every moment where the interviewee's voice changes — frustration, resignation, shame, delight — and check each one for an insight; emotional peaks are where the strongest signals hide.
4. **Apply the four-part insight filter** (`references/ground-rules.md`). An insight survives
   only if it passes all four:
   - **Quote** — a verbatim line from the transcript, not a paraphrase.
   - **Clean zone** — that quote predates the contamination boundary.
   - **Decision** — you can name the build / price / positioning / targeting decision it changes.
   - **Surprise** — a competent founder would not have predicted it before the call.
   Anything that fails *Decision* or *Surprise* is a summary. Delete it; do not demote it.
5. **Capture the numbers** — $/month, hours/day, requests/week, months-until-abandoned, ages,
   counts. Money already spent outranks every stated price.
6. **Update the files** (`references/output-formats.md` for exact schemas):
   - `INSIGHTS.md` — append new insight records, merge duplicates, raise confidence when a
     second household repeats something, and mark contradictions rather than averaging them.
   - `SCOREBOARD.md` — every hypothesis gets exactly one of `VALIDATED` / `REFUTED` / `OPEN`,
     with the insight ids that moved it and the next test that would settle it.
   - A `Contaminated — not evidence` section listing the post-pitch quotes you discarded and
     why. Compliment-zone quotes appear **only** there.
7. **Emit the next interview's questions** — 8–15, each aimed at an `OPEN` or contradicted
   hypothesis, or at the biggest gap in the numbers. Say explicitly what changed since the
   last bank and who you now need to interview that you have not.

Self-check: `python3 scripts/pmf_lint.py insights <file> --transcript <path…>` — it verifies
every quote exists verbatim in a source transcript and that no compliment-zone quote is used
as evidence.

## Quality bar

Good and bad, on the same call:

- Summary (delete): *"The shop tried a tablet and the techs stopped using it."*
- Insight (keep): *"The tablet had zero value to the techs inside two weeks — `\"we tried a
  tablet last winter and the techs stopped opening it after two weeks\"` [02:10]. So this is
  an owner tool in a technician costume: retention is coerced, and every retention number
  from this segment is fake until a tech asks to open it."*

The difference is the last sentence. If you cannot write it, you do not have an insight.

## Stop and fix

- An insight with no verbatim quote, or with a quote you cannot find in the transcript.
- Any price, "I'd buy that", or enthusiasm from after the pitch treated as evidence.
- A scoreboard where nothing is `REFUTED` — you are confirming, not testing.
- A question bank with no question you are afraid to ask.
- Insights that are all one household's opinion, presented as a market.
- No sampling note when the sample is skewed (all one gender, one income band, one city).
- The next-questions section missing, or identical to the last one — the loop did not turn.

## References

| File | Load when |
|---|---|
| `references/ground-rules.md` | Always. Form filter, inbound filter, insight filter, the pitch rule. |
| `references/question-banks.md` | Building a bank. Category skeleton + two worked domain banks. |
| `references/frameworks.md` | Slicing a persona, writing hypotheses, judging a problem, pricing. |
| `references/output-formats.md` | Writing `INSIGHTS.md` / `SCOREBOARD.md` / the post-call scorecard. |

Acceptance criteria and gold answers for this skill live in `evals/GOLD.md`.

## Usage tracking (company convention)

Optionally record one memory fact: `used pmf for <5-word purpose>`. Skip if no memory tool exists.
