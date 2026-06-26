---
name: build
description: Complete development workflow from idea to merged code. Use when starting any feature, bugfix, or project. Combines brainstorming, planning, TDD, debugging, and verification into one optimal flow.
user-invocable: true
argument-hint: "[feature description]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task
---

# /build - Complete Development Workflow

## Overview

One command to rule them all. Takes you from rough idea to merged, tested code.

**Flow:** Brainstorm → Plan → Mode Select → Setup → Implement (TDD) → Code Review → Quality Gates → Debug (if needed) → Verify → Summary → Complete

**Announce at start:** "I'm using the /build skill to guide this development workflow."

## Shortcuts

| Command | What It Does |
|---------|-------------|
| `/build review [scope]` | Code review + duplication check in one pass |
| `/build [feature]` | Full workflow (brainstorm → ship) |

### `/build review`

Quick quality audit without running the full build flow. Spawns `code-reviewer` and `duplication-hunter` subagents **in parallel** via the Task tool.

**Process:**
1. Spawn both subagents in parallel:
   - `code-reviewer` — quality score, plain English summary, issues found
   - `duplication-hunter` — duplicate code patterns, duplication ratio
2. Present combined results:
   - Quality Score: X/10
   - Duplication: X% (PASS/WARN/BLOCK)
   - Issues found (plain English)
   - Recommendations
3. Ask user: **Fix issues now?** or **Ship as-is?**

If the user says "fix them", execute fixes directly — no need to re-enter the full build flow.

## Execution Modes

| Mode | Description | Best For |
|------|-------------|----------|
| **Interactive** (default) | Human checkpoints at each phase | Complex features, new patterns |
| **Ralph** | Autonomous iteration until tests pass | Mechanical tasks, migrations |
| **Hybrid** | Ralph implements, human reviews at gates | Balanced autonomy + control |

## Execution Model: Quality Gates

**Your role:** Approve/decline/provide ideas. Nothing else.

- **At review checkpoints:** Quality subagents run (code review, duplication, coverage)
- **You see:** Plain English summary with quality report
- **You decide:** "Ship it" or "Hold on, I want X instead"

> **Hooks active:** 3-gate enforcement (plan → TDD → review) runs via `settings.json` hooks config. See `hooks/README.md` for details. Quality subagents are invoked at the checkpoints in each phase.

## Common Rationalizations (Don't Fall For These)

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Emergency, no time" | Systematic is FASTER than thrashing. |
| "Just try this first" | First fix sets the pattern. Do it right. |
| "I see the problem" | Seeing symptoms ≠ understanding root cause. |
| "Should work now" | RUN the verification. |

## Subagents

All subagents are invoked via the **Task tool** with the appropriate `subagent_type`.

| Subagent | Purpose | Used In |
|----------|---------|---------|
| `architect` | Design approaches with plain English trade-offs | Phase 1 |
| `tdd-guide` | Enforce RED→GREEN→REFACTOR cycle | Phase 4 |
| `code-reviewer` | Plain English code review with quality score | Phase 4.5, `/build review` |
| `duplication-hunter` | Find duplicate code patterns | Phase 4.75, `/build review` |
| `unslopper` | Clean up low-quality agent-generated code | Phase 4.75 |
| `test-coverage-improver` | Identify uncovered code and generate tests | Phase 4.75 |
| `verify-app` | Run tests and generate manual test checklist | Phase 6 |

### Agent Fleet (Scheduled Operations) — PLANNED

Autonomous agents that run on schedule to keep codebases healthy. "Playing chess on 10 boards — monitoring an army of interns."

The key insight: **merge imperfect code fast**, because cleanup agents run daily and fix the debt automatically.

