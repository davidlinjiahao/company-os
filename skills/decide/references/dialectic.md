# The dialectic lens

The second of the two lenses the panel runs (`scripts/panel.py`, lens `dialectic`). Where the
game-theory lens asks *"who wants what and which outcome is stable"*, this one asks
*"what is the disagreement actually about, and is there a level at which it stops being a
disagreement?"*

Distilled from the full dialectic method; the long version lives outside this skill. What
survives here is the part that changes decisions.

---

## The four moves

### 1. Thesis
The strongest case **for** acting, argued at full conviction. Not a summary of one side — an
argument by someone who believes it. Hedging here is a failure: a hedged thesis makes the whole
pass useless, because the contradiction never gets sharp enough to be informative.

### 2. Antithesis
The strongest case **against**, also at full conviction. It must attack the thesis' actual
load-bearing assumption, not a caricature of it. If the antithesis is easy to knock down, it was
built wrong — go back and find the version that genuinely worries you.

### 3. Determinate negation
This is the engine, and it is the step people skip.

Not "the thesis is wrong." Rather: **"the thesis is wrong in this specific way, and that
specific failure points at what is missing."** The failure mode is a signpost.

Example. Thesis: *sign the exclusive, we need national distribution.* Antithesis: *never sign,
they own a competing brand.* The thesis fails specifically because it assumes distribution
capacity equals distribution effort. The antithesis fails specifically because it assumes no
version of the deal can align their effort with ours. Both failures point at the same missing
thing: **a term that makes their effort observable and costly to withhold.** That is the signpost.

### 4. Sublation
The resolution that *cancels, preserves and elevates* both sides at once.

A sublation is **not a compromise**. It is not splitting the difference, not "do a bit of each",
and not "it depends". A real sublation produces something neither side could have reached alone, which
both sides — once they hear it — recognise as more complete than what they were arguing.

The test: **does the sublation make the original disagreement look predictable in hindsight?**
If you can now say "of course they disagreed, they were each holding one half of X", you have
one. If all you have is a midpoint, you have a compromise, and the honest thing is to say so.
The panel returns `sublation_is_real: false` in that case rather than dressing it up.

---

## Why this earns its place next to game theory

The two lenses fail in different directions, which is exactly why both run.

- **Game theory** is sharp when there is a counterparty and blunt when the decision is really
  about what kind of company you want to be. It will happily optimise you into an equilibrium
  nobody wanted.
- **Dialectic** is sharp when the team's disagreement is a proxy for an unexamined assumption,
  and blunt when the answer is simply "their BATNA is better than yours, take the deal."

When the two lenses agree, confidence goes up. When they disagree, **that disagreement is the
most valuable output of the whole process** — it usually means the team is arguing about the
wrong question. Read both before writing the recommendation.

---

## Failure modes to watch for in the panel's output

| Symptom | What it means |
|---|---|
| Antithesis is a strawman | The model is agreeing with the owner. Discard the pass. |
| Sublation is "do both" or "start small" | A compromise wearing a costume. Check `sublation_is_real`. |
| Determinate negation restates the antithesis | The step was skipped; there is no signpost. |
| Both sides fail "because of uncertainty" | Not determinate. Every decision has uncertainty. |

---

## What the panel returns from this lens

```json
{
  "thesis": {"claim": "", "strongest_support": ""},
  "antithesis": {"claim": "", "strongest_support": ""},
  "determinate_negation": {"thesis_fails_because": "", "antithesis_fails_because": ""},
  "sublation": "", "sublation_is_real": true,
  "what_it_dissolves": "", "test_that_would_falsify": ""
}
```

Plus the common envelope every lens returns: `recommendation`, `headline`, `confidence`,
`decisive_fact`, `members_used`, `kill_criteria`, `what_would_change_the_answer`.
