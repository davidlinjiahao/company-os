# GOLD — pre-registered acceptance for `decide` v3

Frozen **2026-08-03, before any v3 skill content was written.** Nothing in this file may be
loosened to make a case pass. If a case is wrong, the honest move is to record the FAIL in
`RESULTS.md` and fix the skill — or, if the case itself is genuinely mis-specified, to say so
explicitly in `RESULTS.md` and leave the case failing until the operator rules on it.

Runner: `python3 evals/run.py --all` (also `--static`, `--runtime`, `--judge`).
Keys are read from the environment; `evals/run.py` will additionally source `~/.claude/.env`
if it exists and the variables are not already set.

---

## 1. What is being accepted

The v3 flow, per the spec:

1. Frame the decision + classify **1-way** vs **2-way** door.
2. **Every team member** answers the same 10 decision principles (one crisp question each,
   askable by a Slack agent).
3. Aggregate all members' answers into one matrix that preserves divergence.
4. Run **both** lenses — game theory **and** Hegelian dialectic — across **three** frontier
   models: `claude-fable-5` (Anthropic), `gpt-5.6-sol` (OpenAI), `grok-4.5` (xAI). Merge.
5. Output = **recommendation brief** + **one ledger row**.

2-way doors take the fast path: no panel, quick recommendation, still a ledger row.

---

## 2. Gold: the ten principles (frozen)

The form must be exactly these ten, in this order, with these field keys. Adding an eleventh
principle, renaming a key, or dropping one is a FAIL of `s05` / `s06`.

| # | Key | Principle |
|---|-----|-----------|
| P1 | `P1_timing` | Timing — does this have to be decided now? |
| P2 | `P2_reversibility` | Reversibility — 1-way or 2-way, and what exactly is irreversible? |
| P3 | `P3_expected_value` | Expected value — best / base / worst with rough probabilities |
| P4 | `P4_downside_cap` | Downside cap — maximum loss, and can we survive it? |
| P5 | `P5_opportunity_cost` | Opportunity cost — what we give up; next-best use of the same resource |
| P6 | `P6_information` | Information needed — the one fact that would most change the answer |
| P7 | `P7_second_order` | Second-order effects — what this makes easier or impossible later |
| P8 | `P8_strategy_fit` | Strategy alignment — does this move the mission, or is it fear/opportunism? |
| P9 | `P9_owner` | Who decides — single owner, plus who must ratify |
| P10 | `P10_kill_criteria` | Kill criteria — the observable signal, by a date, that says we were wrong |

Plus a closing **verdict block** on every member form: `lean` (GO / NO-GO / MODIFY / DEFER),
`confidence` (1-10), `decisive_reason` (one sentence).

## 3. Gold: the ledger row (frozen)

Exactly one row per decision, exactly these columns in this order:

```
| date | decision | type | recommendation | owner | outcome:pending |
```

