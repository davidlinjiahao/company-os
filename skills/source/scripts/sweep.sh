#!/usr/bin/env bash
# sweep.sh — run every scraper lane for one role profile, then merge.
#
# Usage:
#   sweep.sh --profile <role.json> [--out <dir>] [--dry-run] [--only <lane,lane>]
#   sweep.sh --help
#
# Lanes: hn, reddit, v2ex, github, waas-jobs, waas-candidates
# Each lane is independent. A lane that lacks credentials, is disabled in the
# profile, or is blocked by the source prints a skip and the sweep continues —
# then `merge.py` combines whatever landed. Un-swept lanes are reported at the
# end so they can be surfaced as blind spots rather than silently dropped.

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROFILE=""; OUT=""; DRY=""; ONLY=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --profile) PROFILE="${2:-}"; shift 2 ;;
    --out)     OUT="${2:-}"; shift 2 ;;
    --only)    ONLY="${2:-}"; shift 2 ;;
    --dry-run) DRY="--dry-run"; shift ;;
    *) echo "unknown argument: $1 (try --help)" >&2; exit 2 ;;
  esac
done

if [[ -z "$PROFILE" ]]; then
  echo "ERROR: --profile is required (see profiles/TEMPLATE.json)" >&2
  exit 2
fi

OUT_ARG=(); [[ -n "$OUT" ]] && OUT_ARG=(--out "$OUT")

LANES=(hn reddit v2ex github waas-jobs waas-candidates)
run_lane() {
  case "$1" in
    hn)               python3 "$HERE/hn_hired.py"            --profile "$PROFILE" "${OUT_ARG[@]}" $DRY ;;
    reddit)           python3 "$HERE/reddit_forhire.py"      --profile "$PROFILE" "${OUT_ARG[@]}" $DRY ;;
    v2ex)             python3 "$HERE/v2ex_cv.py"             --profile "$PROFILE" "${OUT_ARG[@]}" $DRY ;;
    github)           python3 "$HERE/github_contributors.py" --profile "$PROFILE" "${OUT_ARG[@]}" $DRY ;;
    waas-jobs)        python3 "$HERE/yc_waas.py" --mode jobs       --profile "$PROFILE" "${OUT_ARG[@]}" $DRY ;;
    waas-candidates)  python3 "$HERE/yc_waas.py" --mode candidates --profile "$PROFILE" "${OUT_ARG[@]}" $DRY ;;
    *) echo "unknown lane: $1" >&2; return 2 ;;
  esac
}

if [[ -n "$ONLY" ]]; then
  IFS=',' read -r -a LANES <<< "$ONLY"
fi

FAILED=()
for lane in "${LANES[@]}"; do
  echo
  echo "──────── $lane ────────"
  if ! run_lane "$lane"; then
    echo "  ! $lane exited non-zero — recording as UN-SWEPT" >&2
    FAILED+=("$lane")
  fi
done

echo
echo "──────── merge ────────"
python3 "$HERE/merge.py" --profile "$PROFILE" "${OUT_ARG[@]}" $DRY || FAILED+=(merge)

echo
if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo "UN-SWEPT lanes (report these as blind spots, do not present the list as complete): ${FAILED[*]}"
  exit 1
fi
echo "All lanes swept."
