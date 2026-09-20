---
name: decide
description: Use when making a real decision with a team — "should we sign/hire/acquire/invest", "should I leave or stay", any go/no-go with stakeholders. Frames the decision and classifies it as a 1-way or 2-way door; every team member answers the same ten decision principles; the answers are aggregated with their disagreements intact; 1-way doors then get a three-model panel (claude-fable-5, gpt-5.6-sol, grok-4.5) running both a game-theory analysis and a Hegelian dialectic pass. Output is one recommendation brief and one ledger row.
user-invocable: true
disable-model-invocation: false
argument-hint: "[decision question]"
allowed-tools: AskUserQuestion, Read, Write, Glob, Grep, Bash
---

# decide

Five steps. Two paths.

```
1. FRAME + CLASSIFY  →  2-way door ──────────────→ fast path: quick rec + ledger row
        │
        └─────────────  1-way door
                            │
        2. EACH MEMBER answers the ten principles
                            │
        3. AGGREGATE — divergence kept intact
                            │
        4. PANEL — 3 models × 2 lenses (game theory + dialectic)
                            │
        5. OUTPUT — recommendation brief + one ledger row
```

---

## Step 1 — Frame and classify

Write the decision as **one sentence with a verb and an object**. "Sign the 3-year exclusive
supply agreement with Kestrel", not "the Kestrel situation". If you cannot write that sentence,
you do not yet have a decision — you have a topic.

Then ask the owner (`AskUserQuestion`) whether it is a **1-way door** (irreversible, or so
expensive to undo that you would not) or a **2-way door** (you can change course in weeks for a
knowable cost). **Ask — do not guess from keywords.** A framework choice can be a 1-way door if
it takes the whole team a year to learn; a hire can be a 2-way door in a country with a
probation period.

If the owner says "not sure": ask what specifically cannot be undone and what undoing it would
cost. That question resolves it almost every time.

**Also settle the owner now.** One name. If nobody owns it, stop and fix that first — the rest
of this process produces a recommendation with nowhere to land.

**Pull prior context if a team vault exists.** Before classifying, search local `decisions/`
notes and any transcript folder the operator points at. If a fetch helper is on `PATH`
or next to this skill, use it. If it is missing, write `vault: not accessible from this
scope` in the brief and continue — **never fabricate vault context.**

### 2-way doors: the fast path

Reversible decisions do not earn a panel. **Skip the panel entirely.** Have the owner alone
answer P1, P2, P5 and P10 (timing, reversibility, opportunity cost, kill criteria), write a
quick brief, emit the **ledger row**, and move. The cost of a wrong 2-way decision is one
migration; the cost of deliberating is a month.

Quick-brief template: `references/output-format.md`.

```bash
python3 scripts/ledger.py --date 2026-08-03 \
  --decision "Pick an observability vendor for the inference service" \
  --type 2-way --recommendation GO --owner Jordan
```

Everything below applies to 1-way doors only.

---

## Step 2 — Every member answers the ten principles

Ten questions, same ten for everyone, answered **independently before anyone argues**.

| | Principle | Field |
|---|---|---|
| P1 | Timing — does this have to be decided now? | `P1_timing` |
| P2 | Reversibility — what exactly cannot be undone? | `P2_reversibility` |
| P3 | Expected value — best / base / worst, roughly | `P3_expected_value` |
| P4 | Downside cap — max loss, and can we survive it? | `P4_downside_cap` |
| P5 | Opportunity cost — what we give up | `P5_opportunity_cost` |
| P6 | Information needed — the one fact that would change it | `P6_information` |
| P7 | Second-order effects — what this makes easy or impossible later | `P7_second_order` |
| P8 | Strategy alignment — mission, or fear and opportunism? | `P8_strategy_fit` |
| P9 | Who decides — one owner, plus who ratifies | `P9_owner` |
| P10 | Kill criteria — the signal, by a date, that says we were wrong | `P10_kill_criteria` |

