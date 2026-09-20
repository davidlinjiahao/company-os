# GOLD — pre-registered acceptance for the `pmf` skill (public template)

Synthetic corpus. No real people, no real companies. Thresholds must not be
relaxed to make a run pass.

## 1. What is being tested

| Command | Contract |
|---|---|
| `/pmf questions <hypothesis or persona>` | Past-behaviour question bank, named persona, falsifiable hypotheses. |
| `/pmf log <transcript…>` | Quote-backed insights, numbers, compliment-zone excluded, hypothesis scoreboard, next questions. |

## 2. Fixtures

Four invented auto-shop discovery calls in `evals/fixtures/`.

| Fixture | Role |
|---|---|
| `call-A.md` | Full call. Pitch at **`[18:00]`**. |
| `call-B.md` | Excerpts. Diarization split across three labels. |
| `call-C.md` | Advisor who wants to join — enthusiasm is not a buy signal. |
| `call-D-postpitch.md` | Call A from the pitch onward. Negative control. |

**Known sampling bias:** all three interviewees are independent-shop owners. A correct run says so.

## 3. Gold insights (threshold ≥ 8 of 10)

See `score.py` `GOLD` for anchors. Decision-changing claims:

1. `dies-in-weeks` — tablet abandoned by techs in two weeks
2. `forced-use` — owner made them use it; they never asked
3. `dealer-stigma` — "dealer software, not for independents"
4. `owner-overhead` — another login to babysit
5. `counter-is-battery` — counter person is the battery; techs walk around a dead board
6. `lunch-logistics` — board-checking is lunch logistics, not theft fear
7. `catalog-not-screen` — objection is stale catalog, not the screen
8. `texts-funnel` — 3–4 parts texts/week, half ignored
9. `emotional-blindness` — "how was the day / fine"; comebacks hidden by shame
10. `post-pitch-contamination` — every price and "sign me up" is after `[18:00]`

## 4. Compliment-zone blocklist

`$200` / "sign me up" / "you're nailing it" may appear **only** under a contamination heading.

## 5–10

Same structural bars as the original method: ≥ 30 questions, hypothetical-form ≤ 20%,
≥ 4 of 6 countables, ≥ 6 scoreboard rows with at least one REFUTED, ≥ 8 next questions,
negative control yields 0 validated insights, SKILL.md ≤ 200 lines, two runtimes, no
personal names, no recorder share tokens.

```bash
python3 skills/pmf/evals/score.py --structure
python3 skills/pmf/evals/score.py --selftest
```
