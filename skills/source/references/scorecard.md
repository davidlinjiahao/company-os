# Scorecard reference (WHO method)

Read this during **Phase 2**. Source: Geoff Smart & Randy Street, *Who: The A Method for Hiring*. The one idea worth keeping: **write the bar down before you meet anyone, then score everyone against that same written bar.** Everything else is bookkeeping in service of that.

An A-player is not "a great engineer". An A-player is someone with a ≥90% chance of hitting *these specific outcomes* in *this specific situation*. The same person can be an A for one role and a C for another. That is why the scorecard comes first.

---

## 1. Mission — one paragraph

Why this role exists, stated as the failures it eliminates and what is true in 12–18 months if an A-player holds it.

Bad: *"Own the backend and help the team scale."*
Good: *"Own the entire software surface between the device and the customer, so the company can put a working product in a stranger's hands and keep it working without a platform team. In 12 months, software is no longer what blocks a hardware iteration."*

If you cannot name what breaks today, you are not ready to source. Go back and ask.

## 2. Outcomes — 3 to 8, ranked

Each one **measurable**, **time-bound**, and set at the *"an A-player has already personally shipped this exact thing"* bar.

| # | Outcome (measurable + time-bound) | A-player bar (what proof looks like) | Weight |
|---|---|---|---|
| 1 | Ship X to production by month 4, hitting metric Y | Has personally shipped a comparable X and owned metric Y | High |

Test each row: could two people who have never met agree whether it happened? If not, rewrite it.

Common failure: writing outcomes that describe *activity* ("improve code quality") rather than *results* ("cut p95 latency to 300ms by month 8"). Activity outcomes cannot be scored, so they quietly disappear from the filter.

## 3. Competencies

**A. Technical / role-specific** — for each: what "A" looks like, concretely, and which outcome it serves. A competency that serves no outcome is decoration; cut it.

**B. Cultural** — how this person has to operate here specifically. "Ships without a spec", "talks to customers directly", "comfortable being the only person who knows a subsystem". These are real filters, not values-poster words, and you should be able to name the evidence that would show them.

## 4. A-BAR legs — the filter

This is the part the whole skill runs on. **3–6 legs. Each decidable from evidence a stranger can open.**

Format each leg as: `L<n> <requirement> — evidence = <what proves it>`.

Two legs are mandatory in every role:
- **Geography / work authorization.** Skipping it produces beautiful lists of people who cannot take the job.
- **≥2 distinct public evidence URLs, all resolving.** This is what stops the list from drifting into plausible-sounding fiction.

**Decidable vs not:**

| Not decidable | Decidable |
|---|---|
| Strong systems engineer | Has run a production backend they personally designed, with real users — named system + public artefact |
| Startup mindset | Founder, founding/first-5 engineer, employee at a sub-20-person company, or solo maintainer of a ≥200-star OSS project |
| Familiar with hardware | Has written software that talks to a physical device over BLE, USB/serial, MQTT, or firmware OTA — named project |

**Calibrate the legs against reality once.** Before sweeping, check the legs against 3 people you would obviously hire and 3 you would obviously not. If an obvious yes fails a leg, the leg is wrong. If an obvious no passes every leg, the legs are too loose. Fix them *now* — after the sweep, editing the bar to fit results is exactly the failure mode the method exists to prevent.

## 5. Exclusions — write them down

The adjacent-but-not profiles that will flood a keyword sweep. Naming them in advance is what makes the excluded section fast and defensible later. Typical: pure researchers with nothing shipped; a neighbouring discipline (mechanical when you need software); agencies and contract shops with no owned product; founders currently fundraising (not recruitable); anyone whose only evidence sits behind a login.

## 6. Scoring a specific person

For each leg: **PASS** (explicit evidence, quote it) · **UNSUPPORTED** (the profile does not say — this is the default) · **FAIL** (contradicted).

- **A** = every leg PASS.
- **HOLD** = exactly one leg UNSUPPORTED, and it is plausible. Name the leg and what would settle it.
- **REJECT** = anything else.

Absence of evidence is never charitably rounded up. A prestigious employer is not evidence of a leg. "Was on the team that shipped X" is not "shipped X" — look for first-person ownership.

---

## Where the scorecard goes

Local: a shared doc if the user wants one (a Notion page, a vault note). Sandbox or no preference: a markdown file next to the candidate list.

If you are writing to Notion via MCP: create the page with headings and prose only, then add each table as a **native table block** — markdown tables get flattened into literal `| ... |` paragraphs and `**bold**` survives as visible asterisks. Add tables after the section heading, delete the flattened text paragraphs, and re-fetch the block children to confirm the true state before deleting anything (the append response echoes sibling IDs and will mislead you).
