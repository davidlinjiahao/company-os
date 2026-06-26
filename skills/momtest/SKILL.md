---
name: momtest
description: Use when preparing customer-discovery / user interviews, validating a problem or product idea, or talking to a target customer / ICP — generates a large, structured bank of Mom Test–style interview questions (bias-free, past-tense, grounded in a specific persona) instead of leading, hypothetical, "would you buy this" questions.
user-invocable: true
disable-model-invocation: false
argument-hint: "[product / topic / problem you want to validate]"
allowed-tools: AskUserQuestion, Read, Write, WebFetch
---

# Mom Test Questions

## Overview

Generate a large, organized bank of customer-interview questions for a product's ICP that pass **The Mom Test** (Rob Fitzpatrick) — questions even a biased, polite person can't lie to you about. The output is not a flat list: it is a persona-locked, category-by-category kit. **It's a reservoir, not a script** — the Mom Test default is a *casual* chat: pull 1–3 questions in naturally, never read the list aloud, and if it ever feels like they're doing you a favor by talking, it's too formal.

**The Mom Test — three rules every generated question must obey:**
1. Talk about **their life**, not your idea.
2. Ask about **specifics in the past**, not generics or opinions about the future.
3. (For the interviewer) talk less, listen more — so questions are short and open.

**Core principle:** *They own the problem; you own the solution.* You never ask people what to build or whether your idea is good — only the market knows that (the *one* exception: an industry expert who has built a very similar business — their opinion can carry weight). You extract concrete facts about their life and decide for yourself.

## When to Use

- Founder/PM is about to do customer discovery, user research, or "talk to users."
- Validating a problem, a new feature, a positioning, or a whole idea.
- Anyone says "what should I ask customers?" / "interview questions" / "discovery script."
- Preparing for a sales-as-learning call, expert call, or partner conversation.

**Not for:** survey design with rating scales (Mom Test is conversational), or pitch decks.

## The Iron Filter — Forbidden Question Shapes

Before emitting ANY question, run it through this filter. If a question matches a forbidden shape, rewrite it to its past-tense, life-based equivalent or delete it. **A leading question is worse than no question** — it manufactures a false positive, and a false positive is worse than no data because it gets you to over-invest cash, time, and team. (The danger is *treating a leading answer as data* — a deliberate topic-nudge that you immediately anchor to a specific past instance is fine; see the magic-wand row.)

| ❌ Forbidden shape | Why it lies | ✅ Rewrite to |
|---|---|---|
| "Do you think it's a good idea?" | Opinion. Only the market knows. | "How do you handle this today? Show me." |
| "Would you buy / use a product that…?" | Future hypothetical → always "yes". | "What have you already tried to solve this?" |
| "How much would you pay for…?" | Number feels rigorous but is fiction. | "How much does this problem cost you now? What do you pay to deal with it?" |
| "Would you pay $X for Y?" | Adding a number doesn't fix the future-tense lie. | "Walk me through the last thing you bought to fix this." |
| "If you could wave a magic wand / dream product?" | Collects fantasy feature requests. | Only OK as a *setup* — must immediately follow with "why would that help? how do you cope without it now?" |
| "Do you ever / would you ever / could you see yourself…?" | Fluff-inducing — invites "sure, someday." | "When did that last happen? Talk me through it." |
| "What do you usually / always / never do?" | Generic self-image, not real behavior. | "What did you do the last time it came up?" |

**Low-value-unless-anchored vocabulary:** *would, could, ever, usually, typically, generally, imagine, if you had, on a scale of 1–5.* These aren't banned outright — a generic opener ("what do you usually do?") or a gentle nudge to reach a topic is fine **only if the very next question pins it to a specific past instance** ("…and when did that last happen? walk me through it"). Standing alone and unanchored, they're fluff — fix them.

## Reading the Answers — the inbound filter

