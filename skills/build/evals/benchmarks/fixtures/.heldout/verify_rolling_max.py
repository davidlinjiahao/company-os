#!/usr/bin/env python3
"""Held-out verification for the seeded bug in fixtures/ledger-app.

Deliberately kept OUTSIDE the fixture repo (dot-directory) so an agent working the bugfix
benchmark cannot find it and pattern-match to the answer. Exits non-zero while the bug is
present, zero once it is fixed.

Run with PYTHONPATH pointed at the fixture (or a patched copy of it):
    PYTHONPATH=../ledger-app python3 verify_rolling_max.py
"""

import sys

from ledger.report import drawdown, rolling_max


def main() -> int:
    failures = []

    got = rolling_max([5, 1, 1, 1], 3)
    want = [5, 5, 5, 1]
    if got != want:
        failures.append(f"rolling_max([5,1,1,1], 3) -> {got}, want {want}")

    got = rolling_max([9, 1, 1], 2)
    want = [9, 9, 1]
    if got != want:
        failures.append(f"rolling_max([9,1,1], 2) -> {got}, want {want}")

    got = rolling_max([3, 2, 1], 1)
    want = [3, 2, 1]
    if got != want:
        failures.append(f"rolling_max([3,2,1], 1) -> {got}, want {want}")

    got = drawdown([5, 1, 1, 1], 3)
    want = [0, 4, 4, 0]
    if got != want:
        failures.append(f"drawdown([5,1,1,1], 3) -> {got}, want {want}")

    # regressions the fix must not introduce
    if rolling_max([1, 2, 3, 4, 5], 3) != [1, 2, 3, 4, 5]:
        failures.append("regression: rising series")
    try:
        rolling_max([1, 2], 0)
    except ValueError:
        pass
    else:
        failures.append("regression: window=0 no longer raises ValueError")

    for f in failures:
        print("FAIL:", f)
    if failures:
        return 1
    print("PASS: rolling_max window boundary correct")
    return 0


if __name__ == "__main__":
    sys.exit(main())
