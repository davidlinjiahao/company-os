# RESULTS — `/build` rebuild acceptance run

- Run date: 2026-08-03
- Branch: `rebuild/build-v2` · Worktree: `/tmp/company-os-wt/build`
- Cases: `cases.json` v4.0 (21 cases), pre-registered at commit `659b665`, **before** any
  rebuilt skill content existed.
- Reproduce: `python3 skills/build/evals/check_routing.py` and
  `python3 skills/build/evals/run_checks.py` from the repo root.

## Verdict

**ACCEPTED, with two categories of unproven work explicitly outstanding.**

Every runnable check passed (16/16). Nothing failed. The three end-to-end benchmark runs
and the two LLM-judge cases could not run this pass and are recorded as PENDING — they are
**not** passes, and the following claims remain unproven until they run:

- That an agent *actually follows* the dispatcher end-to-end (only the artefacts and rules
  are verified, not the behaviour they are meant to produce).
- That code produced under this skill scores ≥ 4.0/5 on the code-quality rubric.

## Per-case results

| # | Case | Runner | Result | Evidence |
|---|------|--------|--------|----------|
| 1 | `routing-coverage-100pct` | shell | **PASS** | `ROUTING COVERAGE: 16/16`, `MISSING: none`, `SKIP-RULE COVERAGE: 16/16`, `LIVE-DRIFT-EXTRA: none` |
| 2 | `skill-md-has-phase-routing-table` | shell | **PASS** | Header `Phase \| Skill to invoke \| Skip when`, `phase_rows=11` |
| 3 | `skill-md-frontmatter-and-size` | shell | **PASS** | `name=build description=ok lines<=300` (actual: 216 lines) |
| 4 | `progressive-disclosure-references-resolve` | shell | **PASS** | `dead_links=0 orphan_references=0` |
| 5 | `tdd-is-the-spine` | shell | **PASS** | `tdd_never_skipped=true iron_law_present=true` |
| 6 | `acceptance-pre-registered-before-implementation` | shell | **PASS** | `acceptance_before_impl=true eval_format_referenced=true cases_json_mandated=true` |
| 7 | `loop-driver-documented` | shell | **PASS** | `loop_pattern=true shell_fallback=true max_iterations=true stuck_detection=true` |
| 8 | `build-init-emits-acceptance-and-loop-driver` | shell | **PASS** | All 4 artefacts present; `loop.sh` and `acceptance_check.sh` executable |
| 9 | `loop-driver-red-then-green` | shell | **PASS** | `red_exit_nonzero=true green_exit_zero=true` — scaffold ships red, goes green when checks are satisfied |
| 10 | `guardrails-preserved-safety-review` | shell | **PASS** | `critical_items=5/5 blocking_gate=true` |
| 11 | `guardrails-workflow-gate-guarded` | shell | **PASS** | `unguarded_invocations=0` (see "Failures found and fixed" below) |
| 12 | `guardrails-no-secrets` | shell | **PASS** | `secret_literals=0 no_secrets_rule=true` |
| 13 | `dual-runtime-mcp-guarded` | shell | **PASS** | `runtime_matrix=true qm_sandbox_documented=true unguarded_mcp_steps=0` |
| 14 | `scripts-are-portable-and-lint-clean` | shell | **PASS** | `bash_syntax_ok=true hardcoded_user_paths=0` |
| 15 | `benchmarks-three-specs-present` | shell | **PASS** | `specs=3 cli_spec=true api_spec=true bugfix_spec=true all_specs_declare_acceptance=true` |
| 16 | `seeded-bug-fixture-actually-broken` | shell | **PASS** | `fixture_suite_passes=true heldout_repro_fails=true fix_makes_heldout_pass=true` |
| 17 | `benchmark-run-cli-tool` | manual-benchmark | **RUN-PENDING** | e2e run not executed this pass (permitted by the task brief) |
| 18 | `benchmark-run-api-endpoint` | manual-benchmark | **RUN-PENDING** | as above |
| 19 | `benchmark-run-bugfix` | manual-benchmark | **RUN-PENDING** | as above |
| 20 | `judge-code-quality-benchmarks` | llm-judge | **JUDGE-PENDING** | No `ANTHROPIC_API_KEY` in env; also blocked on 17–19 producing artefacts to judge |
| 21 | `judge-skill-md-dispatch-clarity` | llm-judge | **JUDGE-PENDING** | No `ANTHROPIC_API_KEY` in env, and no `anthropic` SDK installed |

**Totals: 16 PASS · 0 FAIL · 5 PENDING (3 RUN-PENDING, 2 JUDGE-PENDING).**

## Failures found and fixed during the run

Recorded because a suite that never went red proves nothing about itself.

1. **`guardrails-workflow-gate-guarded` — FAIL on first run** (`unguarded_invocations=1`,
   `safety.md:67`). The prose warning against unguarded gate calls contained a literal
   unguarded invocation as its own illustration. The checker was right. Fixed the doc, not
   the check: the anti-pattern is now described rather than written out.

## Harness correction, made before any skill content existed

Committed separately at `633fd95`, ahead of the first line of `SKILL.md`, so the ordering is
auditable:

The safety-review, no-secrets-rule and MCP-guard checks originally scanned every markdown
file under `skills/build/`, **including `evals/`**. That meant benchmark spec `02-api-endpoint.md`
— which merely *names* the five CRITICAL safety items as part of its own acceptance — would
have satisfied the safety check on the skill's behalf, and inert file paths in `GOLD.md`
were flagged as unguarded plugin steps. Scope was narrowed to the skill's instructional
surface (`SKILL.md` + `references/`).

This makes those three checks **strictly harder** to pass, not easier. No threshold was
changed, no case text was changed, and the change was made blind to the implementation
(none existed yet). It is recorded here rather than left silent because a post-hoc harness
edit is exactly the move that turns an eval into theatre.

## What would have to happen to remove the PENDINGs

1. Run each benchmark spec end-to-end with `/build` in a scratch worktree, capturing the
   git log (to verify acceptance precedes implementation) and the final
   `acceptance_check.sh` exit code.
2. Grade the three outputs with a judge from a different model family than the builder,
   against the frozen rubric in `GOLD.md` §3. Threshold: mean ≥ 4.0/5, none below 3.5.
3. Re-run case 21 against `SKILL.md` with the same judge.

Until then the honest claim is: **the skill's structure, guardrails and mechanics are
verified; its behaviour under a real agent is not.**

VERDICT: ACCEPTED
