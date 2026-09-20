# Phase 4 — pre-register acceptance

The rule this whole file exists to enforce:

> **You do not know what you are building until you can name the command that proves it.**

Writing the proof after the code is not a proof. By then the target has moved to wherever
the code happens to have landed. So the acceptance artefact is written, committed, and
shown to the user **before** the first line of implementation, every run, no exceptions.

This mirrors the eval methodology used everywhere else in this repo: freeze the gold, then
run the experiment. Never the reverse.

---

## What gets written

`scripts/build_init.sh <slug>` scaffolds all four files. Run it, then fill them in.

```
.build/<slug>/
  ACCEPTANCE.md        the contract: what "done" means, in runnable commands
  evals/cases.json     the cases, in the /eval skill's format
  acceptance_check.sh  runs every command in ACCEPTANCE.md, exits 0 only if all pass
  loop.sh              re-runs acceptance_check.sh until green (see loop-driver.md)
  progress.md          one block per iteration; the run's memory
```

Commit these as **one commit, before any implementation commit**, with a message starting
`eval: pre-register <slug> acceptance`. The git history is the evidence that the order was
respected; `git log --diff-filter=A --format=%h%x09%s -- .build/<slug>/ACCEPTANCE.md`
should show a hash strictly older than the first source commit.

---

## ACCEPTANCE.md format

````markdown
# ACCEPTANCE — <slug>

## Done means
<3-8 bullets. Observable outcomes, not activities. "Returns 403 for a token without
exports:write" is an outcome. "Auth is handled" is an activity.>

## Out of scope
<What this run will NOT do. Prevents scope drift mid-loop.>

## Checks
Every line in the block below is run by acceptance_check.sh. All must exit 0.

```checks
python3 -m unittest discover -s tests -q
python3 -c "import json,subprocess;json.loads(subprocess.check_output(['./dupefind','--json','.']))"
! grep -rn "OLD_CONFIG_KEY" src/
```

## Known-unrunnable
<Checks you cannot automate, with the manual steps and who signs them off. Being explicit
here is the only honest alternative to automating them.>
````

Rules for the `checks` block:

- **Every line must be able to fail.** A check that cannot fail is decoration. Before you
  trust the block, break the code on purpose once and watch it go red.
- Commands run from the project root with `set -o pipefail`. Prefix with `!` to assert
  a command fails.
- No check may depend on network access, a secret, or a service you did not start. Those
  belong under Known-unrunnable.
- Keep it under ~10 lines. If you need more, the run is too big — split it.

---

## evals/cases.json format

Use the `/eval` skill's schema — same file layout, same expectation vocabulary, so the
existing runner can read it. Minimum viable case:

```json
{
  "component": "<slug>",
  "type": "skill",
  "version": "1.0",
  "cases": [
    {
      "id": "returns-403-without-scope",
      "category": "safety",
      "description": "A valid token lacking exports:write is refused, not crashed on",
      "input": {"command": "curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer $READONLY' localhost:8080/v1/exports"},
      "expected": {"contains": ["403"], "must_not_contain": ["500"]},
      "metrics": ["TaskCompletion", "ErrorHandling"]
    }
  ]
}
```

Expectation vocabulary — deterministic first, judge only when nothing deterministic will do:

| Kind | Keys | Use for |
|------|------|---------|
| Deterministic | `contains`, `must_not_contain`, `contains_sections`, `min_length`, `no_error`, `status` | Anything with a right answer |
| Tool-level | `required_tools`, `forbidden_tools`, `tool_args` | Proving *how* a result was reached |
| LLM judge | any other key, plus `rubric` + `min_score` | Quality, tone, design — things with no string to grep |

Judge cases need a rubric written **now**, with the numeric threshold stated now. A rubric
invented after seeing the output is a rationalisation.

---

## Coverage bar

The cases must cover, at minimum:

1. The happy path.
2. Every error path named in the brief (each status code, each rejection reason).
3. One boundary per numeric or size parameter.
4. One case for the thing most likely to break silently — the failure that would ship
   unnoticed. If you cannot name it, you have not understood the change yet.

## Amending acceptance mid-run

Allowed, but never quietly. If the acceptance turns out to be wrong:

1. Stop the loop.
2. Say what is wrong with it and why the original was mistaken.
3. Amend `ACCEPTANCE.md` in its own commit, message prefixed `eval: amend acceptance —`.
4. Restart the loop.

Never edit an expected value to match what the code produced. That is the single most
common way a build run silently becomes worthless.