| Agent | Purpose | Schedule |
|-------|---------|----------|
| `duplication-hunter` | Find and eliminate duplicate code | Daily 2am |
| `test-coverage-improver` | Add tests to uncovered code | Daily 3am |
| `dependency-updater` | Update deps AND fix breaking changes (reads changelogs, not just bumps versions) | Weekly |
| `unslopper` | Clean up imperfect agent-generated code | Daily 4am |
| `logging-inserter` | Add strategic logging (5 files/day) | Daily 5am |

> **Status:** Scheduling infrastructure not yet implemented. These agents can be invoked manually at any time via the Task tool.

---

## Phase 1: Brainstorm (Design)

**Goal:** Turn rough idea into validated design.

### Process

1. **Understand context first**
   - Check project state (files, docs, recent commits)
   - Ask questions ONE AT A TIME
   - Prefer multiple choice when possible

2. **Explore approaches**
   - Propose 2-3 approaches with trade-offs
   - Lead with your recommendation and why
   - YAGNI ruthlessly — remove unnecessary features
   - **For complex decisions:** Spawn an `architect` subagent

3. **Present design incrementally**
   - 200-300 word sections
   - Check after each: "Does this look right so far?"
   - Cover: architecture, components, data flow, error handling, testing

4. **Document**
   - Write to `docs/plans/YYYY-MM-DD-<topic>-design.md`
   - Commit the design document

**Skip when:** Task is a well-defined ticket with clear requirements.

---

## Phase 2: Plan (Implementation Steps)

**Goal:** Create bite-sized task list assuming zero codebase context.

Each task follows the TDD cycle defined in Phase 4: write failing test → implement → verify → commit.

### Plan Format

```markdown
# [Feature] Implementation Plan

> **For Claude:** Use /build to execute this plan task-by-task.

**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]

---

### Task 1: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write failing test**
```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test, verify fails**
Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**
```python
def function(input):
    return expected
```

**Step 4: Run test, verify passes**
Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**
```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

**Save to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

**Gate:** After plan is approved, open Gate 1:
```bash
bash upgrades/hooks/workflow-gate.sh complete plan
```

---

## Phase 2.5: Execution Mode Selection

**Goal:** Choose between interactive or autonomous execution.

After the plan is approved, present execution options:

```
Plan ready. How would you like to proceed?

