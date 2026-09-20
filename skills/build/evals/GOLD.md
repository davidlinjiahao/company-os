# GOLD — pre-registered acceptance for the `/build` rebuild

Frozen **before** any skill content was written. Nothing in here may be weakened to make a
case pass. If a threshold turns out to be wrong, the honest move is to record a FAIL in
`RESULTS.md` and raise it with the operator — not to edit this file.

- Pre-registered: 2026-08-03
- Branch: `rebuild/build-v2`
- Worktree: `/tmp/company-os-wt/build`
- Cases: `skills/build/evals/cases.json`
- Deterministic runner: `skills/build/evals/run_checks.py`
- Routing checker: `skills/build/evals/check_routing.py`

---

## 1. Frozen inventory of installed practice skills (the coverage denominator)

**Definition used.** A *practice skill* is a skill that teaches an engineering **practice**
(how to work), not a **domain** (what to work on). Domain skills in `~/.claude/skills/`
(`email`, `legal`, `prd`, `network`, …) are out of scope: `/build` never dispatches to them.
Two local/harness skills — `eval` and `loop` — are dispatched by `/build` but are covered by
dedicated cases (`acceptance-pre-registered-before-implementation`, `loop-driver-documented`)
rather than by the coverage count, because they are workflow infrastructure rather than
practice guidance.

**Inventory command (reproduces the denominator):**

```bash
ls ~/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0/skills/   # 14
ls -d ~/.claude/plugins/cache/claude-plugins-official/frontend-design/*/skills/*  # frontend-design
# dataviz: harness-provided (bundled with the CLI, no on-disk path); appears in the
#          available-skills listing. Treated as installed.
```

**Result — 16 practice skills, enumerated (this is the gold list):**

| # | Skill | Source | Path / provenance |
|---|-------|--------|-------------------|
| 1 | `brainstorming` | superpowers 6.2.0 | `…/superpowers/6.2.0/skills/brainstorming` |
| 2 | `writing-plans` | superpowers 6.2.0 | `…/skills/writing-plans` |
| 3 | `executing-plans` | superpowers 6.2.0 | `…/skills/executing-plans` |
| 4 | `subagent-driven-development` | superpowers 6.2.0 | `…/skills/subagent-driven-development` |
| 5 | `dispatching-parallel-agents` | superpowers 6.2.0 | `…/skills/dispatching-parallel-agents` |
| 6 | `using-git-worktrees` | superpowers 6.2.0 | `…/skills/using-git-worktrees` |
| 7 | `test-driven-development` | superpowers 6.2.0 | `…/skills/test-driven-development` |
| 8 | `systematic-debugging` | superpowers 6.2.0 | `…/skills/systematic-debugging` |
| 9 | `verification-before-completion` | superpowers 6.2.0 | `…/skills/verification-before-completion` |
| 10 | `requesting-code-review` | superpowers 6.2.0 | `…/skills/requesting-code-review` |
| 11 | `receiving-code-review` | superpowers 6.2.0 | `…/skills/receiving-code-review` |
| 12 | `finishing-a-development-branch` | superpowers 6.2.0 | `…/skills/finishing-a-development-branch` |
| 13 | `using-superpowers` | superpowers 6.2.0 | `…/skills/using-superpowers` |
| 14 | `writing-skills` | superpowers 6.2.0 | `…/skills/writing-skills` |
| 15 | `frontend-design` | plugin (claude-plugins-official) | `…/frontend-design/*/skills/frontend-design` |
| 16 | `dataviz` | harness-provided | bundled; no on-disk path |

Also installed, **deliberately excluded** from the denominator with reasons:

| Item | Why excluded |
|------|--------------|
| `security-guidance` plugin (2.0.6) | Hooks only — ships no SKILL.md, nothing to dispatch to. Its function is covered by the safety-review gate. |
| `ralph-loop` plugin (1.0.0) | Slash **commands**, not skills. Routed as an optional loop-driver backend; see `references/loop-driver.md`. |
| `artifact-design`, `artifact-capabilities` | Publishing surface, not a build practice. |
| 29 Aligned domain skills in `~/.claude/skills/` | Domain, not practice (see definition above). |
| `simplify`, `code-review`, `security-review`, `run`, `learn` | Harness slash-commands; routed opportunistically, guarded as optional. |

**PASS bar:** all 16 names appear in the routing table in `references/routing.md`, each with a
non-empty "skip when" rule, and each phase row in `SKILL.md` resolves to at least one of them.
Anything less than 16/16 is a FAIL. There is no partial credit.

---

## 2. Gold answers per deterministic case