Then a closing verdict: **lean** (GO / NO-GO / MODIFY / DEFER), **confidence** 1-10, and a
**single decisive reason** in one sentence.

Exact wording for each question, the answer shape it expects, and the Slack cadence for asking
them: **`references/principles.md`**.

---

## Step 3 — Aggregate

Collect the forms into one decision object. The rule is: **lose nothing.** Keep every answer
verbatim, never average the leans, and build the divergence map — the list of principles where
members materially disagree. That map is usually where the decision actually is.

Splits on facts (P1, P3, P4, P6) are resolvable — go get the fact. Splits on values (P8) are
not, and need the owner.

Decision-object schema and the divergence-map method: **`references/aggregation.md`**.

---

## Step 4 — The panel

Six analyses: three frontier models, each running both lenses.

| Model | Provider | Key |
|---|---|---|
| `claude-fable-5` | Anthropic | `ANTHROPIC_API_KEY` |
| `gpt-5.6-sol` | OpenAI | `OPENAI_API_KEY` |
| `grok-4.5` | xAI | `XAI_API_KEY` |

| Lens | Asks | Detail |
|---|---|---|
| Game theory | Who wants what, what is each player's next-best option, which outcome is stable, and is there a third door? | **`references/game-theory.md`** |
| Dialectic | What is the disagreement actually about, and is there a level at which it stops being one? | **`references/dialectic.md`** |

```bash
python3 scripts/panel.py --decision-file decision.json --out decisions/kestrel/
```

Writes `panel-log.jsonl` (one line per model call — the proof all three ran), `panel.json`
(merged analysis + member coverage + the ledger row) and `brief.md`.

Read the merged output, don't just forward it:

- **Where the two lenses disagree is the most valuable output.** It usually means the team is
  arguing about the wrong question.
- **Check `member_coverage`.** A member engaged by 0 of 6 analyses was dropped; re-run.
- **Check `sublation_is_real`.** A `false` means the dialectic found only a compromise.
- **Check `reachable`.** An equilibrium the owner cannot reach is a wish, not a plan.

Missing keys degrade gracefully — the run logs `skipped_no_key` for that provider and continues
on the others. A brief built on fewer than three models must say so.

---

## Step 5 — Output

Two artifacts, both local to where you ran this. Nothing is written to any hosted or shared
system.

1. **The recommendation brief** — `brief.md`, written by the panel. Sections and conventions:
   **`references/output-format.md`**.
2. **One ledger row**, appended to your decisions ledger file:

```
| date | decision | type | recommendation | owner | outcome:pending |
```

Grade the outcome later by editing the row in place. A ledger nobody grades is a diary.

---

## Runtimes

This skill runs in two places and must behave the same in both.

- **Local Claude Code** — full tooling. Extra context gathering (searching the working directory
  for prior memos and specs with Glob/Grep, or pulling meeting notes if a transcript tool
  happens to be connected) is **optional**: use it if present, **skip** it silently if not.
- **restricted sandbox** — no MCP servers at all. Shell, files, curl, and env-var API keys only.
  `scripts/panel.py` and `scripts/ledger.py` are pure `python3` standard library over `urllib`
  precisely so they run unchanged here.

Every optional step is guarded. Never fail a decision because a data source is down — note the
gap in the brief and continue.

---

## Evals

`evals/cases.json` + `evals/GOLD.md` are the pre-registered acceptance contract: the frozen ten
principles, the ledger-row regex, the proof-of-three-models rule, the divergence-survives rule,
and five historical decisions with known-good outcomes judged by `gpt-5.6-sol` at 4.0/5.

```bash
python3 evals/run.py --static     # offline, no keys needed
python3 evals/run.py --all        # adds live panel runs + judged historical cases
```

Latest run: `evals/RESULTS.md`.

## Usage tracking (company convention)

Optionally record one memory fact: `used decide for <5-word purpose>`. Skip if no memory tool exists.