1. Interactive mode (default) - I guide you through each phase
2. Ralph mode - Autonomous execution until tests pass
3. Hybrid - Ralph implements, you review at checkpoints
```

### When to Recommend Ralph Mode

**Recommend Ralph for:** Mechanical tasks, clear success criteria, well-defined plans, tasks where iteration beats perfection.

**Recommend Interactive for:** Exploratory work, architectural decisions, security-sensitive code, first-time patterns.

### Ralph Mode Configuration

If Ralph mode selected:

1. **Calculate max iterations:**
   | Plan Tasks | Max Iterations |
   |------------|----------------|
   | 1-3 tasks | 15 |
   | 4-7 tasks | 25 |
   | 8+ tasks | 40 |

2. **Auto-detect validation command:**
   ```bash
   [ -f package.json ] && echo "npm test"
   [ -f Cargo.toml ] && echo "cargo test"
   [ -f pytest.ini ] && echo "pytest"
   [ -f pyproject.toml ] && echo "pytest"
   ```

3. **Guardrails:**
   - Creates `progress.txt` documenting each iteration
   - Creates `.ralph/guardrails.md` for learned failure patterns
   - Detects stuck states (same error 3x, no progress 5 iterations)
   - Creates `RALPH-BLOCKED.md` if permanent blocker encountered

4. **On completion:**
   - SUCCESS: Report iterations used, proceed to Phase 4.5
   - BLOCKED: Show blocker file, ask for human guidance
   - MAX_ITERATIONS: Report progress, ask whether to continue or pause

---

## Phase 3: Setup (Isolated Workspace)

**Goal:** Create isolated git worktree with clean test baseline.

**Skip when:** Change is small (< 3 files) or already on a feature branch.

### Process

1. **Create worktree**
   ```bash
   git worktree add .worktrees/<feature> -b feature/<feature>
   cd .worktrees/<feature>
   ```

2. **Install dependencies**
   ```bash
   # Auto-detect
   [ -f package.json ] && npm install
   [ -f Cargo.toml ] && cargo build
   [ -f requirements.txt ] && pip install -r requirements.txt
   [ -f pyproject.toml ] && poetry install
   ```

3. **Verify clean baseline**
   ```bash
   npm test / pytest / cargo test
   ```
   If tests fail: Report failures, ask whether to proceed.

---

## Phase 4: Implement (TDD)

**Goal:** Execute plan using test-driven development.

### The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before test? Delete it. Start over. Spawn a `tdd-guide` subagent to enforce the cycle.

### Red-Green-Refactor Cycle

**RED — Write Failing Test**
```typescript
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };
  const result = await retryOperation(operation);
  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```

**Verify RED** — Run test, confirm it fails for expected reason (feature missing, not typo).

**GREEN — Minimal Code**
```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try { return await fn(); }
    catch (e) { if (i === 2) throw e; }
  }
  throw new Error('unreachable');
}
```

Don't add features. Don't refactor other code. Just pass the test.

**Verify GREEN** — Run test, confirm it passes. All other tests still pass.

**REFACTOR** — After green only. Remove duplication, improve names. Keep tests green.

### TDD Gate

| Check | Result | Action |
|-------|--------|--------|
| Test written first | PASS | Proceed to implement |
| Production code without test | BLOCK | Delete code, write test first |
| Test passes immediately | WARN | Test might be wrong |

**Gate:** After first test is written and failing, open Gate 2:
```bash
bash upgrades/hooks/workflow-gate.sh complete tdd
```

### Execution Options

**Interactive:** Follow plan steps exactly. Batch 3 tasks, report, get feedback.

**Ralph Mode:** If selected in Phase 2.5, execution proceeds autonomously per the Ralph configuration. Progress tracked in `progress.txt`, git commits after each task.

---

## Phase 4.5: Code Review

**Goal:** Get a plain English summary of what was built, with quality score.

### Process

1. Spawn a `code-reviewer` subagent to review the implementation.

2. **Expected output:**
   - **What Changed (30-Second Version)** — Non-technical summary
   - **Files Changed** — Table of files and what each does
   - **Quality Score** — X/10 with breakdown
   - **Issues Found** — In plain English
   - **Recommendations** — Actionable suggestions
   - **Bottom Line** — Ship or fix?

### Quality Gate

| Score | Status | Action |
|-------|--------|--------|
| 7-10 | PASS | Proceed to Phase 4.75 |
| 5-6 | WARN | Review issues, may proceed |
| 3-4 | WARN | Fix recommended |
| 0-2 | BLOCK | Must fix before continuing |

**Gate:** After code review passes (score 5+), open Gate 3:
```bash
bash upgrades/hooks/workflow-gate.sh complete review
```

---

## Phase 4.75: Quality Gates

**Goal:** Run automated quality checks before proceeding.

### Process

Spawn these subagents (in parallel where possible):
- `duplication-hunter` — check for duplicate code
- `unslopper` — check for slop patterns
- `test-coverage-improver` — check coverage

### Hard Gates

| Check | Threshold | Status if Fail |
|-------|-----------|----------------|
| Duplication ratio | > 25% | BLOCK |
| Duplication ratio | > 15% | WARN |
| Slop score | > 20% | BLOCK |
| Coverage | < 70% | BLOCK |
| Coverage | < 80% | WARN |
| Security scan | Any vulnerability | BLOCK |
| Code review score | < 3 | BLOCK |

### Recovery

If any gate **BLOCKs**: Fix the issues in-place and re-run this phase. Do not return to earlier phases.

If any gate **WARNs**: Proceed with warnings noted in the summary.

---

## Phase 5: Debug (When Needed)

**Goal:** Find root cause before attempting fixes.

### The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

### Steps

1. **Root Cause Investigation** — Read error messages carefully, reproduce consistently, check recent changes (git diff), trace data flow backward.

2. **Pattern Analysis** — Find working examples in codebase, compare against references, identify differences.

3. **Hypothesis and Testing** — Form single hypothesis: "I think X because Y." Make SMALLEST possible change to test. One variable at a time. Didn't work? NEW hypothesis (don't add more fixes).

4. **Implementation** — Create failing test case, implement single fix (ONE change), verify fix. **If 3+ fixes failed:** STOP. Question the architecture.

### Red Flags — STOP

- "Quick fix for now"
- "Just try changing X"
- "I don't fully understand but this might work"
- Proposing solutions before tracing data flow

---

## Phase 6: Verify (Before Claiming Done)

**Goal:** Evidence before claims, always.

### The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

### Process

1. Spawn a `verify-app` subagent to verify the implementation.

2. **The Gate Function:**
   - IDENTIFY: What command proves this claim?
   - RUN: Execute the FULL command (fresh, complete)
   - READ: Full output, check exit code, count failures
   - VERIFY: Does output confirm the claim?
   - ONLY THEN: Make the claim

3. **If evals exist:** Run `/eval [component-name]` and include results in the summary.

### Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test output: 0 failures | Previous run, "should pass" |
| Build succeeds | Build exit 0 | Linter passing |
| Bug fixed | Test original symptom | Code changed |

---

## Phase 6.5: Plain English Summary

**Goal:** Provide a summary the founder can understand without reading code.

### Output Format

```
## Build Complete: [Feature Name]

