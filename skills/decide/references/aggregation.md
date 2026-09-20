# Aggregating the members' answers

Step 3 of the flow. Input: one filled form per member. Output: one decision object that the
panel reads.

The whole job of this step is **to not lose anything.** Aggregation here means collecting and
laying side by side — it does **never average**, never pick a majority answer, and never
rewrite anyone's words.

---

## The rules

1. **Keep every answer verbatim.** Each member's ten answers go into the decision object
   unedited, under their name. Paraphrasing is where dissent quietly disappears.
2. **Never average the leans.** Two GOs and one NO-GO is not "mostly GO". It is a live
   disagreement and it goes into the panel as one.
3. **Find the divergence, principle by principle.** Walk P1 through P10 and mark every
   principle where members materially disagree. Those are the cruxes.
4. **A lone dissenter with domain knowledge outranks a majority without it.** Note who is
   closest to the facts on each principle. The person who owns the system in question is not
   one vote among many on P4 and P7.
5. **Anchoring check.** If everyone's answers echo the owner's, that is not agreement — ask
   the dissenting-most member P6 and P10 again, privately, before running the panel.
6. **Do not resolve anything yet.** The temptation is to settle the disagreement before the
   panel runs. Don't. The panel's job is to reason across the disagreement; a pre-resolved
   input produces a pre-baked answer.

---

## The divergence map

Before running the panel, produce this table. It takes two minutes and it is usually where
the decision is actually made.

| Principle | Agreement | The split |
|---|---|---|
| P1 Timing | — | Alex: deadline is theirs · Jordan: build starts 09-01 |
| P2 Reversibility | — | Alex: 1-way on cap table · Jordan: mostly 2-way |
| P4 Downside cap | ✓ | both: survivable once, not twice |
| ... | | |

Two things to read off it:

- **Principles where everyone agrees** are settled. Do not spend panel tokens or meeting time
  on them.
- **Principles where the split is on *facts*** (P1, P3, P4, P6) are resolvable — go get the
  fact. **Splits on *values*** (P8) are not resolvable by analysis and need the owner to decide.
  Telling these apart is most of the value of the map.

---

## The decision object

```json
{
  "id": "short-slug",
  "decision": "One line with a verb and an object — this becomes the ledger row.",
  "ledger_label": "optional short form if the decision sentence runs past 120 characters",
  "door_type": "1-way",
  "framing": {
    "context": "What triggered this, what is at stake, the numbers that matter.",
    "options": ["Option A", "Option B", "Option C"],
    "deadline": "YYYY-MM-DD",
    "owner": "Name"
  },
  "members": [ /* one filled form per member — see references/principles.md */ ]
}
```

Written to any path; pass it with `--decision-file`. Worked examples:
`evals/fixtures/decisions/*.json`.

**Framing quality is the ceiling on the panel's quality.** The `context` field should contain
the specific numbers and terms — the runway figure, the percentage, the notice period, who owns
what. A vague context produces six confident, generic analyses.

---

## Checking that divergence survived

`scripts/panel.py` computes `member_coverage` in `panel.json`: for each member, which of the six
analyses referenced them by name. The brief renders this as an "Engaged by" column.

If a member shows `0/6`, the brief says so explicitly and the honest move is to re-run — the
panel dropped a stakeholder's input, and a recommendation that ignores a stakeholder is not a
recommendation, it is a summary of the people who agreed.
