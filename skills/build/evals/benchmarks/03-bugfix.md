# Benchmark 03 — bugfix on a seeded defect

**Task type:** debugging an existing repo from a symptom report.
**Fixture:** `fixtures/ledger-app/` — copy it to a scratch dir before starting; do not edit
it in place.
**Runtime:** both local Claude Code and the restricted sandbox (stdlib `unittest` only).

## Brief

Ops filed `fixtures/ledger-app/BUG.md`. The repo's own test suite is green. Find the root
cause, prove it with a failing test, fix it, and show it stays fixed.

There is exactly one seeded defect. It is a one-line fix. The value of this benchmark is not
the fix — it is whether the dispatcher refuses to patch before the root cause is understood.

## Acceptance

1. `systematic-debugging` is routed **before** any edit to `ledger/`. The run must state a
   single hypothesis in the form "I think X because Y" before touching code.
2. `ACCEPTANCE.md` + `evals/cases.json` committed before the fix commit.
3. Loop driver present and executable; `acceptance_check.sh` exits 0 at the end.
4. A new test reproducing the reported symptom exists and is committed **before** the fix,
   with its RED output recorded in `progress.md`.
5. After the fix: the repo's original suite still passes AND the new repro test passes.
6. The held-out verification (`fixtures/.heldout/verify_rolling_max.py`, run by the grader,
   not by the agent) exits 0 against the fixed code.
7. The fix touches one function. A rewrite of `report.py` is a FAIL even if tests pass —
   it means the root cause was never isolated.

## Anti-patterns that fail this benchmark

- Editing code before reproducing the symptom.
- More than one hypothesis in flight at once.
- "Fixing" by widening the test's tolerance or changing the expected value.
- Adding defensive branches around the symptom instead of correcting the boundary.

## Expected artifact set

```
ACCEPTANCE.md
evals/cases.json
loop.sh                 (executable)
acceptance_check.sh     (executable)
progress.md             (hypothesis + RED output + fix + GREEN output)
tests/<repro test>
ledger/report.py        (one function changed)
```

## What is being measured

Whether `systematic-debugging` actually gates the fix, whether the repro test precedes the
fix, and whether the change stays minimal.
