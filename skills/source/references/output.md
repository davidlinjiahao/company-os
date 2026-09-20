# Output reference

Read during **Phase 7**.

## The deliverable

`<Role>_Candidates.md` in the working directory (also copy to `~/Desktop` when it exists). One file, five sections, in this order.

```markdown
# <Role> — candidate list, <date>

**Bar:** <the A-bar legs, verbatim>
**Swept:** <lanes> · **Blocked:** <lanes> · **Found:** <n> A-grade, <n> hold, <n> excluded

## Top picks
1. **<Name>** — <one line: the single strongest reason> · <route-in>
...

## A-grade

### 1. <Name> — <current role, company, location>
| Leg | Verdict | Evidence |
|---|---|---|
| L1 <short name> | PASS | "<quote>" — [<source>](<url>) |
| L2 ... | PASS | ... |

**Route in:** <warm path, or cold with a suggested opening>
**Watch for:** <the honest reservation — every real candidate has one>

## Hold
### <Name> — missing **L3**
<what is known, what would settle the leg, how to find out>

## Excluded (by reason)
- **Adjacent, not the thing** (7): <names> — <one line each>
- **Not recruitable** (3): ...

## Source depletion
<tracker from references/agents.md, including NEEDS YOU>
```

Why this shape: the leg table makes the filter auditable. Anyone can check your work by clicking. The **Watch for** line prevents the list from reading as a sales pitch — a list where every candidate is flawless is a list nobody trusts.

## Ranking

Rank on: number of legs passed with *first-person ownership* evidence → bullseye geography → warmth of the route in → recency of the matching work. Do **not** rank on employer prestige; it is the loudest signal in the data and one of the weakest predictors of the outcomes you wrote down.

## Verify before handing over

```bash
python3 scripts/verify_links.py --input <Role>_Candidates.md
```

Exit 0 required. Anything else means a citation is dead, bot-walled, or wrong — fix the citation or drop the claim. A 403 counts as a failure on purpose: if the user cannot open it, it is not evidence. LinkedIn URLs will usually fail this; cite the person's own site, repo, talk, or post instead and keep the LinkedIn link only as a contact route.

## Optional: blind cross-family grade

```bash
python3 scripts/judge_list.py --list <Role>_Candidates.md --scorecard <scorecard.md> --runs 3
```

Sends the legs and the entries — nothing else — to a model from a different family, which returns a per-leg verdict for every candidate. Useful as a self-check before delivery: if a different model cannot find the evidence you claim is there, the reader will not find it either.

It reports; it does not decide. Thresholds live in the eval, not in the script.

## Optional: clickable PDF

```bash
bash scripts/make_pdf.sh <Role>_Candidates.md
```

pandoc + weasyprint, A4 landscape, dense, with a link-annotation check that proves the URLs are real clickable annotations rather than blue text. Exits 3 if the tools are absent — that is fine, the markdown is the deliverable.

## When the answer is "not enough A-players"

Say it plainly, in the first three lines, with the count. Then name the levers, in order of expected value:

1. **Blocked lanes** — a credential or an intro that unlocks a real pool.
2. **Geography** — what widening it would add, numerically if you can.
3. **Split the role** — if no single person plausibly clears every leg, the scorecard may describe two people. Say so; this is a common and expensive mistake to leave undiagnosed.
4. **Lower a specific leg** — name *which* leg and what it costs. This is the user's decision to make explicitly, never yours to make quietly by relaxing the filter.

A short honest list plus a clear lever beats a padded list every time. The padded list looks better for one meeting and wastes weeks of interview time afterwards.