Acceptance regex (also stored as `ledger_row_regex` in `cases.json`; `@ledger_row_regex` in a
case's `expected.regex` resolves to it):

```
^\| \d{4}-\d{2}-\d{2} \| [^|]{3,120} \| (1-way|2-way) \| (GO|NO-GO|MODIFY|DEFER) \| [^|]{1,60} \| outcome:pending \|$
```

- `date` — ISO `YYYY-MM-DD`.
- `decision` — one line, no pipe characters, 3-120 chars.
- `type` — `1-way` or `2-way` only.
- `recommendation` — `GO`, `NO-GO`, `MODIFY`, `DEFER` only. Anything else must be **rejected**,
  not coerced (case `r11`).
- `owner` — a single named human.
- `outcome` — literally `outcome:pending` at write time. Outcomes are graded later, by hand.

## 4. Gold: proof that all three models ran

`panel.py` writes `panel-log.jsonl`, one JSON object per model call:

```json
{"ts": "...", "run_id": "...", "model": "grok-4.5", "provider": "xai", "lens": "game_theory",
 "status": "ok", "http_status": 200, "latency_ms": 12345,
 "prompt_tokens": 0, "completion_tokens": 0, "attempt": 1, "error": null}
```

- `r04` / `r05` PASS only if the log contains a `status:"ok"` line for **each** of
  `claude-fable-5`, `gpt-5.6-sol`, `grok-4.5`.
- `r06` PASS only if all **six** (model, lens) pairs have a `status:"ok"` line.
- A missing key must produce `status:"skipped_no_key"` — never a crash (`s20`, `r10`).

## 5. Gold: divergence must survive aggregation

Fixture `t3-vp-eng-offer.json` is deliberately three-way split:

| Member | Role | Lean | The position that must survive into the output |
|--------|------|------|-----------------------------------------------|
| Alex | CEO | MODIFY | Will not trade governance (board observer seat / 4.0% of a 6.2% pool) for a hire |
| Jordan | Head of Ops | GO | The bottleneck is that nobody runs engineering full time; two quarters of schedule beats dilution |
| Riley | Principal Engineer | NO-GO | Sole roadmap authority puts the calibration pipeline — the customer program — at risk |

`r07` PASS only if `panel.json.member_coverage` shows **every one of the three** referenced by at
least one model. `r08` PASS only if `brief.md` names all three under a
`Where the team diverged` heading. Averaging the three into a single "team view" is a FAIL.

## 6. Gold: the five historical decisions

Synthetic but structurally faithful fact patterns; each fixture carries a frozen `known_good`
block (`recommendation_class`, `decisive_fact`, `what_actually_happened`, `why_it_was_right`).
The `known_good` block is **stripped before the panel sees the fixture** and is shown **only to
the judge**.

| Case | Fixture | Known-good call | Decisive fact the brief must find |
|------|---------|-----------------|-----------------------------------|
| J1 | h1-exclusive-distribution | NO-GO / counter to non-exclusive or exclusivity + minimum purchase + performance termination | Harrow owns a competing house brand and has committed to nothing; exclusivity is a free option for them |
| J2 | h2-raise-now-or-wait | GO — sign the committed flat $8M now | 6.0 months runway vs a 5-month minimum sales cycle not yet started, in a market compressing 40% |
| J3 | h3-cofounder-control | Negotiated exit (third door) with carve-outs | Board math is 3-of-5 against with the fifth seat needing that same majority; "win control" is unreachable |
| J4 | h4-pivot-funding | MODIFY — staged wind-down, keep the two design-partner accounts | The legacy segment is both the balance sheet ($3.4M of next-12-month cash vs $900k on hand) and the training-data pipeline |
| J5 | h5-anchor-customer-nre | GO — sign after pinning milestone-three acceptance criteria | IP retained, licence non-exclusive, exclusivity field-limited to a vertical with no roadmap; $2.4M non-dilutive |

J5 exists specifically to catch a framework that has learned to be reflexively cautious. A brief
that recommends declining or heavily counter-offering on J5 should score low.

### Judge rubric {#judge-rubric}

Judge model: **`gpt-5.6-sol`**. Temperature 0 (or provider default if unsupported). The judge is
given: the decision fixture without `known_good`, the frozen `known_good` block, and the produced
brief. It returns strict JSON `{"score": <1-5>, "reasoning": "..."}`.

| Score | Meaning |
|-------|---------|
| 5 | Reaches the known-good call **and** names the decisive fact as decisive; states kill criteria / what would change the answer; uses the members' actual inputs; honest about uncertainty |
| 4 | Reaches the known-good call and identifies the decisive fact, with minor gaps (e.g. weak kill criteria, thin use of member inputs) |
| 3 | Plausible reasoning but either misses the decisive fact, or lands on a materially different call without engaging the known-good option |
| 2 | Wrong call, reasoning does not engage the decisive structural fact |
| 1 | Wrong call plus confident errors or facts not present in the fixture |

**PASS threshold: score >= 4.0 on every judge case.** The suite reports the mean, but the mean is
not the gate — one case at 3 is a FAIL for that case.

Adjacent-call rule (frozen so it cannot be argued after the fact): a brief that recommends
`MODIFY` where the known-good is a counter-offer of that same substance counts as reaching the
known-good call. A brief that recommends `DEFER` where the known-good is a decision counts as
**not** reaching it.

## 7. Overall acceptance

`RESULTS.md` may say **ACCEPTED** only if:

- every `static` case passes,
- every `runtime` case passes,
- every `judge` case scores >= 4.0,
- and no case was edited after this file was committed (git history is the proof).

Any case that could not be run is recorded as **PENDING** with the reason. A run containing any
PENDING case is not ACCEPTED — it is `ACCEPTED-PARTIAL` at best, and the file must say so.
