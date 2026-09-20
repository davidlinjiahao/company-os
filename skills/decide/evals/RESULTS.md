# RESULTS — `decide` v3

**Run:** 2026-08-03 · `python3 evals/run.py --all --rundir /tmp/decide-final`
**Contract:** `evals/cases.json` + `evals/GOLD.md`, both committed in `45c3e9f`
(`eval: pre-register decide acceptance`) **before** any v3 skill content existed.
No case was edited after pre-registration — `git log -p evals/cases.json evals/GOLD.md` is the proof.

## ACCEPTED

**36 pass / 0 fail / 0 pending.** Every static case passed, every runtime case passed,
and all five judge cases scored 5.0/5 against a 4.0 threshold.

Read the **Known weakness** section below before trusting the recommendation column.

---

## Per-case results

| Case | Tier | Result | Detail |
|---|---|---|---|
| `s01-frontmatter-valid` | static | PASS | valid `name` + `description` frontmatter |
| `s02-progressive-disclosure` | static | PASS | SKILL.md 184 lines (cap 200), all four reference files linked |
| `s03-reference-files-exist` | static | PASS | 5 references + 2 scripts present |
| `s04-five-step-flow` | static | PASS | frame/classify → forms → aggregate → panel → ledger |
| `s05-ten-principles-named` | static | PASS | exactly the ten frozen principles |
| `s06-form-is-askable` | static | PASS | P1..P10 field keys in order, each with `Ask:` + `Answer shape:` |
| `s07-form-closes-with-verdict` | static | PASS | lean / confidence / decisive reason |
| `s08-twoway-fast-path` | static | PASS | 2-way skips the panel, still emits a ledger row |
| `s09-game-theory-preserved` | static | PASS | players, interest, BATNA, leverage, Nash, natural vs reachable, third doors |
| `s10-dialectic-lens-present` | static | PASS | thesis / antithesis / determinate negation / sublation, "not a compromise" |
| `s11-three-models-declared` | static | PASS | three model ids, three key env vars, three API hosts |
| `s12-panel-runs-both-lenses` | static | PASS | both lenses + merge |
| `s13-panel-stdlib-only` | static | PASS | no third-party imports — runs in the restricted sandbox |
| `s14-two-runtimes-guarded` | static | PASS | both runtimes named, optional steps guarded |
| `s15` (id spelled out in `cases.json` only — see note) | static | PASS | zero personal-vault / workspace dependencies across all `.md` and `.py` |
| `s16-no-hosted-sinks` | static | PASS | no hosted decision database |
| `s17-ledger-row-schema-documented` | static | PASS | exact column order documented |
| `s18-brief-sections-specified` | static | PASS | all required brief sections |
| `s19-aggregation-surfaces-divergence` | static | PASS | verbatim, never average |
| `s20-missing-key-degrades` | static | PASS | `skipped_no_key` path present |
| `r01-ledger-row-t1` | runtime | PASS | `\| 2026-08-03 \| Sign the 3-year exclusive supply agreement with Kestrel Optics \| 1-way \| MODIFY \| Alex \| outcome:pending \|` |
| `r02-ledger-row-t2-fastpath` | runtime | PASS | fast-path row from `ledger.py`, no panel involved |
| `r03-ledger-row-t3` | runtime | PASS | schema-valid row for the VP Eng decision |
| `r04-log-proves-three-models-t1` | runtime | PASS | `status:"ok"` logged for all three models |
| `r05-log-proves-three-models-t3` | runtime | PASS | `status:"ok"` logged for all three models |
| `r06-log-proves-both-lenses` | runtime | PASS | all 6 (model, lens) pairs OK |
| `r07-divergent-members-referenced` | runtime | PASS | Alex 6/6, Jordan 6/6, Riley 6/6 |
| `r08-divergence-in-brief` | runtime | PASS | all three named under "Where the team diverged" |
| `r09-panel-refuses-twoway` | runtime | PASS | exits 2 on a 2-way door and points at the fast path |
| `r10-missing-key-degrades-live` | runtime | PASS | with `XAI_API_KEY` unset: 2 OK + 1 `skipped_no_key`, no crash |
| `r11-ledger-rejects-bad-row` | runtime | PASS | `--recommendation MAYBE` rejected, not coerced |
| `j01-historical-exclusive-distribution` | judge | **5.0**/5 | reached NO-GO/counter; named the free-option-plus-house-brand structure as decisive |
| `j02-historical-raise-now-or-wait` | judge | **5.0**/5 | reached "sign the committed $8M now + cut burn"; runway-vs-sales-cycle arithmetic decisive |
| `j03-historical-cofounder-control` | judge | **5.0**/5 | reached the negotiated exit; 3-of-5 board math named as making "win control" unreachable |
| `j04-historical-pivot-funding` | judge | **5.0**/5 | reached the staged wind-down; legacy segment identified as both balance sheet and data pipeline |
| `j05-historical-anchor-customer-nre` | judge | **5.0**/5 | reached sign-after-pinning-milestone-3; did not reflexively refuse a good irreversible deal |

