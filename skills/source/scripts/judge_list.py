#!/usr/bin/env python3
"""
Blind A-bar judge.

Grades a candidate list against the A-bar legs of a scorecard, using a model
from a DIFFERENT family than the one that produced the list (default gpt-5.6
via OPENAI_API_KEY). The judge is never told which system produced the list,
that anything is being evaluated, or what the pass threshold is — it only sees
the scorecard legs and the entries.

    judge_list.py --list candidates.md --scorecard evals/GOLD.md
    judge_list.py --list candidates.md --scorecard evals/GOLD.md --runs 3 --json out.json

Exit codes: 0 = judged (read the printed A-count), 2 = setup problem
(no key, no legs, unparseable list). It does NOT decide pass/fail — the
threshold lives in the pre-registered eval, not here.

Standard library only: talks to the API over urllib.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

DEFAULT_MODEL = "gpt-5.6"
ENDPOINT = "https://api.openai.com/v1/chat/completions"

SYSTEM = (
    "You grade candidate write-ups against a fixed hiring bar. You are strict and "
    "literal. Evidence must be quoted verbatim from the entry you are grading. If "
    "the entry does not state something, it is UNSUPPORTED — never infer it, never "
    "give the benefit of the doubt, never reason from a company name or a job title "
    "to a capability. Reply with JSON only."
)

TEMPLATE = """Below is a hiring bar made of numbered legs, then a list of candidate entries.

HIRING BAR
{legs}

CANDIDATE ENTRIES
{entries}

For every entry, decide each leg independently:
- "PASS" only if the entry contains an explicit statement satisfying that leg. Quote it.
- "FAIL" if the entry contains a statement that contradicts the leg.
- "UNSUPPORTED" if the entry simply does not say.

grade = "A" only if every leg is PASS. Otherwise "HOLD" if exactly one leg is not PASS,
"REJECT" if two or more are not PASS.

Reply with JSON exactly of this shape and nothing else:
{{"candidates": [{{"name": "...", "legs": {{"L1": {{"verdict": "PASS|FAIL|UNSUPPORTED", "quote": "..."}}, ...}}, "grade": "A|HOLD|REJECT"}}]}}
"""


def extract_legs(scorecard: str):
    """Frozen protocol (GOLD.md SS3): the judge receives SS1.1-SS1.4 of the scorecard
    VERBATIM - including the evidence-definition column. GOLD SS3 (the pre-registered
    document) governs over any code that disagrees; ambiguity flagged for next freeze."""
    m = re.search(r"(###? 1\.1.*?)(?=\n###? 1\.5|\n## 2|\Z)", scorecard, re.S)
    if m:
        return [m.group(1).strip()]
    legs = []
    for mm in re.finditer(r"^\|\s*\*{0,2}(L\d+)[^|*]*\*{0,2}\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", scorecard, re.M):
        legs.append(f"{mm.group(1)}: {mm.group(2).strip()}  [evidence that counts: {mm.group(3).strip()}]")
    return legs


def split_entries(md: str):
    """Each `### ` heading is one candidate entry."""
    chunks = re.split(r"^###\s+", md, flags=re.M)[1:]
    return [("### " + c).strip() for c in chunks if c.strip()]


def _post(body: dict, key: str) -> dict:
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def call_model(model: str, key: str, prompt: str, temperature: float | None) -> tuple[str, bool]:
    """Returns (content, temperature_honoured). Newer reasoning models reject any
    temperature but their default; when that happens we drop the parameter and
    lean on the multi-run majority vote instead of pretending determinism."""
    body = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }
    if temperature is not None:
        body["temperature"] = temperature
    try:
        return _post(body, key)["choices"][0]["message"]["content"], temperature is not None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        if e.code == 400 and "temperature" in detail and temperature is not None:
            print(f"  ~ {model} rejects temperature={temperature}; retrying at the model default. "
                  "Determinism now rests on the multi-run majority vote.", file=sys.stderr)
            body.pop("temperature")
            return _post(body, key)["choices"][0]["message"]["content"], False
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", dest="list_path", required=True, help="candidate list markdown")
    ap.add_argument("--scorecard", required=True, help="file containing the A-bar legs")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--runs", type=int, default=3, help="independent runs; majority vote per candidate")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--json", dest="json_out", help="write the full verdict here")
    ap.add_argument("--print-prompt", action="store_true", help="show the exact blind prompt and exit (no API call)")
    args = ap.parse_args()

    legs = extract_legs(Path(args.scorecard).expanduser().read_text())
    if not legs:
        print("ERROR: no A-bar legs (L1, L2, ...) found in the scorecard.", file=sys.stderr)
        return 2
    entries = split_entries(Path(args.list_path).expanduser().read_text())
    if not entries:
        print("ERROR: no candidate entries found — entries must be '### ' headings.", file=sys.stderr)
        return 2

    prompt = TEMPLATE.format(legs="\n".join(legs), entries="\n\n".join(entries))
    if args.print_prompt:
        print(prompt)
        return 0

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        print("ERROR: OPENAI_API_KEY not set — cannot run the judge.", file=sys.stderr)
        return 2

    runs, temp_honoured = [], True
    for i in range(args.runs):
        try:
            content, honoured = call_model(args.model, key, prompt, args.temperature)
            temp_honoured = temp_honoured and honoured
            runs.append(json.loads(content))
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as e:
            detail = ""
            if isinstance(e, urllib.error.HTTPError):
                detail = f" — {e.read()[:300].decode('utf-8', 'replace')}"
            print(f"ERROR: judge run {i + 1} failed: {e}{detail}", file=sys.stderr)
            return 2

    votes = Counter()
    names = []
    for r in runs:
        for c in r.get("candidates", []):
            n = c.get("name", "?")
            if n not in names:
                names.append(n)
            votes[(n, c.get("grade"))] += 1

    final = {}
    for n in names:
        grades = {g: votes[(n, g)] for g in ("A", "HOLD", "REJECT") if votes[(n, g)]}
        top = max(grades.items(), key=lambda kv: kv[1]) if grades else ("REJECT", 0)
        # a tie is not a majority for A
        if top[0] == "A" and top[1] <= args.runs / 2:
            top = ("HOLD", top[1])
        final[n] = top[0]

    a_count = sum(1 for g in final.values() if g == "A")
    for n in names:
        print(f"{final[n]:<7} {n}")
    temp_note = args.temperature if temp_honoured else "model default (temperature not settable)"
    print(f"\nA-grade: {a_count}/{len(names)}  (model={args.model}, runs={args.runs}, temp={temp_note})")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(
            {"model": args.model, "runs": runs, "final": final, "a_count": a_count,
             "n": len(names), "legs": legs,
             "temperature_honoured": temp_honoured}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
