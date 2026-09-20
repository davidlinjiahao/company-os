# Output format

Every decision, 1-way or 2-way, produces exactly two things:

1. a **recommendation brief** (markdown, written next to where you ran the skill), and
2. **one ledger row**.

Nothing else. No hosted database, no shared workspace, no sync step.

---

## The ledger row

Frozen schema — column order does not change:

```
| date | decision | type | recommendation | owner | outcome:pending |
```

Rendered under a standard header:

```markdown
| date | decision | type | recommendation | owner | outcome |
|---|---|---|---|---|---|
| 2026-08-03 | Sign the 3-year exclusive supply agreement with Kestrel | 1-way | MODIFY | Alex | outcome:pending |
```

| Column | Rule |
|---|---|
| `date` | ISO `YYYY-MM-DD`, the day the decision was made |
| `decision` | one line, 3-120 characters, **no pipe characters** |
| | *A framed decision sentence may legitimately run longer. `scripts/panel.py` trims it at the last word boundary that fits; set `"ledger_label"` on the decision object to choose the short form yourself.* |
| `type` | `1-way` or `2-way` — nothing else |
| `recommendation` | `GO`, `NO-GO`, `MODIFY`, `DEFER` — nothing else |
| `owner` | one named human, 1-60 characters |
| `outcome` | literally `outcome:pending` at write time |

Build it with `python3 scripts/ledger.py --date ... --decision "..." --type 1-way
--recommendation MODIFY --owner Alex`. It **refuses to emit an invalid row** rather than
coercing a bad value — an out-of-enum recommendation is an error, not a rounding problem.

`DEFER` is a real answer, not a cop-out — but only when paired with the P6 fact being fetched
and a date. A `DEFER` with no date is a `NO-GO` that nobody wanted to say.

**Grading outcomes later:** edit the row in place, replacing `outcome:pending` with
`outcome:good`, `outcome:bad`, or `outcome:unresolved` and the date. A ledger nobody grades is
a diary. Re-reading the row against the pre-registered kill criteria is the entire point of
writing it down.

---

## The recommendation brief (1-way doors)

`scripts/panel.py` writes this automatically as `brief.md`. Required sections:

```markdown
# Decision brief: [decision]

**Recommendation:** GO | NO-GO | MODIFY | DEFER · **Door type:** 1-way · **Owner:** [name]
**Panel:** N analyses from claude-fable-5, gpt-5.6-sol, grok-4.5 across game_theory, dialectic

## Recommendation
[the vote across the six analyses, each with its one-line headline and confidence]
### The facts each analysis called decisive

## Where the team diverged
[one row per member: name, role, lean, their single decisive reason, and how many of the
six analyses actually engaged with them]

## Game theory
[per model: natural equilibrium, recommended equilibrium, is it reachable, the
players table (position / interest / BATNA / leverage), sequencing]

## Third doors
[positive-sum moves that change the game, clustered across models]

## Dialectic
[per model: thesis, antithesis, why each fails specifically, the sublation and whether
it is a real transformation or only a compromise, what it dissolves, what would falsify it]

## Kill criteria
[the observable signal, with a date, that says this was wrong]

## What would change the answer
[the highest-value unknown and how to resolve it]

## Ledger row
[the single row]
```

Two conventions the brief must keep:

- **When the panel is split, say so at the top.** A contested recommendation presented as
  settled is worse than no recommendation.
- **When a member was engaged by zero analyses, say so at the top of the divergence table.**
  Do not quietly drop them.

---

## The quick brief (2-way doors)

Fast path. No panel, no six analyses. Written by hand or by the orchestrating model in a couple
of minutes:

```markdown
# Decision: [decision]

**Recommendation:** GO | NO-GO | MODIFY · **Door type:** 2-way · **Owner:** [name]
**Confidence:** [X]/10

## Why
[2-4 sentences — the goal, the leading option, the reason]

## What makes this reversible
[the specific thing that makes undoing it cheap, and roughly what undoing costs]

## Kill criteria
[the signal, by a date, that says switch]

## Ledger row
| date | decision | type | recommendation | owner | outcome |
|---|---|---|---|---|---|
| ... |
```

If writing the "what makes this reversible" section is hard, it is not a 2-way door. Go back
to step 1 and reclassify.
