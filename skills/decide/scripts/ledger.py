#!/usr/bin/env python3
"""
Emit and validate the single ledger row that every decision produces.

Frozen schema (see evals/GOLD.md):

    | date | decision | type | recommendation | owner | outcome:pending |

One row per decision. The outcome column is literally `outcome:pending` at write
time; outcomes are graded later, by hand, by editing the row.

Usage:
    python3 scripts/ledger.py --date 2026-08-03 --decision "Sign the Kestrel supply deal" \
        --type 1-way --recommendation MODIFY --owner Alex

    python3 scripts/ledger.py --validate "| 2026-08-03 | ... | outcome:pending |"

Exits non-zero (and prints nothing to stdout) if the row would be invalid — a bad
recommendation is rejected, never coerced.

Standard library only, so it runs identically in local Claude Code and in the restricted sandbox.
"""
from __future__ import annotations

import argparse
import re
import sys

RECOMMENDATIONS = ("GO", "NO-GO", "MODIFY", "DEFER")
DOOR_TYPES = ("1-way", "2-way")

ROW_REGEX = (
    r"^\| \d{4}-\d{2}-\d{2} \| [^|]{3,120} \| (1-way|2-way) \| "
    r"(GO|NO-GO|MODIFY|DEFER) \| [^|]{1,60} \| outcome:pending \|$"
)

HEADER = (
    "| date | decision | type | recommendation | owner | outcome |\n"
    "|---|---|---|---|---|---|"
)


def build_row(date: str, decision: str, door_type: str,
              recommendation: str, owner: str) -> str:
    """Build a row, raising ValueError on anything that would not validate."""
    errs = []
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        errs.append(f"date must be YYYY-MM-DD, got {date!r}")
    decision = " ".join(decision.split())
    if "|" in decision or not (3 <= len(decision) <= 120):
        errs.append("decision must be 3-120 chars on one line with no '|'")
    if door_type not in DOOR_TYPES:
        errs.append(f"type must be one of {DOOR_TYPES}, got {door_type!r}")
    if recommendation not in RECOMMENDATIONS:
        errs.append(f"recommendation must be one of {RECOMMENDATIONS}, "
                    f"got {recommendation!r} — rejected, not coerced")
    owner = " ".join(owner.split())
    if "|" in owner or not (1 <= len(owner) <= 60):
        errs.append("owner must be 1-60 chars with no '|'")
    if errs:
        raise ValueError("; ".join(errs))

    row = (f"| {date} | {decision} | {door_type} | {recommendation} | "
           f"{owner} | outcome:pending |")
    if not re.fullmatch(ROW_REGEX, row):
        raise ValueError(f"assembled row failed schema check: {row}")
    return row


def validate_row(row: str) -> bool:
    return bool(re.fullmatch(ROW_REGEX, row.strip()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date")
    ap.add_argument("--decision")
    ap.add_argument("--type", dest="door_type", choices=list(DOOR_TYPES) + ["other"])
    ap.add_argument("--recommendation")
    ap.add_argument("--owner")
    ap.add_argument("--header", action="store_true", help="also print the table header")
    ap.add_argument("--validate", help="validate an existing row and exit")
    args = ap.parse_args()

    if args.validate:
        if validate_row(args.validate):
            print("valid")
            return 0
        print(f"invalid ledger row: {args.validate}", file=sys.stderr)
        return 1

    missing = [f"--{n}" for n, v in (("date", args.date), ("decision", args.decision),
                                     ("type", args.door_type),
                                     ("recommendation", args.recommendation),
                                     ("owner", args.owner)) if not v]
    if missing:
        print(f"missing required arguments: {', '.join(missing)}", file=sys.stderr)
        return 2

    try:
        row = build_row(args.date, args.decision, args.door_type,
                        args.recommendation, args.owner)
    except ValueError as e:
        print(f"refusing to emit an invalid ledger row: {e}", file=sys.stderr)
        return 1

    if args.header:
        print(HEADER)
    print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