The Iron Filter screens what you *ask*; this screens what you *hear*. Three kinds of bad data, each with its recovery move:
- **Compliments** → deflect. Own the slip and pivot to the present: *"Whoops — I got excited and started pitching. Can I ask how you're handling this today?"*
- **Fluff** (generics, futures, hypotheticals — especially the volunteered *"I'd totally buy that"*) → anchor to the last real instance: *"When did that last come up? Walk me through it."*
- **Feature requests / ideas** → understood, not obeyed: dig for the motivation behind them rather than logging them: *"What would that let you do?"*

Debrief trip-wire: if afterward you catch yourself saying *"that went great / lots of positive feedback / everybody loves it"* but can't name **why** they liked it, **what** it would save them, and **what** they've already tried — you collected a compliment, not data. There's more reliable signal in a flat *"meh"* than an excited *"wow."*

## Process

### Step 1 — Lock the ICP (the persona "Carol")

Mom Test questions are different for every segment. A vague segment ("students", "advertisers", "sales orgs") yields 20 conversations with 20 different people and mixed signals. So **first narrow to one specific, findable persona** before generating anything.

Read [reference.md](reference.md) → "Customer Slicing" and "Building Carol (the ICP)". Then:

1. From the topic, take a best-guess segment and **slice it to a who-where pair** — a specific person + where you can physically find them (per the slicing questions in reference.md). A segment with no "where" is useless.
2. State the locked persona back to the user in 2–4 lines: who they are (role/title/company-type), the problem in *their* words ("the way she'd complain about it to a friend over lunch"), why they'd want this *now*, and where to find them.
3. If the segment is genuinely ambiguous and changes the questions materially, ask **one** `AskUserQuestion` offering 2–4 candidate slices (e.g. "solo freelancer vs. 5-person studio vs. agency"). Otherwise pick the best guess, say so, and offer to regenerate for another slice at the end. Don't stall — generate.
4. **Classify the dominant risk.** If the idea is a marketplace, network-effect play, ad/affiliate model, game, or hard-tech build, it's **product-risk-dominant** — flag to the user that interviews can validate the market questions but *not* whether you can build/grow it, and that "if you can build it, I'd pay" is burden-shifting, not validation (see reference.md → "Product risk vs market risk").

### Step 2 — Set the 3 Big Questions

Derive the **3 scariest things** to learn from THIS persona by running two thought experiments on the idea:
- **Pre-mortem:** assume it's dead in 18 months — what are the 2–3 likeliest causes?
- **Pre-parade:** assume it's a huge success — what had to be true to get there?

The scariest item from each becomes a Big Question. **Importance test:** for each one ask *"if the answer comes back unexpected, does it change or kill the plan?"* If not, it's a comfortable question — cut it and find the one you're afraid to ask. A bank that can't falsify the idea is worthless however clean its questions; you should be a little scared of at least one question you're walking in with. Every question in Step 3 must ladder up to one of these. Example Big Questions: "Is this even a top-3 problem for them? / What do they already spend to cope? / Who actually controls the budget?"

### Step 3 — Generate the bank, by category

Instantiate **every** category below to the specific persona and topic. Generate generously — aim for **5–10 questions per category, 40+ total** ("a ton"). Every question must survive the Iron Filter. Categories, in interview order:

> **Open broad unless the problem is a known must-solve for this persona.** Category 1 ("talk me through the last time you…") presupposes they already do the task and care about it — asking it cold manufactures false positives (the classic "biggest problem with the gym?" asked of someone who never goes). If problem-status is unproven, open with *"What are your big goals/focuses right now?"* or *"What are the top problems in [their domain]?"* and only zoom into your problem area once **they** raise it unprompted. If they never raise it, that *is* your signal — note it and move on.

