#!/usr/bin/env python3
"""
Eval runner for the `decide` skill.

Three tiers, all driven by the pre-registered evals/cases.json:

  static   deterministic string/regex checks against the skill's own artifacts.
           No model, no network.
  runtime  executes scripts/panel.py and scripts/ledger.py against the frozen
           fixtures in evals/fixtures/, then checks the produced artifacts and
           the model-call run log.
  judge    replays the 5 synthetic historical decisions, hands the produced brief
           plus the frozen known-good outcome to gpt-5.6-sol, and requires a
           score >= 4.0 out of 5 on every case.

Scoring semantics are frozen here on purpose (committed with GOLD.md, before the
skill was written) so they cannot be quietly loosened later. Any expectation key
that this runner does not understand is reported as a FAILURE, never a pass.

Usage:
    python3 evals/run.py --all
    python3 evals/run.py --static
    python3 evals/run.py --runtime --judge --rundir evals/results/run-x
    python3 evals/run.py --all --markdown        # emit the RESULTS.md table
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CASES_PATH = SKILL_DIR / "evals" / "cases.json"

STATIC_KEYS = {"contains", "must_not_contain", "regex", "regex_not",
               "max_lines", "min_lines", "files_exist"}
RUNTIME_KEYS = {"contains", "must_not_contain", "regex", "regex_not",
                "jsonl_ok_models", "jsonl_ok_pairs", "member_coverage_all"}
JUDGE_KEYS = {"llm_judge"}


# ---------------------------------------------------------------- environment
def load_env() -> None:
    """Populate provider keys from ~/.claude/.env if not already in the env."""
    dotenv = Path.home() / ".claude" / ".env"
    if not dotenv.exists():
        return
    for line in dotenv.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


# ------------------------------------------------------------------- checking
def _as_list(v):
    return [v] if isinstance(v, str) else list(v)


def apply_checks(expected: dict, text: str, cases_meta: dict) -> list[str]:
    """Return a list of failure strings; empty means pass."""
    fails: list[str] = []
    low = text.lower()

    for s in _as_list(expected.get("contains", [])):
        if s.lower() not in low:
            fails.append(f"contains: missing {s!r}")

    for s in _as_list(expected.get("must_not_contain", [])):
        if s.lower() in low:
            fails.append(f"must_not_contain: forbidden {s!r} present")

    for pat in _as_list(expected.get("regex", [])):
        resolved = cases_meta.get(pat[1:]) if pat.startswith("@") else pat
        if resolved is None:
            fails.append(f"regex: unresolved reference {pat!r}")
            continue
        if not re.search(resolved, text, re.M):
            fails.append(f"regex: no match for {resolved!r}")

    for pat in _as_list(expected.get("regex_not", [])):
        resolved = cases_meta.get(pat[1:]) if pat.startswith("@") else pat
        if resolved is None:
            fails.append(f"regex_not: unresolved reference {pat!r}")
            continue
        m = re.search(resolved, text, re.M)
        if m:
            fails.append(f"regex_not: forbidden match {m.group(0)!r}")

    if "max_lines" in expected:
        n = len(text.splitlines())
        if n > expected["max_lines"]:
            fails.append(f"max_lines: {n} > {expected['max_lines']}")

    if "min_lines" in expected:
        n = len(text.splitlines())
        if n < expected["min_lines"]:
            fails.append(f"min_lines: {n} < {expected['min_lines']}")

    for rel in expected.get("files_exist", []):
        if not (SKILL_DIR / rel).exists():
            fails.append(f"files_exist: missing {rel}")

    return fails


def check_jsonl_ok_models(path: Path, models: list[str]) -> list[str]:
    if not path.exists():
        return [f"log not found: {path}"]
    ok = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            return [f"log line is not JSON: {line[:80]}"]
        if rec.get("status") == "ok":
            ok.add(rec.get("model"))
    missing = [m for m in models if m not in ok]
    return [f"jsonl_ok_models: no ok call logged for {missing}"] if missing else []


def check_jsonl_ok_pairs(path: Path, pairs: list[list[str]]) -> list[str]:
    if not path.exists():
        return [f"log not found: {path}"]
    ok = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("status") == "ok":
            ok.add((rec.get("model"), rec.get("lens")))
    missing = [p for p in pairs if tuple(p) not in ok]
    return [f"jsonl_ok_pairs: missing ok calls for {missing}"] if missing else []


def check_member_coverage(path: Path, members: list[str]) -> list[str]:
    if not path.exists():
        return [f"artifact not found: {path}"]
    data = json.loads(path.read_text())
    cov = data.get("member_coverage") or {}
    fails = []
    for m in members:
        entry = cov.get(m)
        if not entry or not entry.get("referenced_by"):
            fails.append(f"member_coverage_all: {m!r} not referenced by any model")
    return fails


# --------------------------------------------------------------------- static
def collect_target_text(target: str) -> tuple[str, str | None]:
    """Return (text, error). Supports a single path or comma-separated globs."""
    if any(ch in target for ch in "*,"):
        chunks = []
        for pat in target.split(","):
            for p in sorted(SKILL_DIR.glob(pat.strip())):
                if p.is_file():
                    chunks.append(f"\n===== {p.relative_to(SKILL_DIR)} =====\n"
                                  + p.read_text(errors="replace"))
        if not chunks:
            return "", f"no files matched {target}"
        return "\n".join(chunks), None
    p = SKILL_DIR / target
    if not p.exists():
        return "", f"target not found: {target}"
    return p.read_text(errors="replace"), None


def run_static(cases, cases_meta, results):
    for c in cases:
        expected = c.get("expected", {})
        unsupported = set(expected) - STATIC_KEYS
        if unsupported:
            results.append((c["id"], "FAIL",
                            [f"unsupported static keys {sorted(unsupported)}"]))
            continue
        target = c["input"].get("target", "SKILL.md")
        # files_exist does not need target content
        if set(expected) == {"files_exist"}:
            fails = apply_checks(expected, "", cases_meta)
            results.append((c["id"], "PASS" if not fails else "FAIL", fails))
            continue
        text, err = collect_target_text(target)
        if err:
            results.append((c["id"], "FAIL", [err]))
            continue
        fails = apply_checks(expected, text, cases_meta)
        results.append((c["id"], "PASS" if not fails else "FAIL", fails))


# -------------------------------------------------------------------- runtime
def run_shell(cmd: str, rundir: Path, unset: list[str] | None = None):
    # shell=True is deliberate and safe here: the command strings come only from the
    # committed, pre-registered cases.json in this repo, never from user input. Cases
    # need shell quoting (e.g. --decision 'text with spaces'), so a list-form exec
    # would force every case to carry an argv array.
    env = dict(os.environ)
    env["RUNDIR"] = str(rundir)
    for k in unset or []:
        env.pop(k, None)
    cmd = cmd.replace("$RUNDIR", str(rundir))
    proc = subprocess.run(cmd, shell=True, cwd=SKILL_DIR, env=env,
                          capture_output=True, text=True, timeout=1200)
    return proc


def run_runtime(cases, cases_meta, rundir: Path, results):
    rundir.mkdir(parents=True, exist_ok=True)
    ran: dict[str, subprocess.CompletedProcess] = {}

    for c in cases:
        cid = c["id"]
        expected = c.get("expected", {})
        inp = c["input"]
        unsupported = set(expected) - RUNTIME_KEYS
        if unsupported:
            results.append((cid, "FAIL", [f"unsupported runtime keys {sorted(unsupported)}"]))
            continue

        proc = None
        if "run" in inp:
            try:
                proc = run_shell(inp["run"], rundir, inp.get("unset_env"))
            except subprocess.TimeoutExpired:
                results.append((cid, "FAIL", ["command timed out"]))
                continue
            ran[cid] = proc
            want_nonzero = bool(inp.get("expect_exit_nonzero"))
            if want_nonzero and proc.returncode == 0:
                results.append((cid, "FAIL", ["expected non-zero exit, got 0"]))
                continue
            if not want_nonzero and proc.returncode != 0:
                results.append((cid, "FAIL",
                                [f"exit {proc.returncode}: {(proc.stderr or proc.stdout)[-400:]}"]))
                continue

        # Resolve the text under test.
        fails: list[str] = []
        artifact = inp.get("artifact")
        text = ""
        if artifact:
            apath = Path(artifact.replace("$RUNDIR", str(rundir)))
            if not apath.exists():
                results.append((cid, "FAIL", [f"artifact not found: {apath}"]))
                continue
            raw = apath.read_text()
            if "json_field" in inp:
                try:
                    text = str(json.loads(raw)[inp["json_field"]])
                except (json.JSONDecodeError, KeyError) as e:
                    results.append((cid, "FAIL", [f"json_field {inp['json_field']}: {e}"]))
                    continue
            else:
                text = raw
        elif proc is not None:
            text = (proc.stdout or "") + (proc.stderr or "")

        checkable = {k: v for k, v in expected.items()
                     if k in {"contains", "must_not_contain", "regex", "regex_not"}}
        fails += apply_checks(checkable, text, cases_meta)

        if "jsonl_ok_models" in expected:
            p = Path((artifact or "").replace("$RUNDIR", str(rundir)))
            fails += check_jsonl_ok_models(p, expected["jsonl_ok_models"])
        if "jsonl_ok_pairs" in expected:
            p = Path((artifact or "").replace("$RUNDIR", str(rundir)))
            fails += check_jsonl_ok_pairs(p, expected["jsonl_ok_pairs"])
        if "member_coverage_all" in expected:
            p = Path((artifact or "").replace("$RUNDIR", str(rundir)))
            fails += check_member_coverage(p, expected["member_coverage_all"])

        results.append((cid, "PASS" if not fails else "FAIL", fails))


# ---------------------------------------------------------------------- judge
JUDGE_SYSTEM = """You are grading the output of a decision-making framework against a known-good
historical outcome. You are strict, and you do not reward eloquence.

