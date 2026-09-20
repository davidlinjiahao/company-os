# Phases 8–10 — verify, review, land

---

## Phase 8 — verify

> **NO COMPLETION CLAIM WITHOUT FRESH EVIDENCE.**

The gate function, every time you are about to say something works:

1. **Identify** — what single command would prove this claim false if it were false?
2. **Run** — the full command, fresh. Not a subset, not a cached result, not "it passed
   earlier".
3. **Read** — the whole output. Exit code. Failure count. Not just the last line.
4. **Verify** — does that output actually support the claim, or only fail to contradict it?
5. **Then** claim it, with the output pasted.

| Claim | What proves it | What does not |
|-------|----------------|---------------|
| "Tests pass" | Fresh run, 0 failures, exit 0 | A run from before the last edit |
| "Build succeeds" | Build exit 0 | Linter passing |
| "Bug is fixed" | The original symptom, retested | The code changed |
| "Acceptance is met" | `acceptance_check.sh` exit 0 | Individual checks passing at different times |
| "It works in the app" | Seen running, or a manual checklist someone walked | Unit tests |

Run `superpowers:verification-before-completion` here. It exists precisely because this is
the step everyone's confidence talks them out of.

### Eval pass

Run the pre-registered `evals/cases.json`. Report per-case PASS / FAIL / PENDING. A case
that could not run is PENDING, never a pass. If the diff touched auth, data handling, or a
shell surface, run the security-focused eval pass too — and if that tooling is not
available, say so rather than omitting the line.

### QA pass (only when there is a UI)

If the change is visible and something can drive a browser, exercise the affected routes,
check the console for errors, and capture what you saw. If nothing can drive a browser —
the usual case in the sandbox — emit a numbered manual checklist a human can walk in two
minutes, and mark QA as unverified.

---

## Phase 9 — refine and review

### Refine, in order

1. **Question** — does each new file, function, and abstraction need to exist? Search for
   something already in the codebase that does the job. Used once? Inline it.
2. **Eliminate** — dead code, unused imports, speculative error handling, comments that
   restate the line below them, "just in case" abstractions.
3. **Simplify** — reduce nesting, name things after what they are, split unrelated concerns,
   replace clever with obvious.
4. **Accelerate** — the obvious performance faults only: N+1 queries, work inside loops that
   belongs outside, redundant passes over the same data.
5. **Automate** — fill the test gaps the new code paths opened, then run the safety review
   in `safety.md`.

Steps 1 and 2 usually delete more than steps 3–5 add. If a refine pass produced no
deletions, it was not a refine pass.

### Review

Run `superpowers:requesting-code-review`. When feedback arrives, run
`superpowers:receiving-code-review` **before** implementing any of it — feedback that is
technically wrong should be argued with, not silently obeyed, and feedback that is right
deserves to be understood before it is applied.

Do not defend the code. Do not perform agreement either. For each point: is it correct?
Verify, then act.

---

## Phase 10 — land

Run `superpowers:finishing-a-development-branch`. It owns the decision about how the work
integrates; do not improvise around it.

Pre-flight, all of which must already be true:

- Acceptance green, on a fresh run.
- Full test suite green, on a fresh run.
- Zero unresolved CRITICAL safety findings.
- Nothing uncommitted.
- Every deferred item written down where it will be seen again, not just mentioned.

Then: sync with the base branch, **re-run the tests after the merge** (this is where
integration bugs actually appear, not before), and push.

Stop and ask only for: merge conflicts, post-merge test failures, unresolved critical
findings, or anything the user said they wanted to see first.

---

## The summary

The user reads this instead of the diff. Write it for someone who will not open a file.

```
## Build complete: <name>

### What it does
<2-3 sentences, no jargon. If a term is unavoidable, define it in the same breath.>

### How it works
<One concrete analogy. "It keeps a numbered ticket for each export request, so asking
twice in a minute hands back the same ticket instead of starting a second job.">

### Evidence
| Check | Result | Note |
|-------|--------|------|
| Acceptance | PASS | 7/7 checks, fresh run |
| Tests | PASS | 34 tests, 0 failures |
| Safety review | PASS | 5 CRITICAL items reviewed, 0 findings |
| Code review | 8/10 | 2 informational, both addressed |
| Evals | 9 PASS / 1 PENDING | judge case pending, no key available |
| QA | UNVERIFIED | no browser in this runtime; checklist below |

### Try it yourself
1. <step>
2. <step>
3. <what you should see>

### What I did not verify
<Every gap, named. This section being empty is a claim in itself — only leave it empty
when it is true.>

### Deferred
<Anything punted, and where it is written down.>
```

Two rules for the summary: **no adjective that is not backed by a row in the evidence
table**, and **the gaps section is written before the good news**, so it does not get
quietly trimmed for length.
