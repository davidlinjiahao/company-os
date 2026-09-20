# Routing table — which practice skill fires, when, and when not

`/build` owns no engineering practice of its own. It is a dispatcher: it decides which
installed practice skill runs at each phase and, just as importantly, which ones do not.
A phase with nothing to dispatch to is a phase you skip out loud, in the run log.

**Inventory this table is written against:** 16 practice skills, frozen in
`../evals/GOLD.md` §1. If that inventory changes, this table is stale and
`../evals/check_routing.py` will fail on the next run. That is the intended alarm.

---

## Master table

Every installed practice skill appears exactly once. "Skip when" is a condition you can
evaluate without asking the user — if you find yourself needing judgement, the condition is
written wrong and should be fixed here.

| # | Skill to invoke | Phase | Fires when | Skip when |
|---|-----------------|-------|-----------|-----------|
| 1 | `superpowers:using-superpowers` | 0 Orient | Session start, before any other skill, to confirm what is installed | Already invoked once this session |
| 2 | `superpowers:brainstorming` | 1 Frame | The request names an outcome but not a design — "add X", "make it do Y" | The request is a written spec, a ticket with acceptance criteria, or a one-line bugfix with a known root cause |
| 3 | `superpowers:writing-plans` | 2 Plan | Work spans more than ~3 files or more than one session | Single-file change, or a plan already exists on disk |
| 4 | `superpowers:using-git-worktrees` | 3 Isolate | Work will take more than one commit, or the current tree is dirty | Change is under 3 files and you are already on a feature branch |
| 5 | `superpowers:test-driven-development` | 5 Implement | Always — this is the spine | **Never.** No exception, including "too simple to test" and "emergency". The only case with no test is a change with no behaviour: comments, formatting, docs |
| 6 | `superpowers:executing-plans` | 5 Implement | A written plan exists and is being worked in a fresh session | No plan file, or the plan is being written and executed in the same breath |
| 7 | `superpowers:subagent-driven-development` | 5 Implement | The plan has 4+ tasks that are independent and the session is long | Fewer than 4 tasks, or tasks share mutable state |
| 8 | `superpowers:dispatching-parallel-agents` | 5 Implement | 2+ tasks with no shared state and no ordering between them | Tasks are sequential, or the sub-runner surface is unavailable in this runtime — then run them in series and say so |
| 9 | `superpowers:systematic-debugging` | 7 Debug | Any test failure, crash, or behaviour you cannot explain — **before** proposing a fix | Nothing is broken. Not skippable merely because the cause "seems obvious" |
| 10 | `superpowers:verification-before-completion` | 8 Verify | Before any claim that something works, passes, or is done | Never skipped when a claim is being made; skipped only when no claim is being made |
| 11 | `superpowers:requesting-code-review` | 9 Review | A feature is complete, or before merging | Change is a revert, a lockfile bump, or a docs-only edit |
| 12 | `superpowers:receiving-code-review` | 9 Review | Review feedback has arrived and you are about to act on it | No feedback received yet |
| 13 | `superpowers:finishing-a-development-branch` | 10 Land | Tests green, review resolved, branch ready to integrate | Work is unfinished, or the user asked to keep it local |
| 14 | `superpowers:writing-skills` | any | The thing being built *is* a skill, or you are editing a `SKILL.md` | The deliverable is ordinary code |
| 15 | `frontend-design:frontend-design` | 1 Frame + 5 Implement | New or reshaped UI where visual quality matters | No UI, or you are editing inside an established design system |
| 16 | `dataviz` | 5 Implement | About to write **any** chart, plot, dashboard, or stat tile, in any medium | No visualisation in the deliverable |

---

## Supporting skills (workflow infrastructure, not practice guidance)

These are dispatched too, but they are covered by their own acceptance cases rather than by
the coverage count.

| Skill | Phase | Fires when | Skip when |
|-------|-------|-----------|-----------|
| `/eval` | 4 Pre-register + 8 Verify | Always — supplies the `cases.json` format and runs the suite | Never skipped; if the runner is unavailable, hand-run the cases and record it |
| `/loop` | 6 Loop | Acceptance is red and the remaining work is mechanical | Acceptance is already green, or the failure needs a human decision |

## Opportunistic add-ons (local runtime only; each is a no-op when absent)

Each of these is optional. Absence is expected in the sandbox and must never block a phase.

| Add-on | Phase | Fires when | Skip when |
|--------|-------|-----------|-----------|
| `/simplify` | 6 Refine | Diff is large and quality-only cleanup is wanted | Not installed, or the diff is under ~50 lines |
| `/code-review` | 9 Review | You want a second opinion on your own working diff | Not installed — fall back to `requesting-code-review` alone |
| `/security-review` | 9 Review | Diff touches auth, data, or shell surfaces | Not installed — the safety checklist in `safety.md` still runs by hand |
| `/run` | 8 Verify | The change must be seen working in the real app | Headless environment or no app to launch |
| `ralph-loop` commands | 6 Loop | Installed and the task is mechanical enough to iterate unattended | Not installed — use the shell loop driver in `loop-driver.md` instead |

---

## Worked routings

**"Fix a flaky test."**
0 orient → 7 `systematic-debugging` (never skip; flakiness has a cause) → 4 pre-register
acceptance ("100 consecutive runs green") → 5 `test-driven-development` for the repro →
6 loop until the acceptance command is green → 8 `verification-before-completion` →
9 `requesting-code-review`. Skipped: `brainstorming` (no design question),
`writing-plans` (one file), `using-git-worktrees` (small), `frontend-design`, `dataviz`.

**"Build a dashboard page."**
0 → 1 `brainstorming` + `frontend-design` → 2 `writing-plans` → 3 `using-git-worktrees` →
4 pre-register → 5 `test-driven-development` + `dataviz` (before the first line of chart
code) → 6 loop → 8 verify → 9 review → 10 land. Skipped: `systematic-debugging` (nothing
broken yet), `writing-skills`.

**"Rename a config key across the repo."**
0 → 4 pre-register (the acceptance command *is* the grep that must return zero old hits) →
5 `test-driven-development` on the one behaviour that reads the key → 6 loop → 8 verify.
Skipped: `brainstorming`, `writing-plans`, `frontend-design`, `dataviz`,
`subagent-driven-development` (shared state across every file).

**"Write a new skill."**
0 → 1 `brainstorming` → 14 `writing-skills` → 4 pre-register the skill's own eval cases →
5 TDD against those cases → 6 loop → 8 verify → 9 review.

---

## Dispatch rules

1. **Announce the route before running it.** One line: phases you will run, phases you skip,
   why. A silent skip is a skipped skip.
2. **Never inline a practice.** If a skill covers the phase, invoke the skill — do not
   paraphrase its contents from memory. Paraphrase decays; the skill file does not.
3. **A skipped phase still produces a line in the run log.** "Skipped 2 Plan: single file."
4. **When two skills claim a phase, run both** in the order listed. They are complementary
   (`brainstorming` shapes intent, `frontend-design` shapes form).
5. **When you cannot tell whether to skip, do not skip.** The cost of an unnecessary
   `systematic-debugging` pass is minutes. The cost of skipping it is a wrong fix that sets
   the pattern for every fix after it.