1. **Context & current workflow** ("show, don't tell") — *"Talk me through the last time you [did the task]." / "Walk me through your whole workflow for X — what tools, what people, what happens at each step?" / "Where in that process does it usually break?"* (then anchor "usually" to a specific instance).
2. **Problem reality & frequency** — *"When did this last happen?" / "How often does it come up?" / "What triggered it that time?"*
3. **Implications & stakes** (separates pay-to-solve from mildly-annoying) — *"What were the consequences when that happened?" / "What did it cost you — time, money, stress, reputation?" / "What happens if it doesn't get fixed?"*
4. **Existing alternatives & the search test** — *"What else have you tried?" / "How are you dealing with it right now?" / "What do you love and hate about that?" / "How much does that solution cost you?" / "Have you searched for something better? What did you find?"* (If they never even Googled it, they don't care enough — that's gold.)
5. **Money & budget source** (essential for B2B) — *"How much are you spending on this today, across tools and people?" / "Where would the budget for a fix come from?" / "Whose budget is it?" / "Who else would need to approve — or could kill — a purchase?"*
6. **Motivation — the "why" behind it** — *"Why do you bother doing it that way?" / "What are you ultimately trying to get done?"* (gets from the perceived problem to the real one).
7. **Digging into feature requests** (understood, not obeyed) — *"What would that let you do?" / "How are you coping without it now?" / "Walk me through how you'd use it."*
8. **Digging into emotional signals** (any strong emotion → dig) — *"Tell me more about that." / "That seems to really bug you — what makes it so awful?" / "Why haven't you been able to fix this already?"*
9. **Commitment & advancement tests** (replace "would you buy?" with a real ask for something they value — time, reputation, or money) — *"Can I buy the prototype / put down a deposit?" / "Can we set up a follow-up next week to go deeper?" / "Could you intro me to two others on your team who hit this?" / "Would you be willing to trial it with your real data?"* (A real "yes" costs them something; a compliment costs nothing.) **Define your own next funnel rung *before* the interview** — alpha access, paid trial, intro to the budget-holder — so you can name it on the spot: *commitment* = they give up time/reputation/money; *advancement* = they take that next step. If you don't know what happens next, the meeting was pointless. And pin down soft promises: *"Who specifically did you have in mind — could you intro me this week?"*
10. **The close — referral & gaps** — *"Who else should I talk to?" / "Is there anything I should have asked but didn't?"* End every interview here.

### Step 4 — Output

Emit the bank as markdown:
- A short **Persona** block (the locked Carol + where to find her).
- The **3 Big Questions**.
- Questions grouped under the 10 category headers above.
- A 4-line **Field reminders** footer: deflect compliments, anchor fluff to a past instance, dig beneath every signal, and *talk less than they do.*

Offer to: (a) regenerate for a different persona slice, (b) produce a "find people to interview" plan + first marketing channel (see reference.md), or (c) tighten to a 3-question casual version for serendipitous run-ins.

## Quality Bar — a good vs. bad bank

❌ **Bad** (what a generic list produces): "Would you use an app that tracks invoices? How much would you pay? What's your dream invoicing tool?" → all future/hypothetical/opinion. Zero learning.

✅ **Good** (persona = *solo freelance designer who already invoices via PayPal and chases late payers by hand*): "Talk me through the last invoice that went unpaid — what did you do, day by day? / What did that late payment actually cost you? / What are you using to track who owes you right now, and what do you hate about it? / Have you ever paid for a tool to fix this — which, and did it stick? / Could I check back in two weeks to see how the next late one plays out?"

## Red Flags — STOP and rewrite

- A question uses *would / could / ever / usually / imagine / dream / scale of 1–5* **and is left unanchored** — no immediate follow-up pinning it to a specific past instance.
- None of the questions scare you — no answer could change or kill the idea (the bank is unfalsifiable).
- The bank zooms straight into your problem without first checking it's even a top-3 problem for them (premature zoom = false positives).
- You're asking whether the **idea** is good, or pitching inside a question.
- The bank is one flat list, not persona-locked and category-grouped.
- The persona is a broad segment with no "where to find them."
- No commitment/advancement asks and no "who else should I talk to?" — the two most-skipped, highest-value categories.

## Source grounding

Question mechanics, customer-slicing, note symbols, and commitment currencies from *The Mom Test* (Rob Fitzpatrick); the Carol/bullseye ICP, the 6-conditions problem test, and the first-marketing-channel framework from Jason Cohen (asmartbear.com) — distilled in [reference.md](reference.md).