Judge model `gpt-5.6-sol`, mean **5.00/5**, threshold 4.0, no case below threshold.

---

## Known weakness — read this before using the ledger

**Every one of the eight panel runs returned `MODIFY`, unanimously.** H1 (known-good: decline /
counter), H2 (known-good: sign now), H3 (known-good: negotiated exit), H4 (known-good: staged
wind-down), H5 (known-good: sign) and all three test decisions collapsed to the same enum value.

The judge scored these 5/5 because the *substance* was right each time, and because GOLD.md's
pre-registered **adjacent-call rule** explicitly allows a `MODIFY` that is a counter-offer of the
known-good substance. That rule was frozen before the run, so this is not a case being bent after
the fact — but it does mean the eval as pre-registered cannot distinguish "the panel reasoned its
way to a nuanced yes" from "the panel always says MODIFY".

Practical consequence: **the `recommendation` column of the ledger row is currently low-information.
The brief's headline is where the actual call lives.**

Candidate fix, deliberately *not* applied: tighten the enum definition in the lens prompts —
`GO` = do the thing, ordinary conditions attached; `MODIFY` = the substance of the deal must
change; `NO-GO` = do not do it in any form on offer. Applying it now would be post-hoc tuning
against an eval that has already passed, so it needs a fresh pre-registered case
(e.g. "across 5 historical decisions the recommendation enum takes at least 3 distinct values")
before the change is made. Flagged for the operator.

---

## One defect the eval caught, and the fix

`j02` failed on the first judge run — not on judgement, on a crash. The H2 decision sentence is
135 characters and the frozen ledger schema caps the decision column at 120, so `merge()` raised
out of `build_row()` and no brief was produced.

Fixed in the **skill**, not the case: `scripts/panel.py` now derives a ledger label
(`ledger_label()`) by trimming at the last word boundary that fits, and the decision object
accepts an explicit `"ledger_label"` override. `scripts/ledger.py` stays strict — it still refuses
invalid rows rather than coercing them (`r11`). The fixture was not shortened.

## Provenance notes

- The `s15` row above does not spell out that case's full id. The case forbids the two vendor
  names anywhere in the skill's `.md` and `.py` files, and its own id contains both — writing it
  here would fail the check it documents. The case was left exactly as pre-registered rather than
  narrowed to exclude this file; the id is in `cases.json`. It is a small proof that the check
  scans everything it claims to.

- One inert edit (`import threading` moved to module scope) landed while the canonical `--all` run
  was in flight. Both deterministic tiers were re-run afterwards against the final bytes:
  `python3 evals/run.py --static --runtime` → **31 pass / 0 fail** (`/tmp/decide-final2`).
- Keys were read from the local environment. In CI without keys, `--static` (20 cases) still runs
  offline; the 11 runtime and 5 judge cases would report as failures-to-run, not passes.
- Latency for reference: 6 parallel model calls per decision, ~90-130s wall clock per panel run.

VERDICT: ACCEPTED

---

## Addendum 2026-08-06 — vault retrieval step

Step 1 gained "Pull prior context from the team vault" (`../vault/scripts/fetch_transcripts.sh`,
credential `team-vault`, cite-by-filename, never-fabricate rule). The frozen case set and
scoring semantics above are untouched. The retrieval behavior itself is covered by the
vault-mirror pre-registered acceptance (`.build/vault-mirror/`, committed before implementation):
happy-path sha-verified mirror, live retrieval by query, and the honest missing-credential path
were all verified against the real bucket on 2026-08-06. `--static` re-run against the edited
SKILL.md: 20 pass / 0 fail (`evals/results/run-20260806-163517`). Runtime/judge tiers were not
re-run — no script or fixture changed.

VERDICT: ACCEPTED — static re-verified 2026-08-06 after vault step; feature acceptance in .build/vault-mirror/
