#!/usr/bin/env python3
"""
Runner for the pre-registered /source acceptance cases (evals/cases.json, evals/GOLD.md).

Mechanizes the deterministic cases only. G1 (blind judge on a real submitted
list) and G2 (link resolution of that list) require a finished sourcing run and
are reported PENDING until one exists — they are never simulated.

    run_cases.py                 # all deterministic cases
    run_cases.py --network       # also run N1-N3 (needs network; N3 needs OPENAI_API_KEY)
    run_cases.py --only G10,G13
"""
import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
FIX = SKILL / "evals" / "fixtures"
STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {"sourcelib"}

SCRAPERS = ["hn_hired.py", "reddit_forhire.py", "v2ex_cv.py",
            "github_contributors.py", "yc_waas.py", "merge.py"]

results = []


def record(cid, ok, detail=""):
    results.append((cid, "PASS" if ok else "FAIL", detail))
    return ok


def pend(cid, detail):
    results.append((cid, "PENDING", detail))


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=SKILL, **kw)


# ---------------------------------------------------------------- hygiene


# Patterns are assembled from fragments so that this file — and the gold
# document that cites it — do not themselves trip the checks they define.
PRIOR_CO = "abund" + "ance"
PERSONAL_PATHS = "/" + "Users" + "/|" + "Davi" + "d's Vault"


def g3():
    r = run(["grep", "-ril", PRIOR_CO, "."])
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    return record("G3", not hits, f"pattern=/{PRIOR_CO}/i · {len(hits)} files: {hits[:5]}")


def g4():
    r = run(["grep", "-rE", PERSONAL_PATHS, "."])
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    return record("G4", not hits, f"pattern=/{PERSONAL_PATHS}/ · {len(hits)} hits: {hits[:3]}")


def g5():
    pat = "kotlin|camerax|camera2|ncnn|tensorrt|vllm|libuvc|v4l2|shenzhen|嵌入式|固件"
    r = run(["grep", "-riE", pat, "scripts/"])
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    return record("G5", not hits, f"{len(hits)} hits: {hits[:3]}")


# -------------------------------------------------------------- functional


def executables():
    return sorted(SCRIPTS.glob("*.py")) + sorted(SCRIPTS.glob("*.sh"))


def g6():
    bad = []
    for s in executables():
        cmd = ["python3", str(s)] if s.suffix == ".py" else ["bash", str(s)]
        r = run(cmd + ["--help"])
        if r.returncode != 0:
            bad.append(f"{s.name}({r.returncode})")
    return record("G6", not bad, f"{len(executables())} scripts; failures: {bad}")


def g7():
    bad = []
    for s in SCRAPERS:
        r = run(["python3", str(SCRIPTS / s), "--profile", str(FIX / "test-role.json"), "--dry-run"])
        if r.returncode != 0 or "DRY RUN" not in r.stdout:
            bad.append(f"{s}(rc={r.returncode})")
    r = run(["bash", str(SCRIPTS / "sweep.sh"), "--profile", str(FIX / "test-role.json"), "--dry-run"])
    if r.returncode != 0 or "DRY RUN" not in r.stdout:
        bad.append(f"sweep.sh(rc={r.returncode})")
    return record("G7", not bad, f"{len(SCRAPERS) + 1} entry points; failures: {bad}")


def g8():
    other = SCRIPTS / "profiles" / "example-data-infra.json"
    a = run(["python3", str(SCRIPTS / "hn_hired.py"), "--profile", str(FIX / "test-role.json"), "--dry-run"]).stdout
    b = run(["python3", str(SCRIPTS / "hn_hired.py"), "--profile", str(other), "--dry-run"]).stdout
    differs = a != b and a and b
    # and the difference must be in the actual search terms, not just the path
    ja, jb = json.loads(a.split("\n", 1)[1]), json.loads(b.split("\n", 1)[1])
    kw_differ = ja["profile"]["keywords"] != jb["profile"]["keywords"]
    return record("G8", bool(differs and kw_differ), f"config differs={bool(differs)} keywords differ={kw_differ}")


def g9():
    r = run(["python3", str(SCRIPTS / "hn_hired.py"), "--profile", str(FIX / "bad-role.json"), "--dry-run"])
    named = bool(re.search(r"(?i)(missing|invalid).*(keywords|role)", r.stderr))
    return record("G9", r.returncode != 0 and named,
                  f"rc={r.returncode} stderr={r.stderr.strip()[:110]!r}")


def g10():
    offenders = []
    for py in sorted(SCRIPTS.glob("*.py")):
        tree = ast.parse(py.read_text())
        guarded = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.Import, ast.ImportFrom)):
                        guarded.add(id(sub))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)) and id(node) not in guarded:
                mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                        else [node.module or ""])
                for m in mods:
                    if m.split(".")[0] not in STDLIB:
                        offenders.append(f"{py.name}:{m}")
    return record("G10", not offenders, f"unguarded third-party imports: {offenders}")


def g11():
    p = SCRIPTS / "credentials.example.json"
    if not p.exists():
        return record("G11", False, "credentials.example.json missing")
    data = json.loads(p.read_text())
    bad = [k for k, v in data.items()
           if not k.startswith("_") and v not in ("",) and not re.fullmatch(r"<.*>", str(v))]
    secretish = [k for k, v in data.items()
                 if re.search(r"(sk-[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|[A-Za-z0-9+/]{40,}=)", str(v))]
    return record("G11", not bad and not secretish,
                  f"non-empty cred fields={bad} secret-shaped={secretish}")