| Case | Gold / threshold |
|------|------------------|
| `routing-coverage-100pct` | `ROUTING COVERAGE: 16/16`, `MISSING: none`, `SKIP-RULE COVERAGE: 16/16` |
| `skill-md-has-phase-routing-table` | A markdown table in `SKILL.md` whose header contains `Phase`, `Skill to invoke`, `Skip when` |
| `skill-md-frontmatter-and-size` | Frontmatter parses; `name: build`; non-empty `description`; file ≤ 300 lines |
| `progressive-disclosure-references-resolve` | 0 dead links, 0 orphan files under `references/` |
| `tdd-is-the-spine` | `test-driven-development` row's skip cell says never/none; `SKILL.md` contains the no-production-code-without-a-failing-test law |
| `acceptance-pre-registered-before-implementation` | `SKILL.md` states ACCEPTANCE + `cases.json` are written and committed **before** implementation, and names the `/eval` skill as the format authority |
| `loop-driver-documented` | `/loop` pattern documented **and** a pure-shell fallback **and** a max-iteration cap **and** stuck detection |
| `build-init-emits-acceptance-and-loop-driver` | `scripts/build_init.sh` in a scratch dir produces `ACCEPTANCE.md`, `evals/cases.json`, executable `loop.sh` and `acceptance_check.sh` |
| `loop-driver-red-then-green` | Generated `acceptance_check.sh` exits **non-zero** with an unmet check and **0** once met |
| `guardrails-preserved-safety-review` | All 5 CRITICAL items present: SQL/data safety, LLM trust boundary, auth/permissions, secret exposure, injection — and a stated blocking gate |
| `guardrails-workflow-gate-guarded` | ≥1 `WORKFLOW_GATE` mention; **0** invocations lacking an `[ -x … ]`/`command -v` guard |
| `guardrails-no-secrets` | 0 credential-shaped literals (`sk-ant-…`, `AKIA…`, `ghp_…`, `xoxb-…`, long hex/base64 assigned to key-ish names); explicit no-secrets rule present |
| `dual-runtime-mcp-guarded` | A local-vs-qm capability matrix exists; `qm` sandbox named; **0** unguarded `mcp__*` / plugin-dependent steps |
| `scripts-are-portable-and-lint-clean` | `bash -n` clean on every `.sh`; 0 hardcoded `/Users/<name>` or `/home/<name>` paths |
| `benchmarks-three-specs-present` | Exactly 3 specs; one each CLI / API+tests / bugfix; each contains an `## Acceptance` section |
| `seeded-bug-fixture-actually-broken` | Fixture's own suite exits 0; held-out repro test exits non-zero; applying the known fix makes the held-out test exit 0 |

### Seeded bug — gold answer (held out from the benchmark agent)

- **Fixture:** `evals/benchmarks/fixtures/ledger-app/`
- **File:** `ledger/report.py`, function `rolling_max`
- **Bug:** window start computed as `max(0, i - window)` instead of `max(0, i - window + 1)` —
  an off-by-one that makes each window one element too wide.
- **Symptom (what the benchmark agent is told):** the 3-day rolling peak for
  `[5, 1, 1, 1]` reports `5` on day 4, when day 4's trailing 3 days are `[1, 1, 1]`.
- **Gold fix:** one-character-class change to `max(0, i - window + 1)`.
- **Why it is a fair test:** the fixture's shipped tests all pass — they only use windows
  where the off-by-one is invisible (monotone input). Finding it requires reproducing from
  the symptom, not running the existing suite.

---

## 3. Judge rubrics and thresholds

`judge-code-quality-benchmarks` — **mean ≥ 4.0/5**, and **no single benchmark < 3.5**.
Dimensions (1–5 each): correctness, test quality, simplicity, readability, safety.
Judge must be a **different model family** from the builder (per the eval methodology:
hold the model constant across systems, use a different-family judge).

`judge-skill-md-dispatch-clarity` — **≥ 4.0/5** on dispatch clarity, unambiguous skip
conditions, unmissable acceptance-first requirement, clear qm-sandbox degradation, and no
reference-depth content leaking into `SKILL.md`.

**If no `ANTHROPIC_API_KEY` (or equivalent) is present, these are reported `JUDGE-PENDING`.**
JUDGE-PENDING is *not* a pass and blocks the "ACCEPTED" verdict from being unconditional.

---

## 4. Verdict rule

Write `ACCEPTED` in `RESULTS.md` only if **every runnable check passed and none failed**.
PENDING cases (benchmarks not run, judge unavailable) must be listed explicitly next to the
verdict; they do not count as passes and the verdict must state what remains unproven.
