#!/usr/bin/env python3
"""Self-check for `/pmf` output. Standard library only — runs in the restricted sandbox.

    python3 pmf_lint.py questions BANK.md
    python3 pmf_lint.py insights INSIGHTS.md --transcript call-A.md [call-B.md …]

`questions` flags questions in unanchored hypothetical form (the Mom Test form filter) and
fails a bank where more than 20% are hypothetical.

`insights` verifies that every quoted string actually appears in one of the supplied
transcripts, that every insight record carries a quote and a "Changes:" line, and that no
compliment-zone quote is used outside the contamination section.

Exit 0 = clean, 1 = defects found, 2 = bad usage. Nothing is written or modified.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HYPOTHETICAL = re.compile(
    r"\b(would|could|usually|typically|generally|might|imagine|suppose|if you had|dream|on a scale)\b",
    re.I)
ANCHORED = re.compile(
    r"\b(last time|last one|when did|walk me through|what did you|what happened|show me|the last)\b",
    re.I)
MAX_HYPOTHETICAL_RATIO = 0.20
MIN_QUESTIONS = 30

CONTAMINATION_HEADING = re.compile(
    r"contaminat|compliment|discard|excluded|not evidence|red flag", re.I)

# Quotes are matched loosely: transcripts are full of disfluency, so a candidate quote counts as
# grounded if a 40-character window of it appears verbatim after whitespace normalisation.
MIN_QUOTE_LEN = 12
FUZZ_WINDOW = 40


def _norm(s: str) -> str:
    s = (s.replace("’", "'").replace("‘", "'")
          .replace("“", '"').replace("”", '"')
          .replace("—", "-").replace("–", "-"))
    return re.sub(r"\s+", " ", s).strip()


def _questions(text: str) -> list[tuple[int, str]]:
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        s = re.sub(r"^\s*(?:[-*+]|\d+\.)\s*", "", line).strip()
        s = re.sub(r"^\*\*(.*?)\*\*:?\s*", "", s).strip().strip("*_`> ")
        if s.endswith("?") and len(s) > MIN_QUOTE_LEN:
            out.append((i, s))
    return out


def lint_questions(path: Path) -> int:
    text = path.read_text()
    qs = _questions(text)
    bad = [(n, q) for n, q in qs if HYPOTHETICAL.search(q) and not ANCHORED.search(q)]
    ratio = len(bad) / len(qs) if qs else 1.0

    print(f"questions: {len(qs)}")
    print(f"unanchored hypotheticals: {len(bad)} ({ratio:.0%}, limit {MAX_HYPOTHETICAL_RATIO:.0%})")
    for n, q in bad:
        print(f"  line {n}: {q}")

    fail = False
    if len(qs) < MIN_QUESTIONS:
        print(f"FAIL: only {len(qs)} questions, want >= {MIN_QUESTIONS}")
        fail = True
    if ratio > MAX_HYPOTHETICAL_RATIO:
        print("FAIL: rewrite the flagged questions into past-behaviour form, "
              "or anchor each one to a specific past instance in the same line")
        fail = True
    if not re.search(r"^#{1,6}.*persona|^\*\*persona", text, re.I | re.M):
        print("FAIL: no persona block — a bank that is not persona-locked mixes segments")
        fail = True
    if not fail:
        print("OK")
    return 1 if fail else 0


def _blocks(text: str) -> list[tuple[str, str]]:
    """(nearest preceding heading, block text) for every markdown heading section."""
    parts = re.split(r"^(#{1,6} .*)$", text, flags=re.M)
    out, head = [], ""
    for i, p in enumerate(parts):
        if re.match(r"^#{1,6} ", p):
            head = p
        elif p.strip():
            out.append((head, p))
    return out


def lint_insights(path: Path, transcripts: list[Path]) -> int:
    text = path.read_text()
    corpus = _norm(" ".join(t.read_text() for t in transcripts)) if transcripts else ""
    fail = False

    quotes = [(h, q) for h, blk in _blocks(text)
              for q in re.findall(r'"([^"]{%d,})"' % MIN_QUOTE_LEN, blk)]
    print(f"quoted strings: {len(quotes)}")

    if corpus:
        ungrounded = []
        for _, q in quotes:
            n = _norm(q)
            probe = n[:FUZZ_WINDOW] if len(n) > FUZZ_WINDOW else n
            if probe.lower() not in corpus.lower():
                ungrounded.append(q)
        if ungrounded:
            fail = True
            print(f"FAIL: {len(ungrounded)} quote(s) not found in any supplied transcript "
                  f"— paraphrase is not evidence:")
            for q in ungrounded[:10]:
                print(f'  "{q[:90]}"')
        else:
            print("all quotes grounded in a transcript")
    else:
        print("WARN: no --transcript given; quote grounding not checked")

    # every insight record needs a quote and a decision
    records = re.findall(r"^###\s+(I-\d+.*?)$(.*?)(?=^###\s|\Z)", text, re.M | re.S)
    print(f"insight records: {len(records)}")
    for title, body in records:
        if not re.search(r'"[^"]{%d,}"' % MIN_QUOTE_LEN, body):
            print(f"FAIL: {title.strip()} has no verbatim quote")
            fail = True
        if not re.search(r"\*\*Changes:\*\*\s*\S", body):
            print(f"FAIL: {title.strip()} has no **Changes:** line — it is a summary, not an insight")
            fail = True

    # contamination hygiene: quotes attributed to a post-pitch timestamp must sit in the
    # contamination section
    if re.search(r"^##\s*Contaminated", text, re.M | re.I):
        print("contamination section present")
    else:
        print("FAIL: no 'Contaminated — not evidence' section. Every call has a boundary; "
              "state it even if the answer is 'the interviewer never pitched'")
        fail = True

    # a scoreboard that never refutes is not testing anything
    if "REFUTED" not in text and not any("REFUTED" in Path(p).read_text()
                                         for p in [path.parent / "SCOREBOARD.md"]
                                         if Path(p).exists()):
        print("WARN: nothing REFUTED anywhere — check you are testing, not confirming")

    if not fail:
        print("OK")
    return 1 if fail else 0


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in ("questions", "insights"):
        print(__doc__)
        return 2
    mode, target = argv[1], Path(argv[2])
    if not target.exists():
        print(f"no such file: {target}")
        return 2
    if mode == "questions":
        return lint_questions(target)
    transcripts = [Path(p) for p in argv[argv.index("--transcript") + 1:]] \
        if "--transcript" in argv else []
    missing = [p for p in transcripts if not p.exists()]
    if missing:
        print(f"no such transcript(s): {missing}")
        return 2
    return lint_insights(target, transcripts)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
