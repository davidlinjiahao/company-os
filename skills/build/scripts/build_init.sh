#!/usr/bin/env bash
#
# build_init.sh — scaffold the acceptance artefact and loop driver for one /build run.
#
# Usage:  bash build_init.sh <slug> [target-dir]
#
# Creates <target-dir>/.build/<slug>/ containing:
#   ACCEPTANCE.md        the contract, with a checks block that is RED by default
#   evals/cases.json     eval cases skeleton, in the /eval skill's format
#   acceptance_check.sh  runs every line of the checks block; exits 0 only if all pass
#   loop.sh              re-runs acceptance_check.sh until green, bounded
#   progress.md          iteration log
#
# Deliberately red on creation: a freshly scaffolded run MUST fail its own acceptance
# until a human writes real checks into it. Portable POSIX-ish bash; no external deps
# beyond coreutils, so it runs unchanged in the sandbox.

set -euo pipefail

SLUG="${1:-}"
TARGET="${2:-.}"

if [ -z "$SLUG" ]; then
  echo "usage: build_init.sh <slug> [target-dir]" >&2
  exit 64
fi

case "$SLUG" in
  */*|.*) echo "slug must be a simple name (no slashes, no leading dot)" >&2; exit 64 ;;
esac

RUN_DIR="$TARGET/.build/$SLUG"
if [ -e "$RUN_DIR" ]; then
  echo "refusing to overwrite existing run dir: $RUN_DIR" >&2
  exit 65
fi

mkdir -p "$RUN_DIR/evals"

# ---------------------------------------------------------------- ACCEPTANCE.md
cat > "$RUN_DIR/ACCEPTANCE.md" <<ACCEPT
# ACCEPTANCE — $SLUG

Written and committed BEFORE any implementation code. Fill every section in before you
write a line of the thing itself.

## Done means

- [ ] <observable outcome, not an activity>
- [ ] <observable outcome>
- [ ] <the failure that would otherwise ship unnoticed>

## Out of scope

- <what this run will not do>

## Assumptions

- <decisions taken without asking, for unattended runs. Empty is fine when a human is present.>

## Checks

Every non-comment line below is run by acceptance_check.sh from the project root.
All must exit 0. Prefix with ! to assert that a command fails.

\`\`\`checks
false  # REPLACE: this scaffold is red on purpose. Write real checks here.
\`\`\`

## Known-unrunnable

- <checks that cannot be automated, the manual steps, and who signs them off>
ACCEPT

# ---------------------------------------------------------------- cases.json
cat > "$RUN_DIR/evals/cases.json" <<CASES
{
  "component": "$SLUG",
  "type": "skill",
  "version": "1.0",
  "cases": [
    {
      "id": "happy-path",
      "category": "functional",
      "description": "REPLACE: the primary behaviour, stated so it could fail",
      "input": {"command": "REPLACE"},
      "expected": {"contains": ["REPLACE"]},
      "metrics": ["TaskCompletion"]
    },
    {
      "id": "error-path",
      "category": "safety",
      "description": "REPLACE: one named failure mode, and what the user sees",
      "input": {"command": "REPLACE"},
      "expected": {"must_not_contain": ["Traceback", "500"]},
      "metrics": ["ErrorHandling"]
    },
    {
      "id": "silent-failure",
      "category": "safety",
      "description": "REPLACE: the thing that would break without anyone noticing",
      "input": {"command": "REPLACE"},
      "expected": {"no_error": true},
      "metrics": ["ErrorHandling"]
    }
  ]
}
CASES

# ---------------------------------------------------------------- acceptance_check.sh
cat > "$RUN_DIR/acceptance_check.sh" <<'CHECK'
#!/usr/bin/env bash
# Runs every check in ACCEPTANCE.md. Exit 0 only if all of them pass.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACCEPTANCE="$SCRIPT_DIR/ACCEPTANCE.md"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

if [ ! -f "$ACCEPTANCE" ]; then
  echo "acceptance_check: no ACCEPTANCE.md at $ACCEPTANCE" >&2
  exit 70
fi

checks="$(awk '/^```checks$/{f=1;next} /^```$/{f=0} f' "$ACCEPTANCE")"

if [ -z "$(printf '%s' "$checks" | tr -d '[:space:]')" ]; then
  echo "acceptance_check: checks block is empty — acceptance was never written" >&2
  exit 71
fi

passed=0
failed=0
cd "$PROJECT_ROOT" || exit 72

while IFS= read -r line; do
  case "$line" in
    ''|'#'*) continue ;;
  esac
  if bash -o pipefail -c "$line"; then
    passed=$((passed + 1))
    echo "  PASS  $line"
  else
    failed=$((failed + 1))
    echo "  FAIL  $line" >&2
  fi
done <<EOF
$checks
EOF

echo "acceptance: $passed passed, $failed failed"
[ "$failed" -eq 0 ]
CHECK

# ---------------------------------------------------------------- loop.sh
cat > "$RUN_DIR/loop.sh" <<'LOOP'
#!/usr/bin/env bash
# Loop driver, backend C (pure shell — works in every runtime).
# Re-runs acceptance_check.sh until green, bounded, with stuck detection.
#
#   MAX_ITERATIONS=20 bash loop.sh
#
# Between iterations this script does nothing clever: it is the human or the agent that
# makes ONE change per iteration and appends to progress.md. The loop only decides when
# to stop.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_ITERATIONS="${MAX_ITERATIONS:-20}"
last=""
repeats=0

for i in $(seq 1 "$MAX_ITERATIONS"); do
  echo "=== acceptance iteration $i/$MAX_ITERATIONS ==="
  out="$(bash "$SCRIPT_DIR/acceptance_check.sh" 2>&1)"
  status=$?
  printf '%s\n' "$out"

  if [ "$status" -eq 0 ]; then
    echo "ACCEPTANCE GREEN after $i iteration(s)"
    exit 0
  fi

  fp="$(printf '%s' "$out" | grep '^  FAIL' | sort | tr -d ' ')"
  if [ "$fp" = "$last" ]; then
    repeats=$((repeats + 1))
  else
    repeats=0
  fi
  last="$fp"

  if [ "$repeats" -ge 2 ]; then
    echo "STUCK: identical failure set 3 iterations running." >&2
    echo "This is a root-cause problem, not a loop problem — run systematic-debugging." >&2
    exit 3
  fi

  echo "--- red. Make ONE change, log it in progress.md, then this loop runs again. ---"
done

echo "MAX_ITERATIONS ($MAX_ITERATIONS) reached without going green." >&2
echo "Do not raise the cap without saying why it should converge this time." >&2
exit 2
LOOP

# ---------------------------------------------------------------- progress.md
cat > "$RUN_DIR/progress.md" <<PROGRESS
# progress — $SLUG

One block per iteration. This file is the run's memory across context rotations: it is what
stops iteration 12 from retrying what iteration 4 already disproved.

## Iteration 0 — scaffold
Red: acceptance not yet written (scaffold ships red on purpose)
Next: fill in ACCEPTANCE.md "Done means" and the checks block, then commit before any code
PROGRESS

chmod +x "$RUN_DIR/acceptance_check.sh" "$RUN_DIR/loop.sh"

cat <<DONE
Scaffolded $RUN_DIR

  ACCEPTANCE.md        <- fill this in FIRST, then commit, then write code
  evals/cases.json     <- eval cases, /eval skill format
  acceptance_check.sh  <- executable; currently RED by design
  loop.sh              <- executable; re-runs acceptance until green
  progress.md          <- one block per iteration

Next:
  1. Write the acceptance and the cases.
  2. git add $RUN_DIR && git commit -m "eval: pre-register $SLUG acceptance"
  3. Only then start implementing.
DONE
