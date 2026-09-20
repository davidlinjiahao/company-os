# Phase 6 — the loop driver

The loop driver is the thing that turns "acceptance is red" into "acceptance is green"
without a human re-typing the same command forty times. It is set up **at the same time as
the acceptance artefact**, in Phase 4, and it sits idle until Phase 6 needs it.

Three backends, in order of preference. All three run the same `acceptance_check.sh`, so
switching backends never changes what "green" means.

---

## Backend A — `/loop` (preferred, local Claude Code)

The `/loop` skill re-invokes a prompt on an interval inside the current session, so the
agent keeps its context and can reason about *why* a check is still red.

```
/loop 3m Run .build/<slug>/acceptance_check.sh. If it exits 0, stop the loop and say
ACCEPTANCE GREEN. Otherwise fix the single highest-signal failure, append an iteration
block to .build/<slug>/progress.md, commit, and wait for the next tick.
```

Use the dynamic form (no interval) when iterations take an unpredictable amount of time —
the agent then self-paces off the check's exit code rather than a clock.

Stop the loop explicitly when green. A loop nobody stopped is a loop that will wake up at
3am and start editing.

## Backend B — `ralph-loop` commands (local, when installed)

If the `ralph-loop` commands are available, `/ralph-loop:ralph-loop` feeds the same prompt
back on every exit, with a completion promise as the exit condition. Set the promise to the
literal string `ACCEPTANCE GREEN` and never emit it while any check is red. `/ralph-loop:cancel-ralph`
stops it. Skip this backend entirely when the commands are not installed.

## Backend C — pure shell (always available, including the restricted sandbox)

No skills, no plugins, no MCP surface — just a bounded shell loop. This is the fallback the
sandbox uses, and it is what `scripts/build_init.sh` writes to `loop.sh`.

```bash
#!/usr/bin/env bash
# Re-run acceptance until green, bounded.
set -uo pipefail
MAX_ITERATIONS="${MAX_ITERATIONS:-20}"
last_fingerprint=""
repeat_count=0

for i in $(seq 1 "$MAX_ITERATIONS"); do
  output="$(bash ./acceptance_check.sh 2>&1)"
  status=$?
  printf '%s\n' "$output"

  if [ "$status" -eq 0 ]; then
    echo "ACCEPTANCE GREEN after $i iteration(s)"
    exit 0
  fi

  fingerprint="$(printf '%s' "$output" | grep -c . )-$(printf '%s' "$output" | md5sum 2>/dev/null || printf '%s' "$output" | md5)"
  if [ "$fingerprint" = "$last_fingerprint" ]; then
    repeat_count=$((repeat_count + 1))
  else
    repeat_count=0
  fi
  last_fingerprint="$fingerprint"

  if [ "$repeat_count" -ge 2 ]; then
    echo "STUCK: identical failure 3 times in a row. Stopping." >&2
    exit 3
  fi

  echo "--- iteration $i red; make one change, then this loop runs again ---"
done

echo "MAX_ITERATIONS ($MAX_ITERATIONS) reached without going green" >&2
exit 2
```

---

## Exit conditions (all backends)

| Condition | Exit | What to do |
|-----------|------|-----------|
| Every check exits 0 | 0 | Stop. Move to Phase 8. |
| `MAX_ITERATIONS` reached | 2 | Stop. Report how far it got. Do **not** raise the cap without saying why. |
| Identical failure output 3 times running | 3 | Stop. You are not converging — this is a `systematic-debugging` problem, not a loop problem. |
| No file changed in the last 2 iterations | 3 | Same as above: the loop is idling. |
| A check needs a human decision | stop | Loops cannot decide. Surface the decision. |

## Iteration discipline

**One change per iteration.** Two simultaneous changes make the next red output
uninterpretable — you no longer know which one moved the needle. This is the same rule as
`systematic-debugging`'s one-hypothesis-at-a-time, applied to an unattended runner.

Every iteration appends to `progress.md`:

```markdown
## Iteration 7 — 2026-08-03T14:22Z
Red: test_idempotent_resubmit — got two ids, expected one
Hypothesis: the cache key omits the token, so two callers collide
Change: include token hash in the key (exports/service.py:88)
Result: GREEN for that check; test_403_without_scope still red
```

`progress.md` is not bookkeeping. It is what stops iteration 12 from re-trying what
iteration 4 already disproved, especially after a context rotation.

## Anti-patterns

- **Raising `MAX_ITERATIONS` because you hit it.** The cap is a smoke alarm; muting it does
  not put the fire out.
- **Loosening a check because the loop keeps failing it.** If the check is genuinely wrong,
  amend acceptance explicitly per `acceptance.md`. If it is right, the code is wrong.
- **Unattended loops on anything destructive.** Never loop a step that deletes, migrates,
  deploys, or spends money. Loops belong on tests.
- **Looping on a red baseline.** If the checks were already failing before your change,
  fix the baseline first or you are chasing someone else's bug.