### What We Built
[2-3 sentences a non-technical person can understand]

### How It Works (The Simple Version)
[Analogy-based explanation]

### Quality Report

| Check | Status | Notes |
|-------|--------|-------|
| Tests pass | ✓ | 12 tests, all green |
| Coverage | ✓ | 85% (threshold: 70%) |
| Code review | ✓ | Score: 8/10 |
| Duplication | ✓ | 5% (threshold: 15%) |
| Slop patterns | ✓ | None detected |

### What You Can Test Yourself

1. Go to [URL/location]
2. Click [button]
3. You should see [expected result]

### Ready to Ship?

Yes/No. [Explanation if no]

Options:
1. Ship it (merge to main)
2. Hold - I want changes
```

---

## Phase 6.75: Capture Learnings

**Goal:** Capture patterns, gotchas, and insights from this build session.

### Process

1. **Ask:** "Did you encounter any patterns, gotchas, or insights worth remembering?"

2. **If yes:** Create an instinct file in `learnings/instincts/`:
   - Use kebab-case ID derived from the insight
   - Set confidence to 0.30
   - Set domain based on the insight type
   - Record evidence from this session

3. **If an existing instinct was relevant:** Bump its confidence:
   - Same person re-observing: +0.05
   - Different person confirming: +0.15
   - Update `last_confirmed` date

4. **If no:** Skip — this phase is voluntary.

See `learnings/README.md` for the full instinct format and confidence scoring.

---

## Phase 7: Complete (Finish Branch)

**Goal:** Verify tests → Present options → Execute → Clean up.

### Process

1. **Verify tests pass**
   ```bash
   npm test / pytest / cargo test
   ```
   If tests fail: STOP. Cannot proceed.

2. **Present options**
   ```
   Implementation complete. What would you like to do?

   1. Merge back to main locally
   2. Push and create a Pull Request
   3. Keep the branch as-is (I'll handle it later)
   4. Discard this work
   ```

3. **Execute choice**
   - Option 1: Merge, verify tests on result, delete branch, cleanup worktree
   - Option 2: Push, create PR with summary, cleanup worktree
   - Option 3: Keep worktree, report location
   - Option 4: Confirm with typed "discard", then delete

---

## Quick Reference

| Phase | When to Skip | Key Output |
|-------|--------------|------------|
| 1. Brainstorm | Well-defined ticket | Design doc |
| 2. Plan | Already have plan | Plan doc + Gate 1 open |
| 2.5 Mode Select | Default to interactive | Mode selected |
| 3. Setup | Small change or on branch | Clean baseline |
| 4. Implement (TDD) | - | Working code + tests + Gate 2 open |
| 4.5 Code Review | Quick fix only | Quality score + Gate 3 open |
| 4.75 Quality Gates | Never skip | All gates pass |
| 5. Debug | No bugs | Root cause fix |
| 6. Verify | Never skip | Evidence + eval results |
| 6.5 Summary | Never skip | Plain English summary |
| 6.75 Learnings | No insights | Instinct file (optional) |
| 7. Complete | - | Merged/PR'd code |

### Ralph Mode Summary

When Ralph mode is active (selected in Phase 2.5):
- **Phase 4 runs autonomously** via Ralph loops
- **Human checkpoints** at: Phase 4.5 (Code Review), Phase 6 (Verify), Phase 7 (Complete)
- **Escape hatch**: `RALPH-BLOCKED.md` created if stuck, returns to interactive

## Integration

This skill combines patterns from:
- obra/superpowers: brainstorming, writing-plans, test-driven-development, systematic-debugging, verification-before-completion, using-git-worktrees, finishing-a-development-branch

### Related Skills

| Skill | Integration |
|-------|-------------|
| /eval | Run during Phase 6 if eval cases exist |

Each phase can be invoked independently if needed.

---

## Appendix: Ralph Autonomous Loop Reference

When Ralph mode is selected in Phase 2.5, execution follows this pattern.

### The Loop

```
for i in 1..MAX_ITERATIONS:
  1. Read progress.txt (see what was tried before)
  2. Work on the task (read files, make changes, run tests)
  3. Validate (run validation command if provided)
  4. Document iteration in progress.txt
  5. Git commit if changes made
  6. Check exit conditions → STOP or continue
```

### Exit Conditions

- Validation command succeeds (exit code 0)
- Completion promise string appears in output
- No files changed in last 2 iterations (converged)
- All tests pass AND no TODOs/FIXMEs remain
- Max iterations reached (report status)
- Same error appears 3+ times (stuck)
- Permanent blocker detected (exit with guidance)

### Blocker Detection

| Type | Examples | Action |
|------|----------|--------|
| **Transient** | Network timeout, file lock, API rate limit | Retry with backoff (3 attempts) |
| **Permanent** | File not found, permission denied, iCloud offline | Exit with recovery instructions |
| **Logic error** | Test failed, type error, lint failure | Continue iterating |
| **Environment** | Missing dependency, wrong version | Exit with setup instructions |
| **Stuck loop** | Same error 3x, no progress 5 iterations | Exit, suggest fresh start |

### Guardrails Persistence

Create `.ralph/guardrails.md` to persist learnings across context rotations:
- File handling rules (check imports before adding, verify iCloud files)
- Codebase-specific constraints (env vars, strict mode, ESM-only)
- Patterns that failed (with iteration number and better alternative)

Each iteration: read guardrails first, add new learnings when failures occur.

### Fresh Context Pattern

For long-running tasks, each iteration spawns a fresh Claude process:
```bash
for i in 1..MAX_ITERATIONS; do
  claude --print "$(cat iteration_prompt.md)" \
         --allowedTools "Bash,Read,Write,Edit,Glob,Grep" \
         > iteration_${i}_result.md
  if grep -q "TASK_COMPLETE" iteration_${i}_result.md; then break; fi
  update_iteration_prompt $i
done
```

Agents with fresh context often outperform agents with accumulated (potentially confused) context.

### RALPH-BLOCKED Marker

When encountering permanent blockers, create `RALPH-BLOCKED.md` with:
- Blocker type and detection timestamp
- Issue description
- Recovery steps
- What was tried (iteration log)
- How to resume (delete file and re-run)

Ralph exits immediately when creating this file.
