#!/usr/bin/env python3
"""Deterministic acceptance runner for the /build skill rebuild.

Pre-registered BEFORE the rebuilt skill was written: every check below was frozen against
GOLD.md, not fitted to whatever the implementation happened to produce.

Usage:
    python3 run_checks.py                      # run all shell-runner cases, print table
    python3 run_checks.py --only <case-id> --raw   # print that case's tokens, exit 0/1
    python3 run_checks.py --json               # machine-readable
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent          # skills/build
REPO = SKILL.parent.parent                               # repo root
SKILL_MD = SKILL / "SKILL.md"
REFS = SKILL / "references"
SCRIPTS = SKILL / "scripts"
BENCH = SKILL / "evals" / "benchmarks"
FIXTURES = BENCH / "fixtures"

CHECKS: dict[str, callable] = {}


def check(case_id: str):
    def deco(fn):
        CHECKS[case_id] = fn
        return fn
    return deco


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def skill_text() -> str:
    return read(SKILL_MD)


def doc_surface() -> list[Path]:
    """The skill's *instructional* surface: the files that tell an agent what to do.

    Deliberately excludes evals/ — a guarantee has to be made by the skill, not by the
    document that grades the skill. Scoping here makes the safety and runtime checks
    strictly harder to satisfy than scanning the whole tree would.
    """
    docs = [SKILL_MD] if SKILL_MD.exists() else []
    if REFS.is_dir():
        docs += sorted(REFS.glob("*.md"))
    return docs


def all_tree_files() -> list[Path]:
    out = []
    for p in SKILL.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".sh", ".py", ".json", ".txt", ""}:
            out.append(p)
    return sorted(out)


def markdown_tables(text: str):
    """Yield (header_cells, [row_cells...]) for every pipe table."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            if len(block) >= 2:
                header = [c.strip() for c in block[0].strip("|").split("|")]
                rows = []
                for r in block[2:]:
                    rows.append([c.strip() for c in r.strip("|").split("|")])
                yield header, rows
        else:
            i += 1


# ---------------------------------------------------------------- structure

@check("skill-md-has-phase-routing-table")
def _routing_table_in_skill_md():
    toks, ok = [], False
    for header, rows in markdown_tables(skill_text()):
        h = " | ".join(header).lower()
        if "phase" in h and "skill" in h and "skip" in h and rows:
            ok = True
            toks = ["Phase", "Skill to invoke", "Skip when", f"phase_rows={len(rows)}"]
            break
    if not ok:
        toks = ["routing_table_in_skill_md=MISSING"]
    return ok, toks


@check("skill-md-frontmatter-and-size")
def _frontmatter():
    text = skill_text()
    toks, ok = [], True
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return False, ["frontmatter=MISSING"]
    fm = m.group(1)
    name = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
    if name and name.group(1) == "build":
        toks.append("name=build")
    else:
        ok = False
        toks.append("name=BAD")
    desc = re.search(r"^description:\s*(.+)$", fm, re.M)
    if desc and len(desc.group(1).strip()) >= 40:
        toks.append("description=ok")
    else:
        ok = False
        toks.append("description=BAD")
    n = len(text.splitlines())
    toks.append(f"lines<=300" if n <= 300 else f"lines={n}")
    if n > 300:
        ok = False
    return ok, toks


@check("progressive-disclosure-references-resolve")
def _refs_resolve():
    text = skill_text()
    mentioned = set(re.findall(r"(?:references|scripts)/[A-Za-z0-9_.\-/]+", text))
    dead = sorted(m for m in mentioned if not (SKILL / m).exists())
    on_disk = {p.relative_to(SKILL).as_posix() for p in REFS.glob("*.md")} if REFS.is_dir() else set()
    orphans = sorted(on_disk - mentioned)
    toks = [f"dead_links={len(dead)}", f"orphan_references={len(orphans)}"]
    if dead:
        toks.append("DEAD:" + ",".join(dead))
    if orphans:
        toks.append("ORPHANS:" + ",".join(orphans))
    return (not dead and not orphans), toks


# ---------------------------------------------------------------- functional

@check("tdd-is-the-spine")
def _tdd_spine():
    routing = read(REFS / "routing.md")
    never = False
    for header, rows in markdown_tables(routing):
        idx = next((i for i, c in enumerate(header) if "skip" in c.lower()), None)
        if idx is None:
            continue
        for row in rows:
            if idx < len(row) and "test-driven-development" in " ".join(row):
                if re.search(r"never|non-?skippable|no exception", row[idx], re.I):
                    never = True
    law = bool(re.search(
        r"no production code without .{0,20}failing test|"
        r"never write production code before a failing test",
        skill_text(), re.I))
    toks = [f"tdd_never_skipped={'true' if never else 'false'}",
            f"iron_law_present={'true' if law else 'false'}"]
    return (never and law), toks


