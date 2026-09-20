#!/usr/bin/env python3
"""Scorer for the pre-registered `pmf` skill eval.

Deliberately independent of anything the skill itself ships, so the skill cannot grade
itself. Every threshold here mirrors GOLD.md and must not be relaxed to make a run pass.

Usage:
    python3 score.py --structure                 # skill shape + PII checks
    python3 score.py --insights OUT.md           # score a `/pmf log` candidate output
    python3 score.py --insights OUT.md --negative-control
    python3 score.py --questions OUT.md          # score a `/pmf questions` candidate output
    python3 score.py --selftest                  # unit-test this scorer
    python3 score.py --all                       # structure + selftest (behavioural cases
                                                 # need a cold runner's output file)
Exit code 0 = every check attempted passed; 1 = at least one failed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
FIXTURES = HERE / "fixtures"

# --------------------------------------------------------------------------------------
# Pre-registered gold (mirrors GOLD.md section 3). Do not edit after pre-registration.
# --------------------------------------------------------------------------------------

GOLD = [
    {
        "id": "dies-in-weeks",
        "anchors": ["the techs stopped opening it after two weeks"],
        "keywords": [["two weeks", "2 weeks", "weeks"], ["stopped", "dead", "abandon"]],
    },
    {
        "id": "forced-use",
        "anchors": ["I made them use it. They never asked for it"],
        "keywords": [["made them", "forc", "never asked"]],
    },
    {
        "id": "dealer-stigma",
        "anchors": ["that's dealer software, not for independents"],
        "keywords": [["dealer"], ["independent"]],
    },
    {
        "id": "owner-overhead",
        "anchors": ["another thing that i'd have to manage"],
        "keywords": [["manage", "login", "babysit"]],
    },
    {
        "id": "counter-is-battery",
        "anchors": ["The counter guy is the battery",
                    "If I don't restock it they just walk around it"],
        "keywords": [["battery", "restock", "walk around"]],
    },
    {
        "id": "lunch-logistics",
        "anchors": ["I look at the board at lunch. Not because a car is stolen"],
        "keywords": [["lunch"], ["waiting", "stolen", "board"]],
    },
    {
        "id": "catalog-not-screen",
        "anchors": ["It's not the screen. It's that the parts catalog on it is a year old"],
        "keywords": [["catalog"], ["screen"]],
    },
    {
        "id": "texts-funnel",
        "anchors": ["Three or four parts texts a week. I ignore half"],
        "keywords": [["week"], ["half", "ignore", "three or four"]],
    },
    {
        "id": "emotional-blindness",
        "anchors": ["You're literally blind", "how the day went", "gonna, feel ashamed"],
        "keywords": [["blind", "shame"], ["day", "fine", "tell"]],
    },
    {
        "id": "post-pitch-contamination",
        "anchors": ["Two hundred a month would be a magic number", "Okay, sign me up",
                    "This was like a validation call"],
        "keywords": [["contaminat", "compliment", "after the pitch", "post-pitch",
                      "not evidence", "discard"]],
    },
]

ALTERNATES = [
    {"id": "advisor-wants-in",
     "anchors": ["I'd love to join this", "Put me on the cap table"],
     "keywords": [["join", "cap table", "advisor", "not neutral"]]},
]

GOLD_MIN = 8

COMPLIMENT_BLOCKLIST = [
    "Two hundred a month would be a magic number",
    "Okay, sign me up",
    "at least a fifty dollars pe",
    "A hundred percent yeah",
    "You're nailing it",
    "That would work yeah that would do it",
]
CONTAMINATION_HEADING = re.compile(
    r"contaminat|compliment|discard|excluded|not evidence|red flag|post-?pitch|fiction", re.I)

NUMBER_PATTERNS = {
    "two-weeks":        r"two weeks|2 weeks",
    "under-a-year":     r"less than a year|under a year|<\s*1 year|within a year",
    "parts-texts":      r"three or four|3\s*[-–]\s*4|3 or 4",
    "ignore-half":      r"ignore half|half",
    "year-old-catalog": r"year old",
    "six-bay":          r"6-bay|six-bay|6 bay",
}
NUMBERS_MIN = 4

STATUSES = ["VALIDATED", "REFUTED", "OPEN"]
HYPOTHESES_MIN = 6
NEXT_QUESTIONS_MIN = 8
LEARNED_REF_MIN = 2

QUESTIONS_MIN = 30
HYPOTHETICAL_MAX_RATIO = 0.20
HYPOTHETICAL_RE = re.compile(
    r"\b(would|could|usually|typically|generally|might|imagine|suppose|if you had|dream|on a scale)\b", re.I)
ANCHOR_RE = re.compile(
    r"\b(last time|last one|when did|walk me through|what did you|what happened|show me|the last)\b", re.I)

SKILL_MD_MAX_LINES = 200
REFERENCES_MIN = 3

# No real-person names belong under skills/pmf/. Keep this list empty in the
# public template; add operator-specific names locally if you freeze a private gold.
PERSONAL_NAMES: list[str] = []
PLAUD_TOKEN_RE = re.compile(r"pub_[0-9a-f-]{36}::")

WINDOW = 800  # chars of context around an anchor quote in which keywords must appear


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------

class Report:
    def __init__(self):
        self.rows: list[tuple[str, bool, str]] = []

    def add(self, name: str, ok: bool, detail: str = ""):
        self.rows.append((name, ok, detail))

    @property
    def ok(self) -> bool:
        return all(r[1] for r in self.rows)

    def render(self) -> str:
        out = []
        for name, ok, detail in self.rows:
            out.append(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
        n_pass = sum(1 for r in self.rows if r[1])
        out.append(f"\n{n_pass}/{len(self.rows)} checks passed")
        return "\n".join(out)


def _norm(s: str) -> str:
    """Normalise smart quotes/dashes so a candidate that re-typographs a quote still matches."""
    return (s.replace("’", "'").replace("‘", "'")
             .replace("“", '"').replace("”", '"')
             .replace("—", "-").replace("–", "-"))


def _find_item(text: str, item: dict) -> tuple[bool, str]:
    """An item is found iff an anchor appears verbatim AND every keyword group has a hit
    inside the surrounding window."""
    low = text.lower()
    for anchor in item["anchors"]:
        a = _norm(anchor).lower()
        idx = low.find(a)
        while idx != -1:
            lo, hi = max(0, idx - WINDOW), min(len(text), idx + len(a) + WINDOW)
            ctx = low[lo:hi]
            if all(any(k.lower() in ctx for k in group) for group in item["keywords"]):
                return True, f"anchor={anchor[:40]!r}"
            idx = low.find(a, idx + 1)
    return False, "no anchor+claim pairing"


def _headings(text: str) -> list[tuple[int, str]]:
    """(char offset, heading text) for markdown headings and bold-only lines."""
    out = []
    pos = 0
    for line in text.split("\n"):
        if re.match(r"\s*#{1,6}\s+\S", line) or re.match(r"\s*\*\*[^*]+\*\*\s*:?\s*$", line):
            out.append((pos, line))
        pos += len(line) + 1
    return out


def _questions(text: str) -> list[str]:
    qs = []
    for line in text.split("\n"):
        s = re.sub(r"^\s*(?:[-*+]|\d+\.)\s*", "", line).strip()
        s = re.sub(r"^\*\*(.*?)\*\*:?\s*", "", s).strip()
        s = s.strip("*_`> ")
        if s.endswith("?") and len(s) > 12:
            qs.append(s)
    return qs


# --------------------------------------------------------------------------------------
# scorers
# --------------------------------------------------------------------------------------

def score_insights(text: str, negative_control: bool = False) -> Report:
    r = Report()
    text = _norm(text)

    if negative_control:
        found = [g["id"] for g in GOLD if _find_item(text, g)[0]]
        # only contamination-awareness is legitimate here
        legit = {"post-pitch-contamination"}
        bad = [f for f in found if f not in legit]
        r.add("negative-control: no validated insights from post-pitch material",
              not bad, f"claimed: {bad}" if bad else "clean")
        r.add("negative-control: states the material is contaminated",
              bool(re.search(r"contaminat|post-pitch|after the pitch|not evidence", text, re.I)))
        laundered = [s for s in ("Two hundred a month", "sign me up", "fifty dollars")
                     if s.lower() in text.lower() and not _is_flagged(text, s)]
        r.add("negative-control: no pricing laundered into evidence",
              not laundered, f"laundered: {laundered}" if laundered else "")
        return r

    # --- gold extraction
    found, missing = [], []
    for g in GOLD:
        ok, _ = _find_item(text, g)
        (found if ok else missing).append(g["id"])
    alt = [a["id"] for a in ALTERNATES if _find_item(text, a)[0]]
    substitutions = min(1, len(alt), len(missing))
    effective = len(found) + substitutions
    r.add(f"gold insights >= {GOLD_MIN}/10", effective >= GOLD_MIN,
          f"{len(found)} gold + {substitutions} alt = {effective}; missing={missing}; alt_found={alt}")

    # --- compliment hygiene
    violations = [q for q in COMPLIMENT_BLOCKLIST
                  if _norm(q).lower() in text.lower() and not _is_flagged(text, q)]
    r.add("compliment-zone quotes used as evidence == 0", not violations,
          f"violations: {violations}" if violations else "clean")

    # --- contamination boundary named
    r.add("names call A's contamination boundary",
          bool(re.search(r"18:00|18 ?min|the pitch|post-?pitch", text, re.I)))

    # --- numbers
    hits = [k for k, p in NUMBER_PATTERNS.items() if re.search(p, text, re.I)]
    r.add(f"countables captured >= {NUMBERS_MIN}/6", len(hits) >= NUMBERS_MIN, f"found={hits}")

    # --- scoreboard
    rows = [l for l in text.split("\n") if any(s in l for s in STATUSES)]
    single = [l for l in rows if sum(l.count(s) for s in STATUSES) == 1]
    r.add(f"hypothesis scoreboard >= {HYPOTHESES_MIN} rows", len(single) >= HYPOTHESES_MIN,
          f"{len(single)} single-status rows")
    r.add("scoreboard contains at least one REFUTED", "REFUTED" in text)

    # --- next questions
    nq, learned = _next_questions(text)
    r.add(f"next-interview questions >= {NEXT_QUESTIONS_MIN}", len(nq) >= NEXT_QUESTIONS_MIN,
          f"{len(nq)} questions")
    r.add(f"next questions referencing what was learned >= {LEARNED_REF_MIN}",
          learned >= LEARNED_REF_MIN, f"{learned} referencing")

    # --- sampling bias
    r.add("flags sampling bias (all owners / independents)",
          bool(re.search(r"sampling bias|skew|all (three )?owners|independent shops only|no dealers", text, re.I)))
    r.add("notes the advisor/conflicted interviewee",
          bool(re.search(r"advis|wants to join|conflict|not neutral|biased", text, re.I)))

    return r


def _is_flagged(text: str, quote: str) -> bool:
    """True iff every occurrence of `quote` sits under a contamination-flagged heading."""
    low, q = text.lower(), _norm(quote).lower()
    heads = _headings(text)
    idx = low.find(q)
    while idx != -1:
        prior = [h for off, h in heads if off < idx]
        if not prior or not CONTAMINATION_HEADING.search(prior[-1]):
            # also accept an inline flag on the same or previous line
            line_start = low.rfind("\n", 0, idx) + 1
            prev_start = low.rfind("\n", 0, max(0, line_start - 1)) + 1
            if not CONTAMINATION_HEADING.search(text[prev_start:idx + len(q) + 120]):
                return False
        idx = low.find(q, idx + 1)
    return True


def _next_questions(text: str) -> tuple[list[str], int]:
    m = re.search(r"^#{1,6}.*(next (interview|call|round)|next questions|sharpened).*$",
                  text, re.I | re.M)
    section = text[m.start():] if m else ""
    qs = _questions(section)
    gold_words = ["dealer", "independent", "manage", "catalog", "parts text", "abandon",
                  "value", "blind", "shame", "lunch", "tablet", "two weeks",
                  "counter", "comeback"]
    learned = sum(1 for q in qs if any(w in q.lower() for w in gold_words))
    return qs, learned


def score_questions(text: str) -> Report:
    r = Report()
    text = _norm(text)
    qs = _questions(text)
    r.add(f"questions >= {QUESTIONS_MIN}", len(qs) >= QUESTIONS_MIN, f"{len(qs)} questions")

    bad = [q for q in qs if HYPOTHETICAL_RE.search(q) and not ANCHOR_RE.search(q)]
    ratio = len(bad) / len(qs) if qs else 1.0
    r.add(f"unanchored hypothetical ratio <= {HYPOTHETICAL_MAX_RATIO:.0%}",
          ratio <= HYPOTHETICAL_MAX_RATIO,
          f"{len(bad)}/{len(qs)} = {ratio:.0%}" + (f"; e.g. {bad[:3]}" if bad else ""))

    r.add("has a persona block",
          bool(re.search(r"^#{1,6}.*persona|^\*\*persona", text, re.I | re.M)))
    hyp = len(re.findall(r"^\s*(?:\||[-*]|\d+\.)?\s*(?:\[[ x]\]\s*)?\s*(?:H\d|hypothesis)", text, re.I | re.M))
    r.add("hypotheses >= 3", hyp >= 3, f"{hyp} hypothesis lines")
    return r


def score_structure() -> Report:
    r = Report()
    skill_md = SKILL_DIR / "SKILL.md"
    r.add("SKILL.md exists", skill_md.exists())
    if not skill_md.exists():
        return r
    text = skill_md.read_text()
    lines = text.split("\n")

    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    r.add("valid frontmatter block", bool(fm))
    if fm:
        body = fm.group(1)
        r.add("frontmatter name == pmf", bool(re.search(r"^name:\s*pmf\s*$", body, re.M)))
        r.add("frontmatter has non-empty description",
              bool(re.search(r"^description:\s*\S", body, re.M)))

    r.add(f"SKILL.md <= {SKILL_MD_MAX_LINES} lines", len(lines) <= SKILL_MD_MAX_LINES,
          f"{len(lines)} lines")

    refs = sorted((SKILL_DIR / "references").glob("*.md")) if (SKILL_DIR / "references").is_dir() else []
    r.add(f"references/ has >= {REFERENCES_MIN} files", len(refs) >= REFERENCES_MIN,
          f"{[p.name for p in refs]}")

    r.add("documents both runtimes (Claude Code + restricted sandbox)",
          bool(re.search(r"sandbox", text, re.I)) and bool(re.search(r"claude code|mcp", text, re.I)))
    r.add("MCP-dependent steps are guarded as optional",
          bool(re.search(r"(optional|if .{0,30}(unavailable|not available)|fall ?back|skip this step)",
                         text, re.I)))

    offenders = []
    for p in sorted(SKILL_DIR.rglob("*")):
        if not p.is_file() or "fixtures" in p.parts:
            continue
        try:
            t = p.read_text()
        except Exception:
            continue
        for n in PERSONAL_NAMES:
            if re.search(rf"\b{n}\b", t):
                offenders.append(f"{p.relative_to(SKILL_DIR)}:{n}")
    r.add("no personal names outside fixtures", not offenders, f"{offenders[:8]}" if offenders else "")

    tokens = [str(p.relative_to(SKILL_DIR)) for p in SKILL_DIR.rglob("*")
              if p.is_file() and _safe_read(p) and PLAUD_TOKEN_RE.search(_safe_read(p))]
    r.add("no Plaud share tokens committed", not tokens, f"{tokens}" if tokens else "")

    for name in ("call-A.md", "call-B.md", "call-C.md", "call-D-postpitch.md"):
        r.add(f"fixture present: {name}", (FIXTURES / name).exists())
    return r


def _safe_read(p: Path) -> str:
    try:
        return p.read_text()
    except Exception:
        return ""


# --------------------------------------------------------------------------------------
# selftest — proves the scorer discriminates
# --------------------------------------------------------------------------------------

GOOD = """## Insights
### 1. The tablet died in two weeks
The techs stopped opening it after two weeks — owner tool, not tech tool.
### 2. Use was coerced
"I made them use it. They never asked for it"
## Contamination (excluded — not evidence)
"Two hundred a month would be a magic number" arrived after the pitch at 18:00, so it is discarded.
Sampling bias: all three owners, independent shops only.
Advisor wants to join — not a buying signal.
## Next interview questions
- Walk me through the last parts text you ignored.
- When did a comeback last surprise you on Friday?
"""

BAD_COMPLIMENT = """## Insights
### Pricing
Shops will pay: "Two hundred a month would be a magic number" and "Okay, sign me up".
"""


def selftest() -> Report:
    r = Report()
    g = score_insights(GOOD)
    d = dict((n, ok) for n, ok, _ in g.rows)
    r.add("selftest: good sample passes compliment hygiene",
          d["compliment-zone quotes used as evidence == 0"])
    r.add("selftest: good sample names contamination boundary",
          d["names call A's contamination boundary"])
    b = score_insights(BAD_COMPLIMENT)
    db = dict((n, ok) for n, ok, _ in b.rows)
    r.add("selftest: laundered compliments are caught",
          not db["compliment-zone quotes used as evidence == 0"])
    r.add("selftest: thin sample fails the gold threshold",
          not db[f"gold insights >= {GOLD_MIN}/10"])

    qs_good = "\n".join([f"- Walk me through the last time you {i}?" for i in range(35)])
    r.add("selftest: past-tense bank passes the form check",
          all(ok for n, ok, _ in score_questions(qs_good).rows if "hypothetical" in n))
    qs_bad = "\n".join([f"- Would you use a device that {i}?" for i in range(35)])
    r.add("selftest: hypothetical bank fails the form check",
          not any(ok for n, ok, _ in score_questions(qs_bad).rows if "hypothetical" in n))

    anchored = "\n".join([f"- Would you say that is typical — and when did that last happen?"] * 35)
    r.add("selftest: anchored hypothetical is exempt",
          all(ok for n, ok, _ in score_questions(anchored).rows if "hypothetical" in n))
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--insights")
    ap.add_argument("--questions")
    ap.add_argument("--structure", action="store_true")
    ap.add_argument("--negative-control", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    reports: list[tuple[str, Report]] = []
    if a.structure or a.all:
        reports.append(("structure-and-portability", score_structure()))
    if a.selftest or a.all:
        reports.append(("scorer-selftest", selftest()))
    if a.insights:
        reports.append(("insights", score_insights(Path(a.insights).read_text(), a.negative_control)))
    if a.questions:
        reports.append(("questions", score_questions(Path(a.questions).read_text())))
    if not reports:
        ap.print_help()
        return 2

    if a.json:
        print(json.dumps({n: [{"check": c, "pass": ok, "detail": d} for c, ok, d in r.rows]
                          for n, r in reports}, indent=2))
    else:
        for n, r in reports:
            print(f"\n=== {n} ===\n{r.render()}")
    return 0 if all(r.ok for _, r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
