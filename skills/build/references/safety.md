# Safety review, gates, and the no-secrets rule

Carried forward from the previous `/build` unchanged in substance. These are the parts that
have caught real problems, so they survive the rebuild intact.

---

## The five CRITICAL items

Run this pass in Phase 9, on the actual diff, before requesting review.
Any CRITICAL finding blocks the ship until it is resolved — there is no "note and move on" tier.

| # | Item | What you are looking for |
|---|------|--------------------------|
| 1 | **SQL & data safety** | Raw queries built by string concatenation; a migration with no down path; anything that can drop, truncate, or overwrite rows the user did not ask to change; a delete without a `WHERE` you can read aloud |
| 2 | **LLM trust boundary** | Model output flowing into a shell, a query, a template, the filesystem, or a page without escaping. Treat model output exactly like a form field a stranger typed into |
| 3 | **Auth & permissions** | Every new endpoint, route, job, or file handler: who is allowed to call it, and what happens to someone who is not? Missing checks, and checks that return 500 instead of 401/403 |
| 4 | **Secret exposure** | Keys, tokens, or credentials in source, in fixtures, in test data, in logs, in error messages, in commit history |
| 5 | **Injection** | User input reaching a shell, `eval`, a SQL string, a path join, a regex, or a template without sanitisation. Path traversal counts |

For each finding, ask exactly one question and wait: **Fix now / Acknowledge and defer /
False positive?** Batching findings into a wall of text gets them all waved through.

## INFORMATIONAL (warn, do not block)

Hidden side effects in conditional branches · magic numbers with no named constant · dead
code and unused imports · new code paths with no test · catch-all blocks that swallow
errors · frontend: missing error, empty, and loading states · accessibility regressions.

---

## The no-secrets rule

**Never hardcode a secret, token, key, or password — not in source, not in a test fixture,
not in a comment, not "temporarily".** Secrets come from the environment or a config file
that is gitignored, and they are read at the point of use, never at import time.

Concretely:

- A test that needs a credential uses an obviously-fake one (`test-token-not-real`) or
  `os.environ.get(...)` with a skip when unset.
- Nothing is ever printed or logged that came out of an env var whose name contains
  `KEY`, `TOKEN`, `SECRET`, or `PASSWORD`.
- If you find a real credential already committed, stop the build run and say so. Rotating
  it is the user's call; continuing to build on top of it is not.
- Before the ship phase, grep the diff. `git diff --staged | grep -iE '(api[_-]?key|secret|token|password)\s*[:=]'` and read every hit.

---

## Workflow gates

Two gates, both optional infrastructure. When the hook script is present, the gate is
mechanically enforced; when it is absent (the sandbox, a fresh machine, a colleague's
laptop) the *phases still apply* and you enforce them conversationally. The commands are
written so that a missing script is a silent no-op, never an error:

```bash
WORKFLOW_GATE="${WORKFLOW_GATE:-}"

# Gate 1 — opened after the plan and the acceptance artefact are committed
[ -x "$WORKFLOW_GATE" ] && bash "$WORKFLOW_GATE" complete plan

# Gate 2 — opened after the refine pass and the safety review are clean
[ -x "$WORKFLOW_GATE" ] && bash "$WORKFLOW_GATE" complete review
```

Never write these without the leading `[ -x … ] &&` guard. Invoking the gate script
unconditionally gives you a build that works on one machine and dies on every other one.

### TDD enforcement

Where the TDD Guard hook is installed it physically blocks edits to production code without
a currently-failing test. Where it is not installed, the Iron Law is enforced by you: write
the failing test, **show its red output**, then implement. The showing is the point — a
claim that a test was written first is not evidence that it was.

---

## Hard gates before landing

| Check | Threshold | On breach |
|-------|-----------|-----------|
| Acceptance checks | all exit 0 | BLOCK |
| Test suite | 0 failures, fresh run | BLOCK |
| Safety review | 0 unresolved CRITICAL findings | BLOCK |
| Code review score | ≥ 7/10 | BLOCK below 5; proceed with noted warnings 5–6 |
| Prompt-bearing files changed | prompt-injection suite run, 0 HIGH findings | BLOCK |

Prompt-bearing means `skills/*/SKILL.md`, agent definition files, or any file containing a
system prompt. Detect with:

```bash
git diff --name-only main...HEAD | grep -qE 'skills/.+SKILL\.md|agents/.+\.md' \
  && echo "prompt change detected — run the prompt-security suite"
```

If the prompt-security tooling is not installed, skip the run and record the gap explicitly
in the summary. A gap you named is a risk the user can price; a gap you skipped silently is
one they cannot.

---

## Rationalisations that show up right before something breaks

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. The test takes 30 seconds. |
| "I'll test after" | A test written after the code passes immediately, and proves nothing. |
| "Emergency, no time" | Systematic is faster than thrashing. It always has been. |
| "Just try this first" | The first fix sets the pattern for every fix after it. |
| "I see the problem" | Seeing the symptom is not understanding the cause. |
| "Should work now" | Then run it and show the output. |