@check("acceptance-pre-registered-before-implementation")
def _acceptance_first():
    text = skill_text()
    before = bool(re.search(
        r"(ACCEPTANCE(\.md)?[^.\n]{0,120}?before[^.\n]{0,60}(implementation|any code|writing code|first line of code))"
        r"|(before[^.\n]{0,60}(implementation|any code|writing code)[^.\n]{0,120}?ACCEPTANCE)",
        text, re.I | re.S))
    eval_ref = bool(re.search(r"/eval\b|skills/eval", text))
    cases = "cases.json" in text
    toks = [f"acceptance_before_impl={'true' if before else 'false'}",
            f"eval_format_referenced={'true' if eval_ref else 'false'}",
            f"cases_json_mandated={'true' if cases else 'false'}"]
    return (before and eval_ref and cases), toks


@check("loop-driver-documented")
def _loop_driver():
    text = skill_text() + "\n" + read(REFS / "loop-driver.md")
    loop_pattern = bool(re.search(r"/loop\b", text))
    fallback = bool(re.search(r"```bash[^`]*?\b(while|for)\b[^`]*?```", text, re.S))
    maxit = bool(re.search(r"max[_ -]?iterations?", text, re.I))
    stuck = bool(re.search(r"stuck|same (error|failure) \d+|no progress", text, re.I))
    toks = [f"loop_pattern={'true' if loop_pattern else 'false'}",
            f"shell_fallback={'true' if fallback else 'false'}",
            f"max_iterations={'true' if maxit else 'false'}",
            f"stuck_detection={'true' if stuck else 'false'}"]
    return all([loop_pattern, fallback, maxit, stuck]), toks


def _scaffold(tmp: Path) -> tuple[int, str, Path]:
    init = SCRIPTS / "build_init.sh"
    if not init.exists():
        return 127, "build_init.sh missing", tmp
    proc = subprocess.run(["bash", str(init), "demo-slug"], cwd=tmp,
                          capture_output=True, text=True, timeout=120)
    return proc.returncode, proc.stdout + proc.stderr, tmp / ".build" / "demo-slug"


@check("build-init-emits-acceptance-and-loop-driver")
def _init_emits():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        rc, out, run_dir = _scaffold(tmp)
        toks, ok = [], rc == 0
        if rc != 0:
            return False, [f"build_init_exit={rc}", out.strip()[:200]]
        wants = {
            "ACCEPTANCE.md": run_dir / "ACCEPTANCE.md",
            "cases.json": run_dir / "evals" / "cases.json",
            "loop.sh": run_dir / "loop.sh",
            "acceptance_check.sh": run_dir / "acceptance_check.sh",
        }
        for label, p in wants.items():
            if p.exists():
                toks.append(f"{label}=present")
            else:
                toks.append(f"{label}=MISSING")
                ok = False
        for label in ("loop.sh", "acceptance_check.sh"):
            p = wants[label]
            if p.exists() and os.access(p, os.X_OK):
                toks.append(f"{label}=executable")
            else:
                toks.append(f"{label}=NOT-EXECUTABLE")
                ok = False
        return ok, toks


@check("loop-driver-red-then-green")
def _red_then_green():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        rc, out, run_dir = _scaffold(tmp)
        if rc != 0:
            return False, [f"build_init_exit={rc}"]
        checker = run_dir / "acceptance_check.sh"
        if not checker.exists():
            return False, ["acceptance_check.sh=MISSING"]

        red = subprocess.run(["bash", str(checker)], cwd=tmp, capture_output=True,
                             text=True, timeout=120)
        red_ok = red.returncode != 0

        acc = run_dir / "ACCEPTANCE.md"
        text = acc.read_text(encoding="utf-8")
        new = re.sub(r"```checks\n.*?```", "```checks\ntrue\n```", text, flags=re.S)
        if new == text:
            return False, ["red_exit_nonzero=%s" % str(red_ok).lower(),
                           "checks_block=NOT-FOUND"]
        acc.write_text(new, encoding="utf-8")

        green = subprocess.run(["bash", str(checker)], cwd=tmp, capture_output=True,
                               text=True, timeout=120)
        green_ok = green.returncode == 0
        toks = [f"red_exit_nonzero={'true' if red_ok else 'false'}",
                f"green_exit_zero={'true' if green_ok else 'false'}"]
        return (red_ok and green_ok), toks


