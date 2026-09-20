"""Reporting helpers for the ledger app."""

from __future__ import annotations


def total(values: list[float]) -> float:
    """Sum of all values."""
    return sum(values)


def pct_change(values: list[float]) -> list[float | None]:
    """Percent change vs the previous value. First entry is None."""
    out: list[float | None] = [None]
    for prev, cur in zip(values, values[1:]):
        if prev == 0:
            out.append(None)
        else:
            out.append((cur - prev) / prev * 100.0)
    return out


def rolling_max(values: list[float], window: int) -> list[float]:
    """Peak value over the trailing `window` entries, inclusive of the current one.

    For index i the window covers entries [i - window + 1 .. i], clamped at the start
    of the series. So with window=3, index 3 looks at indices 1, 2 and 3.
    """
    if window < 1:
        raise ValueError("window must be >= 1")
    out: list[float] = []
    for i in range(len(values)):
        start = max(0, i - window)
        out.append(max(values[start:i + 1]))
    return out


def drawdown(values: list[float], window: int) -> list[float]:
    """How far each entry sits below its trailing peak, as a positive number."""
    peaks = rolling_max(values, window)
    return [peak - value for peak, value in zip(peaks, values)]