Score 1-5:
5 = reaches the known-good call AND names the decisive fact as decisive; states kill criteria or
    what would change the answer; uses the named team members' actual inputs; honest about uncertainty.
4 = reaches the known-good call and identifies the decisive fact, with minor gaps.
3 = plausible reasoning but either misses the decisive fact, or lands on a materially different
    call without engaging the known-good option.
2 = wrong call; the reasoning does not engage the decisive structural fact.
1 = wrong call plus confident errors or facts not present in the input.

Adjacent-call rule: a brief recommending MODIFY where the known-good is a counter-offer of that
same substance counts as reaching the known-good call. A brief recommending DEFER where the
known-good is a decision does NOT count as reaching it.

Return STRICT JSON only: {"score": <number 1-5>, "reasoning": "<2-4 sentences>"}"""


def call_judge(model: str, fixture: dict, brief: str) -> tuple[float | None, str]:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None, "OPENAI_API_KEY not set"
    public = {k: v for k, v in fixture.items() if k != "known_good"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content":
                "## The decision as presented to the framework\n"
                + json.dumps(public, indent=2)
                + "\n\n## Known-good outcome (ground truth, hidden from the framework)\n"
                + json.dumps(fixture["known_good"], indent=2)
                + "\n\n## The brief the framework produced\n" + brief},
        ],
        "max_completion_tokens": 4000,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            body = json.loads(r.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return None, f"judge call failed: {e}"
    text = body["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None, f"unparseable judge output: {text[:200]}"
    try:
        obj = json.loads(m.group(0))
        return float(obj["score"]), str(obj.get("reasoning", ""))[:400]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return None, f"unparseable judge JSON: {e}"


def run_judge(cases, rundir: Path, results, scores: dict):
    rundir.mkdir(parents=True, exist_ok=True)
    for c in cases:
        cid = c["id"]
        expected = c.get("expected", {})
        unsupported = set(expected) - JUDGE_KEYS
        if unsupported:
            results.append((cid, "FAIL", [f"unsupported judge keys {sorted(unsupported)}"]))
            continue
        spec = expected["llm_judge"]
        fixture_path = SKILL_DIR / c["input"]["fixture"]
        fixture = json.loads(fixture_path.read_text())

        case_dir = rundir / cid
        case_dir.mkdir(parents=True, exist_ok=True)
        # Strip the ground truth before the panel ever sees it.
        stripped = case_dir / "input.json"
        stripped.write_text(json.dumps({k: v for k, v in fixture.items()
                                        if k != "known_good"}, indent=2))
        proc = run_shell(
            f"python3 scripts/panel.py --decision-file {stripped} --out {case_dir}",
            rundir)
        brief_path = case_dir / "brief.md"
        if proc.returncode != 0 or not brief_path.exists():
            results.append((cid, "FAIL",
                            [f"panel failed (exit {proc.returncode}): "
                             f"{(proc.stderr or proc.stdout)[-400:]}"]))
            continue

        score, reason = call_judge(spec.get("model", "gpt-5.6-sol"), fixture,
                                   brief_path.read_text())
        if score is None:
            results.append((cid, "PENDING", [reason]))
            continue
        scores[cid] = score
        (case_dir / "judge.json").write_text(
            json.dumps({"score": score, "reasoning": reason}, indent=2))
        threshold = float(spec.get("min_score", 4.0))
        status = "PASS" if score >= threshold else "FAIL"
        results.append((cid, status, [f"score {score}/5 (>= {threshold}) — {reason}"]))


# --------------------------------------------------------------------- driver
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true")
    ap.add_argument("--runtime", action="store_true")
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--rundir", default=None)
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--only", default=None, help="comma-separated case ids")
    args = ap.parse_args()

    if args.all:
        args.static = args.runtime = args.judge = True
    if not (args.static or args.runtime or args.judge):
        args.static = True

    load_env()
    data = json.loads(CASES_PATH.read_text())
    cases_meta = {k: v for k, v in data.items() if isinstance(v, str)}
    cases = data["cases"]
    if args.only:
        want = {s.strip() for s in args.only.split(",")}
        cases = [c for c in cases if c["id"] in want]

    rundir = Path(args.rundir) if args.rundir else \
        SKILL_DIR / "evals" / "results" / time.strftime("run-%Y%m%d-%H%M%S")

    results: list[tuple[str, str, list[str]]] = []
    scores: dict[str, float] = {}

    if args.static:
        run_static([c for c in cases if c["tier"] == "static"], cases_meta, results)
    if args.runtime:
        run_runtime([c for c in cases if c["tier"] == "runtime"], cases_meta, rundir, results)
    if args.judge:
        run_judge([c for c in cases if c["tier"] == "judge"], rundir, results, scores)

    order = {c["id"]: i for i, c in enumerate(cases)}
    results.sort(key=lambda r: order.get(r[0], 999))

    npass = sum(1 for _, s, _ in results if s == "PASS")
    nfail = sum(1 for _, s, _ in results if s == "FAIL")
    npend = sum(1 for _, s, _ in results if s == "PENDING")

    if args.markdown:
        print(f"\n| Case | Result | Detail |\n|---|---|---|")
        for cid, status, notes in results:
            detail = "; ".join(notes).replace("|", "/").replace("\n", " ")[:220] or "—"
            print(f"| `{cid}` | {status} | {detail} |")
    else:
        print("=" * 72)
        print("decide — eval run")
        print(f"rundir: {rundir}")
        print("=" * 72)
        for cid, status, notes in results:
            mark = {"PASS": "PASS", "FAIL": "FAIL", "PENDING": "PEND"}[status]
            print(f"[{mark}] {cid}")
            for n in notes:
                print(f"       {n}")
    if scores:
        print(f"\njudge mean: {sum(scores.values()) / len(scores):.2f}/5")
    print(f"\n{npass} pass / {nfail} fail / {npend} pending  (rundir: {rundir})")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
