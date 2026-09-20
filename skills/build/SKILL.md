---
name: build
description: End-to-end pipeline to build anything with code — a dispatcher that routes each phase to the right installed practice skill, pre-registers acceptance criteria before implementation, and loops until they are green. Use for any feature, bugfix, refactor, tool, or project.
user-invocable: true
argument-hint: "[what you want built]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill
---

# /build — the dispatcher

**Announce at start:** "Using /build. Route: <phases I will run>. Skipping: <phases and why>."

`/build` owns no engineering practice of its own. Every practice already exists as an
installed skill, maintained by someone who thought harder about that one thing than a
combined document ever could. `/build`'s job is to decide **which skill fires at which
phase, and which ones do not** — and to enforce two things nothing else enforces:

1. **`ACCEPTANCE.md` is written and committed before any code exists.**
2. **A loop driver re-runs that acceptance until it is green.**

Everything else is delegation.

---

## The routing table

Full version with fire/skip conditions for all 16 installed practice skills, plus worked
routings: `references/routing.md`. Read it the first time you run in a session.

| Phase | Skill to invoke | Skip when |
|-------|-----------------|-----------|
| 0 Orient | `superpowers:using-superpowers` | Already oriented this session |
| 1 Frame | `superpowers:brainstorming` (+ `frontend-design:frontend-design` if UI) | The request is already a spec, a ticket with acceptance criteria, or a one-line fix with a known cause |
| 2 Plan | `superpowers:writing-plans` | Under ~3 files, or a plan file already exists |
| 3 Isolate | `superpowers:using-git-worktrees` | Under 3 files and already on a feature branch |
| 4 Pre-register | `/eval` format + `scripts/build_init.sh` | **Never** |
| 5 Implement | `superpowers:test-driven-development` (spine) + `executing-plans` / `subagent-driven-development` / `dispatching-parallel-agents` / `dataviz` / `writing-skills` as the work demands | TDD: **never**. The others: see `references/routing.md` |
| 6 Loop | `/loop` or the shell driver in `references/loop-driver.md` | Acceptance already green, or the blocker needs a human decision |
| 7 Debug | `superpowers:systematic-debugging` | Nothing is broken. Not skippable because the cause "seems obvious" |
| 8 Verify | `superpowers:verification-before-completion` | **Never**, whenever a claim is being made |
| 9 Review | `superpowers:requesting-code-review` then `superpowers:receiving-code-review` | Revert, lockfile bump, or docs-only change |
| 10 Land | `superpowers:finishing-a-development-branch` | Work unfinished, or the user asked to keep it local |

Three dispatch rules:

- **Announce skips out loud.** A silent skip is a skipped skip.
- **Never paraphrase a skill from memory.** Invoke it. Memory decays; the file does not.
- **When unsure whether to skip, don't.** An unnecessary debugging pass costs minutes. A
  skipped one costs a wrong fix that sets the pattern for every fix after it.

---

## Phase 4 — pre-register acceptance (the part that is non-negotiable)

> You do not know what you are building until you can name the command that proves it.

Before the first line of implementation, every run:

```bash
bash skills/build/scripts/build_init.sh <slug>
```

