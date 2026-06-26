# WHO-Method Scorecard + A-Bar Scoring Prompt

A reusable prompt for designing a hiring scorecard and scoring candidate CVs against it, using Geoff Smart & Randy Street's **"Who: The A Method for Hiring"**. The point of the WHO method is to replace vibes with a written, measurable bar agreed *before* you see candidates, then score every candidate against that same bar.

---

## How to use this file

1. **Design phase** — Fill in the Mission, Outcomes, Competencies, and A-Bar tables below for the specific role. Ground every field in real evidence (the provided JD/brief, optional meeting transcripts, the failures the hire must fix, competitor calibration). If a sibling role page exists in Notion, mirror its exact structure.
2. **Scoring phase** — Paste a candidate's CV/profile into the `[PASTE CV HERE]` slot at the bottom and run this whole file as the prompt. The model returns a per-leg verdict, per-outcome scores, and a single overall verdict.

---

## Scoring rules (read first — these are non-negotiable)

- **Brutally honest. No vibes.** Every score must cite specific evidence from the CV. "Seems strong" is not allowed; quote the line.
- **Evidence or it didn't happen.** If the CV does not show a thing, it is *absent*, not "probably there." Absence is scored as a 1-2, never charitably rounded up.
- **A-player bar = "has shipped this exact thing."** An A-player for an outcome has already personally delivered that outcome, not an adjacent one. Adjacency is explicitly downgraded.
- **A-Bar is a gate, not an average.** A candidate must pass **every** A-Bar leg to be A-grade. Failing one leg = HOLD or REJECT regardless of how strong the rest is. Do not average your way past a missing leg.
- **Name the missing leg.** For any HOLD/REJECT, state exactly which leg(s) failed and what evidence would flip it.
- **Exclude the adjacent-but-not.** A candidate from a wrong-but-nearby specialty, a purely adjacent discipline, tuning-only experience, or a founder (not recruitable) is excluded *with the reason stated*.
- **Distinguish "did" from "was near."** Being on a team that shipped X is not shipping X. Look for first-person ownership signals.

---

## 1. Mission (one paragraph)

> The mission is the role's reason to exist, stated as the core outcome it must produce — derived from the failures it must fix, not a job-description boilerplate.

```
[Write one paragraph: why this role exists, what changes in the business if an A-player holds it for 12-18 months, and the specific pain/failures it must eliminate.]
```

---

## 2. Outcomes (3-8, ranked, measurable, time-bound)

Each outcome must be **measurable**, **time-bound**, and set at the **"A-player has shipped this exact thing"** bar.

| # | Outcome (measurable + time-bound) | A-player bar (the "shipped this exact thing" standard) | Weight |
|---|-----------------------------------|--------------------------------------------------------|--------|
| 1 | [e.g. Ship X to production by month 3, hitting metric Y] | [What proof an A-player would have done this before] | High |
| 2 | [...] | [...] | High |
| 3 | [...] | [...] | Med |
| 4 | [...] | [...] | Med |
| 5 | [...] | [...] | Low |

---

## 3. Competencies

### A. Role-specific / technical

| Competency | What "A" looks like (concrete) | Why it matters (tied to an outcome) |
|------------|--------------------------------|-------------------------------------|
| [e.g. Shipped the relevant system class] | [Has personally built/operated this exact class of system on a shipping product] | [Outcome 1, 2] |
| [...] | [...] | [...] |

### B. Cultural / values

| Value | What "A" looks like (behavioral evidence) |
|-------|-------------------------------------------|
| [e.g. Bias to ship] | [Owns end-to-end delivery; evidence of shipped artifacts, not just specs or designs] |
| [e.g. Truth-seeking] | [Reports failures and metrics honestly; data over narrative] |
| [...] | [...] |

---

## 4. The A-Bar (must-have legs — the phase-4 filter)

The A-Bar is a **small set of must-have legs**. A candidate is A-grade only if **every** leg is met *on first glance* from the CV. Borderline -> HOLD with the missing leg named. Keep this to 2-4 legs; more than that and the bar becomes un-filterable.

> **Template (generic example — replace for the actual role):**
> - **Leg 1:** Has personally shipped a production system of the relevant class on a real product (not simulation, not coursework).
> - **Leg 2:** At least one of a small, role-specific skill set named in the scorecard (the "≥1 of {...}" set).
> - **Leg 3 (optional bullseye):** Location / work-authorization fit (e.g. in-region or can relocate).

**A-Bar for THIS role:**

- **Leg 1:** [must-have]
- **Leg 2:** [must-have, can be an "at least one of {...}" set]
- **Leg 3:** [optional bullseye leg — location/pedigree/authorization]

---

## 5. Verdict scale

Score each Outcome and Competency **1-5** (1 = no evidence / absent, 3 = adjacent, 5 = has shipped this exact thing). Then assign one overall verdict:

| Verdict | Meaning |
|---------|---------|
| **REJECT** | Fails one or more A-Bar legs with no realistic path; do not pursue. State the failed leg. |
| **PHONE SCREEN** | Passes all A-Bar legs but evidence is thin/ambiguous on >=2 outcomes; a 20-min screen resolves it. |
| **FAST-TRACK** | Passes all A-Bar legs and shows direct shipped evidence on the top outcomes; move to onsite quickly. |
| **STRONG YES** | Passes all A-Bar legs, shipped evidence on the top outcomes, plus a clear bullseye (location/pedigree/competitor pool). Top of list. |

**Maps to the sourcing-list vocabulary** (one canonical set across `SKILL.md` / `reference.md` / this file): STRONG YES & FAST-TRACK → **A-GRADE** · PHONE SCREEN → **HOLD** · REJECT → **EXCLUDED**. This WHO-method prompt is the single canonical CV-scoring rubric for the skill.

---

## 6. Required output format

When scoring, return exactly this structure:

```
CANDIDATE: <name> — <current title @ company> — <profile link>

A-BAR:
  Leg 1: PASS/FAIL — <quoted evidence or "absent">
  Leg 2: PASS/FAIL — <quoted evidence or "absent">
  Leg 3: PASS/FAIL/n.a. — <evidence>

OUTCOMES (1-5):
  O1 <name>: <score> — <evidence>
  O2 <name>: <score> — <evidence>
  ...

COMPETENCIES (1-5):
  <competency>: <score> — <evidence>
  ...

EXCLUSION CHECK: <none | adjacent-but-not reason | founder/not-recruitable>

VERDICT: REJECT | PHONE SCREEN | FAST-TRACK | STRONG YES
ONE-LINE WHY: <the single sentence a hiring manager needs>
WHAT WOULD FLIP IT: <for HOLD/REJECT, the exact missing evidence>
```

---

## CV to score

```
[PASTE CV HERE]
```
