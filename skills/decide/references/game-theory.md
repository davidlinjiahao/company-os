# The game-theory lens

One of the two lenses the panel runs (`scripts/panel.py`, lens `game_theory`). It asks one
plain question: **given what every player actually wants and what happens to them if there
is no deal, which outcome is stable — and can we move the game to a better one?**

This is the lens that catches decisions where you are negotiating with someone. It is useless
for a decision with only one player; the dialectic lens does the work there.

---

## What "game theory" means here, without the jargon

A **game** is any situation where your best move depends on what someone else does. A **player**
is anyone whose choice changes the outcome. An **equilibrium** is a combination of everyone's
choices where nobody can improve their own outcome by changing their mind alone. That is all
"Nash equilibrium" means: *no player can profitably deviate unilaterally.*

The reason this matters: most bad decisions are not bad reasoning, they are plans that require
someone else to act against their own interest. Those plans do not survive contact.

---

## The four facts you need per player

Skipping any one of these breaks the model.

| Fact | Question | Example |
|---|---|---|
| **Position** | What do they *say* they want? | "We need exclusivity." |
| **Interest** | Why do they want it — the need underneath? | "We need to stop our house brand being undercut." |
| **BATNA** | What happens to them if there is no deal? Their next-best option. | "They keep selling their own line, losing nothing." |
| **Leverage** | The concrete lever they control. | "They own the catalog slot and can terminate on 60 days." |

**BATNA** — Best Alternative To a Negotiated Agreement — is the single most useful number in
any negotiation. Whoever has the better BATNA sets the terms, regardless of who talks louder.
If someone's BATNA is excellent, no amount of persuasion moves them.

Down-weight anyone who only talks. Weight whoever holds a real lever.

---

## The structure

Separate **de jure** (what the contracts, titles, and cap table say) from **de facto** (who can
really do what tomorrow morning). The binding constraint almost always lives in the de facto
column: the person who manages the four customers, the engineer who is the only one who can
build the thing, the board seat that has not been filled.

Write down who controls what. This is the board the game is played on.

---

## Solving it

1. **List the strategy sets.** The owner's obvious 2-3 moves, then deliberately hunt for moves
   that are not on the table yet. For each other player, their plausible responses.
2. **Rank the payoffs ordinally.** Who prefers what, in order. Do not invent cardinal numbers —
   made-up payoff matrices are worse than none.
3. **Find the Nash equilibria.** For each candidate outcome, ask each player: could you do
   better by changing your mind alone, given what everyone else is doing? If nobody can, it is
   stable. There is often more than one.
4. **Separate natural from preferred.** The **natural equilibrium** is where the game lands by
   default if nobody does anything clever. The **most-preferred** one is where the owner wants
   to be. Then ask the question that kills most plans: **is the preferred one reachable**, given
   who holds leverage? An equilibrium you cannot reach is not a plan — it is a wish.
5. **Hunt third doors.** A third door is a move that changes the game rather than plays it:
   bringing in a new player, splitting the surplus differently, sequencing, side payments,
   changing what is being traded. A good third door turns a cooperative outcome that *was*
   unstable into one that is stable. Always try to reframe a contest as **positive-sum** before
   accepting that it is zero-sum.
6. **Sequence it.** What order of moves gets you there? What do you lock in before you give up
   leverage? Which commitment makes a threat credible?

---

## The rules that keep this honest

- **Never assert a threat the real BATNA cannot back.** If you would not actually walk, do not
  write that you would. The brief is for your own team; bluffing in it fools only you.
- **An equilibrium you cannot reach is not a recommendation.** Say so explicitly.
- **When the only account of events comes from one player, say so** and weight directly observed
  leverage over asserted intent.
- **Reframe to positive-sum first.** Most "us vs them" framings are a failure to look for the
  trade both sides would take.

---

## What the panel returns from this lens

```json
{
  "players": [{"name": "", "position": "", "interest": "", "batna": "", "leverage": ""}],
  "equilibria": [{"profile": "", "why_stable": "", "quality_for_owner": ""}],
  "natural_equilibrium": "", "recommended_equilibrium": "",
  "reachable": {"verdict": true, "why": ""},
  "third_doors": [], "sequencing": []
}
```

Plus the common envelope every lens returns: `recommendation`, `headline`, `confidence`,
`decisive_fact`, `members_used`, `kill_criteria`, `what_would_change_the_answer`.