@check("scripts-are-portable-and-lint-clean")
def _portable():
    shells = sorted(SKILL.rglob("*.sh"))
    bad_syntax = []
    for s in shells:
        p = subprocess.run(["bash", "-n", str(s)], capture_output=True, text=True)
        if p.returncode != 0:
            bad_syntax.append(f"{s.name}:{p.stderr.strip()[:80]}")
    hard = []
    pat = re.compile(r"(/Users/[a-z][\w.-]+|/home/[a-z][\w.-]+)", re.I)
    for f in all_tree_files():
        if f.suffix not in {".sh", ".py", ".md"}:
            continue
        if f.name in {"run_checks.py", "check_routing.py"}:
            continue  # the scanners themselves contain example paths
        for m in pat.finditer(read(f)):
            hard.append(f"{f.name}:{m.group(0)}")
    toks = [f"bash_syntax_ok={'true' if not bad_syntax else 'false'}",
            f"hardcoded_user_paths={len(hard)}",
            f"scripts_scanned={len(shells)}"]
    if bad_syntax:
        toks.append("SYNTAX:" + ";".join(bad_syntax))
    if hard:
        toks.append("PATHS:" + ";".join(hard[:5]))
    return (not bad_syntax and not hard and len(shells) >= 1), toks


# ---------------------------------------------------------------- safety

CRITICAL_PATTERNS = {
    "sql_data": r"sql\b|migration|data loss",
    "llm_trust": r"llm (output|trust)|model output|trust boundar",
    "auth": r"auth\b|authorization|permission",
    "secrets": r"secret|credential|api key",
    "injection": r"injection|shell\s*(injection)?|eval\(",
}


@check("guardrails-preserved-safety-review")
def _safety_review():
    text = "\n".join(read(p) for p in doc_surface())
    hits = [k for k, pat in CRITICAL_PATTERNS.items() if re.search(pat, text, re.I)]
    blocking = bool(re.search(r"critical[^.\n]{0,80}block|block[^.\n]{0,80}critical", text, re.I))
    toks = [f"critical_items={len(hits)}/5",
            f"blocking_gate={'true' if blocking else 'false'}"]
    missing = sorted(set(CRITICAL_PATTERNS) - set(hits))
    if missing:
        toks.append("MISSING:" + ",".join(missing))
    return (len(hits) == 5 and blocking), toks


@check("guardrails-workflow-gate-guarded")
def _workflow_gate():
    mentions, unguarded = 0, []
    for f in all_tree_files():
        for i, line in enumerate(read(f).splitlines(), 1):
            if "WORKFLOW_GATE" not in line:
                continue
            mentions += 1
            invokes = re.search(r"(bash|sh|source|\.)\s+[\"']?\$\{?WORKFLOW_GATE", line) \
                or re.search(r"^\s*\"?\$\{?WORKFLOW_GATE\}?\"?\s+\w", line)
            if not invokes:
                continue
            guarded = re.search(r"\[\s*-[xfe]\s|command -v|if\s|&&", line)
            if not guarded:
                unguarded.append(f"{f.name}:{i}")
    toks = [f"workflow_gate_mentions{'>=1' if mentions >= 1 else '=0'}",
            f"unguarded_invocations={len(unguarded)}"]
    if unguarded:
        toks.append("AT:" + ",".join(unguarded))
    return (mentions >= 1 and not unguarded), toks


