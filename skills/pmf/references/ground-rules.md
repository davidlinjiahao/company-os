# Ground rules

*The Mom Test* (Rob Fitzpatrick). Worked examples below are from the **synthetic**
auto-shop fixtures in `../evals/fixtures/`. Do not paste real customer calls into this
public template.

---

## The three rules

1. Talk about **their life**, not your idea.
2. Ask about **specifics in the past**, not generics or opinions about the future.
3. **Talk less.** If you spoke more than a third of the time, you ran a pitch, not an interview.

*They own the problem; you own the solution.* You never ask people what to build or whether the
idea is good — only the market knows. You extract facts about their life and decide yourself.

---

## The pitch rule (the expensive one)

**Do not describe, demo or price the product until the discovery is finished.** The moment they
know what you are building, every subsequent answer is a compliment.

Observed: Call A ran clean until `[18:00]`, then the interviewer described the product.
Everything after is worthless as evidence — the owner produced `"two hundred a month would be
a magic number"`, `"okay, sign me up"`, `"a hundred percent"`, all invented on the spot for a
tablet they had never used. None of it is willingness-to-pay data.

A second owner said it to the interviewer's face:

> *"This was like a validation call."*

If you must show something, do it **after** the discovery block, and mark the timestamp. In the
write-up, everything after that timestamp goes in a `Contaminated — not evidence` section.

**Structural contamination too.** An interviewee who wants to join the project, invest, or sell
you something is not a neutral witness. Weight their enthusiasm at zero and their *facts* at
face value.

---

## The form filter — what you are allowed to ask

Run every question through this before it leaves your mouth.

| Forbidden shape | Why it lies | Rewrite to |
|---|---|---|
| "Do you think it's a good idea?" | Opinion. Only the market knows. | "How do you handle this today? Show me." |
| "Would you buy / use a product that…?" | Future hypothetical → always yes. | "What have you already tried to solve this?" |
| "How much would you pay for…?" | Feels rigorous, is fiction. | "What did you pay for the last thing you bought to fix this?" |
| "Would you pay $X for Y?" | A number does not fix a future-tense lie. | "Walk me through that purchase — who raised it, who vetoed it?" |
| "If you could wave a magic wand…?" | Collects fantasy features. | Only as a setup — follow instantly with "why that? how do you cope now?" |
| "Do you ever / could you see yourself…?" | Invites "sure, someday." | "When did that last happen? Talk me through it." |
| "What do you usually / always do?" | Self-image, not behaviour. | "What did you do the last time it came up?" |

**Low-value vocabulary:** *would, could, ever, usually, typically, generally, imagine, if you
had, on a scale of 1–5.* Not banned — but each one must be pinned to a specific past instance in
the very next breath, or it is fluff.

**Observed:** hypothetical questions produced philosophy. Past-behaviour questions produced
gold (*"when did you last text the jobber?"*, *"how many parts texts last week?"*).

**The magic probe.** After any habit they describe, ask: **"What is the feeling that drives that
action?"** On Call A this converted an assumed "anti-theft board" into lunch logistics:

> *"I look at the board at lunch. Not because a car is stolen. Because I need to know who is waiting."*

---

## The inbound filter — what you are allowed to believe

Three kinds of bad data, each with its recovery move.

- **Compliments** → deflect and pivot to the present. *"Whoops, I got excited and started
  pitching. Can I ask how you handle this today?"*
- **Fluff** — generics, futures, hypotheticals, especially the volunteered "I'd totally buy
  that" → anchor. *"When did that last come up? Walk me through it."*
- **Feature requests / ideas** → understood, not obeyed. Dig for the motive: *"What would that
  let you do?"* Then ask how they cope without it today.

**Money already spent is the strongest signal there is.** What they pay for now beats anything
they say they would pay. The synthetic corpus has the same trap on purpose: every price
captured is hypothetical, none is a receipt.

**Debrief trip-wire.** If afterwards you say *"that went great, lots of positive feedback"* but
cannot name **why** they liked it, **what** it would save them, and **what** they have already
tried — you collected a compliment. A flat *"meh"* carries more signal than an excited *"wow"*.

---

## The four-part insight filter

An extracted insight ships only if it passes all four. Fail any one and it is deleted, not
demoted.

1. **Quote.** A verbatim line from the transcript, with speaker and timestamp. Paraphrase is not
   evidence.
2. **Clean zone.** That quote predates the contamination boundary (and the speaker is not
   structurally conflicted).
3. **Decision.** You can name the build / price / positioning / targeting decision it changes.
4. **Surprise.** A competent founder would not have predicted it before the call. *"Shops
   want software"* is not an insight. *"The objection is a stale catalog, not the screen"* is.

Rule of thumb: an insight that only restates what the interviewee said is a **summary**. An
insight names what you must now do differently, or which assumption just died.

---

## Capture the numbers

Every call must leave with countables, because prose cannot be compared across interviews:

- $ per month on the category, and **what they already pay for**
- hours per day / week on the behaviour
- events per week (requests, incidents, arguments, checks)
- months until the last comparable purchase was abandoned, and what killed it
- ages, counts, household composition
- the last $100+ purchase in the category, and how the decision actually happened

Worked example from Call A — one question yielded a whole funnel:
*"Three or four parts texts a week. I ignore half."* That is a measurable owner workload;
"shops want better parts ordering" is not.

---

## Commitment, not compliments

The only real currencies at the end of a call are their **time** (a follow-up), their
**reputation** (an intro), or their **money** (a deposit, a pre-order). Decide your next funnel
rung *before* the call so you can name it on the spot. "Sounds cool" and "keep me posted" are
worth nothing.

Close every interview with: *"Who else should I talk to?"* and *"What should I have asked but
didn't?"*

---

## Sampling

Write down who you have **not** talked to. Three calls with the same kind of person is one call
with error bars. The synthetic corpus is skewed on purpose: three independent-shop owners, one
of whom wants to join the project. Missing: dealers, multi-location groups, night-shift shops,
and the counter person who actually texts the jobber.

Saturation test: keep interviewing until the surprises stop. For a tight segment that can be
3–5 conversations. If you are past ~10 and the answers are still contradictory, the persona is
too fuzzy — go back and slice.