That scaffolds `.build/<slug>/` with `ACCEPTANCE.md`, `evals/cases.json` (the `/eval`
skill's format), an executable `acceptance_check.sh`, an executable `loop.sh`, and
`progress.md`. **The scaffold is red on creation** — it fails its own acceptance until a
human writes real checks into it. That is deliberate: a green scaffold would let a run
claim acceptance it never defined.

Then, in order:

1. Fill in "Done means" — observable outcomes, not activities. *"Returns 403 for a token
   without the write scope"* is an outcome. *"Auth is handled"* is an activity.
2. Fill in the `checks` block — every line must be able to fail. Break the code on purpose
   once and watch it go red before you trust it.
3. Fill in `evals/cases.json`: happy path, every named error path, one boundary per numeric
   parameter, and the failure that would otherwise ship unnoticed.
4. Commit as one commit: `eval: pre-register <slug> acceptance`.
5. Only now write code.

The git history is the evidence the order was respected. Format, coverage bar, judge
rubrics, and the rules for amending acceptance mid-run: `references/acceptance.md`.

**Never edit an expected value to match what the code produced.** That is the single most
common way a build run silently becomes worthless. If the acceptance is genuinely wrong,
stop the loop, say why, and amend it in its own commit.

---

## Phase 5 — implement

> **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.**

Wrote code before the test? Delete it and start over. That is cheaper than it sounds and
much cheaper than the alternative.

Red → Green → Refactor, one behaviour at a time:

- **RED** — write the test, run it, **paste the failing output**. Confirm it fails for the
  right reason (feature missing) and not the wrong one (typo in the import).
- **GREEN** — the least code that passes. No extra features, no refactoring of neighbours.
- **REFACTOR** — only once green, and only with the tests still green.

The showing of red output is the point. A claim that a test was written first is not
evidence that it was. Where a test-first enforcement hook is installed it blocks this
mechanically; where it is not, you enforce it, and the paste is the proof.

---

## Phase 6 — the loop

Set up in Phase 4, used here. Three interchangeable backends, all running the same
`acceptance_check.sh` so "green" never changes meaning:

- `/loop` — preferred locally; keeps context between iterations.
- The `ralph-loop` commands — when installed; completion promise `ACCEPTANCE GREEN`.
- `bash .build/<slug>/loop.sh` — pure shell, works everywhere including the sandbox.

**One change per iteration**, logged in `progress.md` with hypothesis and result. Two
simultaneous changes make the next red output uninterpretable.

Bounded by `MAX_ITERATIONS` (default 20) and stopped early on stuck detection (identical
failure set three iterations running). Hitting either is a signal, not a nuisance:

- Cap reached → stop and report. **Do not raise the cap** without saying why it should
  converge this time.
- Stuck → this is a root-cause problem. Go to Phase 7.

Never loop anything destructive — deletes, migrations, deploys, spend. Loops belong on
tests. Full patterns, exit codes, and anti-patterns: `references/loop-driver.md`.

---

## Phases 7–10

| Phase | The one rule | Depth |
|-------|--------------|-------|
| 7 Debug | No fix without a root cause. One hypothesis at a time, stated as "I think X because Y". Three failed fixes = stop and question the architecture | `superpowers:systematic-debugging` |
| 8 Verify | No completion claim without fresh evidence. Identify the falsifying command → run it whole → read all of it → then claim, with output pasted | `references/ship.md` |
| 9 Refine + review | Question → eliminate → simplify → accelerate → automate. Then the five CRITICAL safety items on the real diff | `references/safety.md`, `references/ship.md` |
| 10 Land | Sync, **re-run tests after the merge**, then push. Integration bugs appear after the merge, not before | `references/ship.md` |

---

## Guardrails (carried forward intact)

**Safety review — five CRITICAL items, run on the real diff in Phase 9.** SQL and data
safety · LLM trust boundary · auth and permissions · secret exposure · injection. Any
CRITICAL finding blocks the ship. One question per finding — *fix now / acknowledge /
false positive* — asked one at a time, because a wall of findings gets waved through.
Detail: `references/safety.md`.

**No secrets.** Never hardcode a secret, token, key, or password — not in source, not in a
fixture, not in a comment, not "temporarily". Grep the staged diff before landing.

**Workflow gates.** Optional hooks. Every gate command is written guarded, so a missing
hook is a silent no-op rather than a broken run, and the phase is enforced conversationally
instead. See `references/safety.md` for the exact guarded form.

**Hard gates before landing:** acceptance green · full suite green on a fresh run · zero
unresolved CRITICAL findings · nothing uncommitted.

---

## Two runtimes

`/build` produces the same decisions in local Claude Code and in the **restricted sandbox**. What
differs is the tooling. No phase may hard-require anything beyond a shell, files, git,
`curl`, and env vars — connected data services and browser automation are optional
everywhere and simply absent in the sandbox, so they are guarded or skipped, never assumed.

Detect the runtime at Phase 0 and say which one you are in. Guard on the capability, not
the runtime name:

```bash
command -v promptfoo >/dev/null 2>&1 \
  && promptfoo redteam eval \
  || echo "SKIPPED: prompt-security suite unavailable — recorded as a gap in the summary"
```

Three rules make a guard real rather than decorative: the absent branch **says something**;
the gap reaches the **summary**; and unattended runs record their assumptions in
`ACCEPTANCE.md` instead of asking. Full capability matrix and degraded paths:
`references/runtimes.md`.

The sandbox is a smaller toolbox, not a lower standard. If something cannot be verified
there, the run says "unverified" — never "assumed fine".

---

## Shortcuts

| Command | Does |
|---------|------|
| `/build <thing>` | Full route, phases 0→10 |
| `/build acceptance <slug>` | Phase 4 only — scaffold and write the acceptance artefact |
| `/build loop <slug>` | Phase 6 only — drive an existing acceptance to green |
| `/build review` | Phase 9 only — refine pass + safety review + code review |
| `/build verify` | Phase 8 only — fresh evidence for every outstanding claim |

## Run log

Every run ends with the summary format in `references/ship.md`. Two rules: **no adjective
that is not backed by a row in the evidence table**, and **the "what I did not verify"
section is written before the good news**, so it does not get trimmed for length.

## Self-test

This skill has its own acceptance suite, pre-registered the same way it demands of every
run it drives:

```bash
python3 skills/build/evals/check_routing.py    # routing covers 100% of installed practice skills
python3 skills/build/evals/run_checks.py       # deterministic acceptance checks
```

If either goes red after an edit to this skill, the edit is wrong until proven otherwise.

## Usage tracking (company convention)

Optionally record one memory fact: `used build for <5-word purpose>`. Skip if no memory tool exists.