def g12():
    import os
    env = dict(os.environ)
    tmp = SKILL / "evals" / ".tmp-creds.json"
    tmp.write_text(json.dumps({"GITHUB_TOKEN": "from-file", "WAAS_COOKIE": "from-file"}))
    env["HIRING_SCRAPER_CREDENTIALS"] = str(tmp)
    env["GITHUB_TOKEN"] = "from-env"
    env.pop("WAAS_COOKIE", None)
    code = (
        "import sys; sys.path.insert(0, r'%s'); import sourcelib as sl; "
        "c = sl.creds(); print(c.get('GITHUB_TOKEN'), c.get('WAAS_COOKIE')); "
        "print('SKIPMSG' if sl.cred('NOPE_MISSING') is None else 'BAD')" % SCRIPTS
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    tmp.unlink(missing_ok=True)
    out = r.stdout.split()
    ok = r.returncode == 0 and out[:2] == ["from-env", "from-file"] and "SKIPMSG" in r.stdout
    return record("G12", ok, f"rc={r.returncode} got={out[:3]}")


# --------------------------------------------------------------- structure


def g13():
    md = (SKILL / "SKILL.md").read_text()
    fm = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    name = desc = ""
    if fm:
        name = (re.search(r"^name:\s*(.+)$", fm.group(1), re.M) or [None, ""])[1].strip()
        desc = (re.search(r"^description:\s*(.+)$", fm.group(1), re.M) or [None, ""])[1].strip()
    lines = len(md.splitlines())
    refs = list((SKILL / "references").glob("*.md"))
    ok = bool(name and desc) and lines <= 200 and len(refs) >= 3
    return record("G13", ok, f"name={bool(name)} desc={bool(desc)} lines={lines} refs={len(refs)}")


def g14():
    md = (SKILL / "SKILL.md").read_text()
    runtime = bool(re.search(r"(?i)(qm|sandbox)", md))
    has_table = "Sandbox" in md and "Local" in md
    guard = bool(re.search(r"(?i)optional|if .*(unavailable|missing|absent)", md))
    return record("G14", runtime and has_table and guard,
                  f"runtime_mention={runtime} runtime_table={has_table} guard_language={guard}")


# ------------------------------------------------------------ network (N*)


def n1():
    good = run(["python3", str(SCRIPTS / "verify_links.py"), "--url", "https://example.com"])
    bad = run(["python3", str(SCRIPTS / "verify_links.py"), "--url",
               "https://github.com/company-os-nonexistent-repo-check-9f2a1b/none"])
    return record("N1", good.returncode == 0 and bad.returncode != 0,
                  f"200-url rc={good.returncode}, 404-url rc={bad.returncode}")


def n2():
    out = SKILL / "evals" / ".tmp-out"
    r = run(["python3", str(SCRIPTS / "hn_hired.py"), "--profile", str(FIX / "test-role.json"),
             "--threads", "1", "--out", str(out)])
    files = list(out.glob("*_hn.md")) if out.exists() else []
    ok = r.returncode == 0 and bool(files)
    detail = f"rc={r.returncode} report={files[0].name if files else None}"
    if files:
        detail += f" ({files[0].read_text().splitlines()[0]})"
    return record("N2", ok, detail)


def n3():
    import os
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        return pend("N3", "OPENAI_API_KEY not in the environment — judge harness not exercised")
    r = run(["python3", str(SCRIPTS / "judge_list.py"), "--list", str(FIX / "judge-smoke.md"),
             "--scorecard", str(SKILL / "evals" / "GOLD.md"), "--runs", "1",
             "--json", str(SKILL / "evals" / ".tmp-judge.json")])
    ok = r.returncode == 0 and "A-grade:" in r.stdout
    legs_ok = False
    jf = SKILL / "evals" / ".tmp-judge.json"
    if jf.exists():
        d = json.loads(jf.read_text())
        cands = d["runs"][0].get("candidates", [])
        legs_ok = bool(cands) and all(set(c.get("legs", {})) >= {f"L{i}" for i in range(1, 6)} for c in cands)
        jf.unlink()
    return record("N3", ok and legs_ok, f"rc={r.returncode} per_leg_verdicts={legs_ok} :: {r.stdout.strip()[-160:]}")


CASES = {"G3": g3, "G4": g4, "G5": g5, "G6": g6, "G7": g7, "G8": g8, "G9": g9,
         "G10": g10, "G11": g11, "G12": g12, "G13": g13, "G14": g14}
NET = {"N1": n1, "N2": n2, "N3": n3}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated case ids")
    ap.add_argument("--network", action="store_true", help="also run N1-N3")
    args = ap.parse_args()

    todo = dict(CASES)
    if args.network:
        todo.update(NET)
    if args.only:
        want = {c.strip() for c in args.only.split(",")}
        todo = {k: v for k, v in {**CASES, **NET}.items() if k in want}

    for cid in sorted(todo, key=lambda c: (c[0], int(c[1:]))):
        todo[cid]()

    if not args.only:
        pend("G1", "no submitted 10-candidate list yet — requires a live sourcing run")
        pend("G2", "no submitted 10-candidate list yet — requires a live sourcing run")

    print(f"\n{'ID':<5} {'RESULT':<8} DETAIL")
    for cid, res, detail in results:
        print(f"{cid:<5} {res:<8} {detail}")
    n_fail = sum(1 for _, r, _ in results if r == "FAIL")
    n_pend = sum(1 for _, r, _ in results if r == "PENDING")
    n_pass = sum(1 for _, r, _ in results if r == "PASS")
    print(f"\n{n_pass} pass · {n_fail} fail · {n_pend} pending")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
