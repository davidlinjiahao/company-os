# Bug report — rolling peak looks stale

**Reported by:** ops, via the weekly balance report.

**What they saw.** An account whose balance was 5 on day 1 and then 1 for the next three
days still shows a "3-day peak" of 5 on day 4. By day 4, the trailing three days are days
2, 3 and 4 — all of which are 1 — so the peak should be 1.

The knock-on effect is that the drawdown column shows a 4-unit drawdown on day 4 that the
account does not actually have, which is what ops noticed.

**Reproduce:**

```
balances = [5, 1, 1, 1]
window   = 3
```

**What we expect:** the day-4 peak reflects only days 2–4.

**Notes.** `python3 -m unittest discover -s tests` is green on this repo, so whatever this
is, the current tests do not cover it. There is no known workaround.
