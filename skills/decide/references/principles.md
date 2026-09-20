# The ten decision principles — the member form

One form. Ten questions. Every person with a stake answers all ten, independently, before
anyone argues. The point is not consensus — it is to get each person's real model of the
decision on the record *before* the loudest voice anchors everyone.

Ask them one at a time. Each answer is 1-3 sentences. If someone cannot answer a question,
"I don't know" is a valid and useful answer — write it down, it usually points at P6.

**Ask everyone the same ten questions in the same order.** Do not tailor them per person;
the value comes from comparing like with like.

---

## The form

### P1 — Timing
**Field:** `P1_timing`
**Ask:** "Does this have to be decided now? What is the real deadline, whose deadline is it,
and what actually breaks if we wait 30 days?"
**Answer shape:** a date + the cost of waiting, in money or in a specific thing that fails.
*Most stated deadlines belong to the other side. Say whose it is.*

### P2 — Reversibility
**Field:** `P2_reversibility`
**Ask:** "Is this a 1-way door or a 2-way door — and what exactly is the part that cannot be
undone?"
**Answer shape:** `1-way` or `2-way` + the specific irreversible component (money, a signature,
a relationship, a person, a cap table).
*Almost every decision has both. Name the irreversible part precisely, not the whole decision.*

### P3 — Expected value
**Field:** `P3_expected_value`
**Ask:** "Best realistic case, base case, worst case — with rough probabilities?"
**Answer shape:** three outcomes with rough percentages. Rough is fine; false precision is not.

### P4 — Downside cap
**Field:** `P4_downside_cap`
**Ask:** "What is the maximum we can lose here, and can we survive it?"
**Answer shape:** the worst-case loss in money / time / reputation + survivable yes or no.
*Expected value is meaningless if the downside ends the company. P4 overrides P3.*

### P5 — Opportunity cost
**Field:** `P5_opportunity_cost`
**Ask:** "What do we give up by doing this? What is the next-best use of the same money,
time, or people?"
**Answer shape:** the specific forgone alternative, not "focus".

### P6 — Information needed
**Field:** `P6_information`
**Ask:** "What is the one fact we don't have that would most change the answer — and what
would it cost to get it before the deadline?"
**Answer shape:** the crux fact + how long and how much to resolve it.
*If it is cheap and fast, the decision is usually "go get it" and nothing else.*

### P7 — Second-order effects
**Field:** `P7_second_order`
**Ask:** "After the obvious first effect — what happens next, to the team, the market, and our
future options? What does this make easy or impossible a year from now?"
**Answer shape:** 2-3 downstream consequences.

### P8 — Strategy alignment
**Field:** `P8_strategy_fit`
**Ask:** "Does this move us toward what we're actually building — or are we doing it out of
fear, flattery, or because it showed up?"
**Answer shape:** fits / doesn't + one sentence of why.

### P9 — Who decides
**Field:** `P9_owner`
**Ask:** "Who owns this decision — one name — and who has to ratify it?"
**Answer shape:** one owner + any required approvals.
*One name. "The team decides" means nobody decides.*

### P10 — Kill criteria
**Field:** `P10_kill_criteria`
**Ask:** "What observable signal, by what date, would tell us we were wrong — and what do we
do when we see it?"
**Answer shape:** a metric or event + a date + the action.
*Written before the decision, this is a plan. Written after, it is an excuse.*

---

## Closing verdict block

After the ten, every member gives:

- **lean** — `GO` / `NO-GO` / `MODIFY` / `DEFER`
- **confidence** — 1-10
- **decisive reason** — one sentence. Not a list. The single thing that, if it were false,
  would flip their lean.

---

## Collected shape

The Slack agent (or you) collects one object per member:

```json
{
  "name": "Riley",
  "role": "Principal Engineer",
  "lean": "NO-GO",
  "confidence": 9,
  "decisive_reason": "Sole roadmap authority puts the calibration pipeline at risk.",
  "answers": {
    "P1_timing": "...", "P2_reversibility": "...", "P3_expected_value": "...",
    "P4_downside_cap": "...", "P5_opportunity_cost": "...", "P6_information": "...",
    "P7_second_order": "...", "P8_strategy_fit": "...", "P9_owner": "...",
    "P10_kill_criteria": "..."
  }
}
```

Field keys are frozen — `scripts/panel.py` and the evals both depend on them.
Worked examples: `evals/fixtures/decisions/*.json`.

---

## Asking this in Slack

The agent posts one question per message and waits. Ten short messages beat one long form —
people answer short questions and abandon long ones.

Suggested cadence:
1. Post P1-P3 as three messages, wait for all three answers.
2. Post P4-P7.
3. Post P8-P10 plus the verdict block.

If a member's answer is a single word, ask once for the specific thing (a date, a number, a
name) and then move on. Do not interrogate. A thin honest answer is better than a padded one,
and thin answers are themselves signal about who has actually thought about this.

If somebody's answers are all identical in shape to the owner's, that is anchoring, not
agreement — ask them P6 and P10 again, alone.