# Assembled so the scanner never matches itself.
SECRET_PATTERNS = [
    "sk-" + "ant-" + r"[A-Za-z0-9_\-]{12,}",
    "AKIA" + r"[0-9A-Z]{16}",
    "ghp" + r"_[A-Za-z0-9]{20,}",
    "xox" + r"[baprs]-[A-Za-z0-9-]{12,}",
    r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*[\"'][A-Za-z0-9/+_\-]{20,}[\"']",
]


@check("guardrails-no-secrets")
def _no_secrets():
    hits = []
    for f in all_tree_files():
        if f.name == "run_checks.py":
            continue  # holds the detector patterns themselves
        body = read(f)
        for pat in SECRET_PATTERNS:
            for m in re.finditer(pat, body):
                hits.append(f"{f.name}:{m.group(0)[:16]}…")
    rule = bool(re.search(
        r"(never|do not|don't)[^.\n]{0,60}(hardcode|commit|log|print)[^.\n]{0,60}"
        r"(secret|key|token|credential)", "\n".join(read(p) for p in doc_surface()), re.I))
    toks = [f"secret_literals={len(hits)}",
            f"no_secrets_rule={'true' if rule else 'false'}"]
    if hits:
        toks.append("AT:" + ",".join(hits[:5]))
    return (not hits and rule), toks


@check("dual-runtime-mcp-guarded")
def _dual_runtime():
    runtimes = read(REFS / "runtimes.md")
    matrix = False
    for header, rows in markdown_tables(runtimes):
        h = " ".join(header).lower()
        if ("qm" in h or "sandbox" in h) and rows:
            matrix = True
    qm = bool(re.search(r"restricted sandbox", skill_text(), re.I))

    unguarded = []
    guard_words = re.compile(
        r"optional|if available|if installed|if present|skip|fallback|absent|"
        r"not available|guard|degrad|when missing|local only|local-only", re.I)
    for f in doc_surface():
        lines = read(f).splitlines()
        for i, line in enumerate(lines):
            if not re.search(r"mcp__|\bMCP\b|Task tool|subagent_type|plugin", line):
                continue
            window = "\n".join(lines[max(0, i - 3): i + 4])
            if not guard_words.search(window):
                unguarded.append(f"{f.name}:{i + 1}")
    toks = [f"runtime_matrix={'true' if matrix else 'false'}",
            f"qm_sandbox_documented={'true' if qm else 'false'}",
            f"unguarded_mcp_steps={len(unguarded)}"]
    if unguarded:
        toks.append("AT:" + ",".join(unguarded[:5]))
    return (matrix and qm and not unguarded), toks


# ---------------------------------------------------------------- benchmarks

@check("benchmarks-three-specs-present")
def _benchmarks():
    specs = sorted(BENCH.glob("*.md")) if BENCH.is_dir() else []
    bodies = {p.name: read(p) for p in specs}
    def any_match(pat):
        return any(re.search(pat, b, re.I) for b in bodies.values())
    cli = any_match(r"\bCLI\b|command[- ]line")
    api = any_match(r"\bAPI\b|endpoint|HTTP")
    bug = any_match(r"\bbug\b|regression|defect")
    declared = all(re.search(r"^##+\s*Acceptance", b, re.I | re.M) for b in bodies.values()) if bodies else False
    toks = [f"specs={len(specs)}",
            f"cli_spec={'true' if cli else 'false'}",
            f"api_spec={'true' if api else 'false'}",
            f"bugfix_spec={'true' if bug else 'false'}",
            f"all_specs_declare_acceptance={'true' if declared else 'false'}"]
    return (len(specs) == 3 and cli and api and bug and declared), toks


@check("seeded-bug-fixture-actually-broken")
def _seeded_bug():
    app = FIXTURES / "ledger-app"
    heldout = FIXTURES / ".heldout" / "verify_rolling_max.py"
    if not app.is_dir() or not heldout.exists():
        return False, ["fixture=MISSING"]

    env = dict(os.environ, PYTHONPATH=str(app))
    suite = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                           cwd=app, capture_output=True, text=True, env=env, timeout=120)
    suite_ok = suite.returncode == 0

    repro = subprocess.run([sys.executable, str(heldout)], cwd=app, capture_output=True,
                           text=True, env=env, timeout=120)
    repro_fails = repro.returncode != 0

    fixed_ok = False
    with tempfile.TemporaryDirectory() as td:
        clone = Path(td) / "ledger-app"
        shutil.copytree(app, clone)
        target = clone / "ledger" / "report.py"
        src = target.read_text(encoding="utf-8")
        patched = src.replace("max(0, i - window)", "max(0, i - window + 1)")
        if patched != src:
            target.write_text(patched, encoding="utf-8")
            env2 = dict(os.environ, PYTHONPATH=str(clone))
            after = subprocess.run([sys.executable, str(heldout)], cwd=clone,
                                   capture_output=True, text=True, env=env2, timeout=120)
            fixed_ok = after.returncode == 0

    toks = [f"fixture_suite_passes={'true' if suite_ok else 'false'}",
            f"heldout_repro_fails={'true' if repro_fails else 'false'}",
            f"fix_makes_heldout_pass={'true' if fixed_ok else 'false'}"]
    return (suite_ok and repro_fails and fixed_ok), toks


# ---------------------------------------------------------------- driver

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--raw", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    ids = [args.only] if args.only else list(CHECKS)
    unknown = [i for i in ids if i not in CHECKS]
    if unknown:
        print(f"unknown case id(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    results = []
    for cid in ids:
        try:
            ok, toks = CHECKS[cid]()
        except Exception as exc:  # a crashing check is a failing check, never a pass
            ok, toks = False, [f"EXCEPTION={type(exc).__name__}: {exc}"]
        results.append({"id": cid, "pass": ok, "tokens": toks})

    if args.raw:
        for r in results:
            print(" ".join(r["tokens"]))
    elif args.json:
        print(json.dumps(results, indent=2))
    else:
        width = max(len(r["id"]) for r in results)
        for r in results:
            print(f"{'PASS' if r['pass'] else 'FAIL'}  {r['id']:<{width}}  {' '.join(r['tokens'])}")
        n = sum(1 for r in results if r["pass"])
        print(f"\n{n}/{len(results)} deterministic checks passed")

    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
