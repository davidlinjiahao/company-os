#!/usr/bin/env python3
"""
The three-model decision panel.

Runs BOTH lenses — game theory and Hegelian dialectic — across THREE frontier
models on their own APIs, then merges the six analyses into one recommendation
brief and one ledger row.

    claude-fable-5   Anthropic   ANTHROPIC_API_KEY   api.anthropic.com
    gpt-5.6-sol      OpenAI      OPENAI_API_KEY      api.openai.com
    grok-4.5         xAI         XAI_API_KEY         api.x.ai   (OpenAI-compatible)

Only 1-way doors go through the panel. 2-way doors take the fast path (see
SKILL.md) and this script refuses to run on them unless --force is passed.

Usage:
    python3 scripts/panel.py --decision-file decision.json --out out/

Inputs: a JSON file shaped like evals/fixtures/decisions/*.json —
    {id, decision, door_type, framing:{context, options, deadline, owner},
     members:[{name, role, lean, confidence, decisive_reason, answers:{P1_..P10_}}]}

Outputs, all written under --out:
    panel-log.jsonl   one line per model call: model, lens, status, latency, tokens
    panel.json        the merged analysis, member coverage, and the ledger row
    brief.md          the recommendation brief

Standard library only (urllib + threads), so it runs identically in local Claude
Code and in the restricted sandbox where no MCP servers exist.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import date as _date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger import build_row  # noqa: E402

MODELS = [
    {"id": "claude-fable-5", "provider": "anthropic", "key_env": "ANTHROPIC_API_KEY",
     "url": "https://api.anthropic.com/v1/messages"},
    {"id": "gpt-5.6-sol", "provider": "openai", "key_env": "OPENAI_API_KEY",
     "url": "https://api.openai.com/v1/chat/completions"},
    {"id": "grok-4.5", "provider": "xai", "key_env": "XAI_API_KEY",
     "url": "https://api.x.ai/v1/chat/completions"},
]

RECOMMENDATIONS = ("GO", "NO-GO", "MODIFY", "DEFER")

COMMON_CONTRACT = """
Return STRICT JSON and nothing else. No markdown fence, no prose outside the object.

Every response must contain these keys:
  "recommendation"  one of "GO", "NO-GO", "MODIFY", "DEFER"
  "headline"        one sentence, plain language, no jargon
  "confidence"      a number between 0 and 1
  "decisive_fact"   the single fact in the brief that decides this, stated flatly
  "members_used"    a list of {"name", "position", "how_it_changed_the_analysis"} —
                    ONE ENTRY FOR EVERY NAMED TEAM MEMBER in the input, including the
                    ones you disagree with. Name them explicitly. Do not merge them
                    into a "the team" view.
  "kill_criteria"   an observable signal, with a date, that would say this was wrong
  "what_would_change_the_answer"  the highest-value unknown, and how to resolve it
"""

LENS_PROMPTS = {
    "game_theory": """You are running a GAME-THEORY analysis of a decision for the team that
has to live with it. Plain language. No hedging, no essay.

Model the decision as a game:
- Every player whose choices move the outcome. For each: position (what they say),
  interest (the why underneath), BATNA (their next-best option if there is no deal),
  and leverage (the concrete lever they control).
- The strategy profiles available, including moves that are not on the table yet.
- Which profiles are Nash equilibria: no player can profitably deviate unilaterally
  given the others' choices and BATNAs. Say whose best response holds each in place.
- Separate the NATURAL equilibrium the game falls into by default from the owner's
  MOST-PREFERRED one, and say whether the preferred one is actually REACHABLE given
  who holds leverage. An equilibrium you cannot reach is not a plan.
- Hunt for third doors: positive-sum moves that change the game rather than play it.
- Never assert a threat the owner's real BATNA cannot back.

Additional required keys:
  "players"   list of {"name","position","interest","batna","leverage"}
  "equilibria" list of {"profile","why_stable","quality_for_owner"}
  "natural_equilibrium"      one line
  "recommended_equilibrium"  one line
  "reachable"                {"verdict": true|false, "why": "..."}
  "third_doors"              list of one-line moves (empty list if there are none)
  "sequencing"               ordered list of moves to reach the recommendation
""" + COMMON_CONTRACT,

    "dialectic": """You are running a HEGELIAN DIALECTIC pass on a decision.

Do it properly, not as decoration:
- THESIS: the strongest, fully committed case for acting. Not a summary of one side —
  argue it as if you believe it.
- ANTITHESIS: the strongest, fully committed case against. It must attack the thesis'
  actual load-bearing assumption, not a caricature.
- DETERMINATE NEGATION: for each side, not "this is wrong" but "this is wrong in a
  SPECIFIC way, and that specific failure points at what is missing." The failure mode
  is the signpost.
- SUBLATION: what both sides are actually disagreeing about, resolved at a level that
  cancels, preserves and elevates both. It is NOT a compromise, NOT splitting the
  difference, and NOT "do a bit of each". A real sublation makes the original
  disagreement look predictable in hindsight, and would be recognised by both sides as
  more complete than what they argued. If all you have is a compromise, say so
  explicitly in "sublation_is_real": false rather than dressing it up.

Additional required keys:
  "thesis"      {"claim","strongest_support"}
  "antithesis"  {"claim","strongest_support"}
  "determinate_negation" {"thesis_fails_because","antithesis_fails_because"}
  "sublation"   the resolution, 2-4 sentences
  "sublation_is_real"  true if it genuinely transforms the question, false if it is
                       only a compromise
  "what_it_dissolves"  the question that stops mattering once you see it this way
  "test_that_would_falsify"  the observation that would break the sublation
""" + COMMON_CONTRACT,
}


# ------------------------------------------------------------------ transport
def _post(url: str, headers: dict, payload: dict, timeout: int):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode())


def call_model(model: dict, system: str, user: str, max_tokens: int, timeout: int):
    """Return (text, http_status, prompt_tokens, completion_tokens). Raises on failure."""
    key = os.environ[model["key_env"]]
    if model["provider"] == "anthropic":
        status, body = _post(
            model["url"],
            {"x-api-key": key, "anthropic-version": "2023-06-01",
             "content-type": "application/json"},
            {"model": model["id"], "max_tokens": max_tokens, "system": system,
             "messages": [{"role": "user", "content": user}]},
            timeout)
        text = "".join(b.get("text", "") for b in body.get("content", [])
                       if b.get("type") == "text")
        usage = body.get("usage", {})
        if body.get("stop_reason") == "max_tokens" and not text.strip():
            raise RuntimeError("truncated at max_tokens before any text was emitted")
        return text, status, usage.get("input_tokens", 0), usage.get("output_tokens", 0)

    # openai + xai are both OpenAI-compatible chat completions
    payload = {"model": model["id"],
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}]}
    payload["max_completion_tokens" if model["provider"] == "openai"
            else "max_tokens"] = max_tokens
    status, body = _post(model["url"],
                         {"Authorization": f"Bearer {key}",
                          "Content-Type": "application/json"},
                         payload, timeout)
    text = body["choices"][0]["message"].get("content") or ""
    usage = body.get("usage", {})
    return text, status, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def extract_json(text: str) -> dict:
    """Pull the first balanced JSON object out of a model response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", text).strip()
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object in response")
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON object in response")


# --------------------------------------------------------------------- prompt
def render_decision(d: dict) -> str:
    f = d.get("framing", {})
    lines = [f"# Decision\n{d['decision']}",
             f"\nDoor type: {d.get('door_type', '1-way')} (irreversible)",
             f"Owner: {f.get('owner', 'unspecified')}",
             f"Deadline: {f.get('deadline', 'unspecified')}",
             f"\n## Context\n{f.get('context', '')}"]
    if f.get("options"):
        lines.append("\n## Options on the table")
        lines += [f"- {o}" for o in f["options"]]
    lines.append("\n## The team's answers to the ten decision principles")
    lines.append("Each member answered the same ten questions. Their answers diverge on "
                 "purpose. Treat the divergence as data, not noise: the places they "
                 "disagree are where the decision actually lives.\n")
    for m in d.get("members", []):
        lines.append(f"### {m['name']} — {m.get('role', '')}")
        lines.append(f"Lean: {m.get('lean', '?')} · Confidence {m.get('confidence', '?')}/10")
        lines.append(f"Single decisive reason: {m.get('decisive_reason', '')}")
        for k, v in (m.get("answers") or {}).items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    names = [m["name"] for m in d.get("members", [])]
    lines.append(f"\nYou must reference every one of these members by name in "
                 f"members_used: {', '.join(names)}.")
    return "\n".join(lines)


# ----------------------------------------------------------------------- runs
def run_one(model, lens, system, user, max_tokens, timeout, run_id, log_path, lock):
    t0 = time.time()
    attempt, last_err = 0, None
    if not os.environ.get(model["key_env"]):
        _log(log_path, lock, {"run_id": run_id, "model": model["id"],
                              "provider": model["provider"], "lens": lens,
                              "status": "skipped_no_key", "http_status": None,
                              "latency_ms": 0, "prompt_tokens": 0,
                              "completion_tokens": 0, "attempt": 0,
                              "error": f"{model['key_env']} not set"})
        return None

    while attempt < 2:
        attempt += 1
        try:
            nudge = "" if attempt == 1 else (
                "\n\nYour previous reply was not parseable. Reply with the JSON object "
                "only — no prose, no code fence.")
            text, http, pt, ct = call_model(model, system + nudge, user,
                                            max_tokens, timeout)
            obj = extract_json(text)
            obj["_model"] = model["id"]
            obj["_lens"] = lens
            obj["_raw"] = text
            _log(log_path, lock, {"run_id": run_id, "model": model["id"],
                                  "provider": model["provider"], "lens": lens,
                                  "status": "ok", "http_status": http,
                                  "latency_ms": int((time.time() - t0) * 1000),
                                  "prompt_tokens": pt, "completion_tokens": ct,
                                  "attempt": attempt, "error": None})
            return obj
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError,
                ValueError, KeyError, RuntimeError, json.JSONDecodeError) as e:
            last_err = f"{type(e).__name__}: {e}"
            if isinstance(e, urllib.error.HTTPError):
                try:
                    last_err += " | " + e.read().decode()[:300]
                except Exception:  # noqa: BLE001 - best-effort error detail
                    pass

    _log(log_path, lock, {"run_id": run_id, "model": model["id"],
                          "provider": model["provider"], "lens": lens,
                          "status": "error", "http_status": None,
                          "latency_ms": int((time.time() - t0) * 1000),
                          "prompt_tokens": 0, "completion_tokens": 0,
                          "attempt": attempt, "error": last_err})
    return None


def _log(path: Path, lock, record: dict) -> None:
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
    with lock:
        with path.open("a") as fh:
            fh.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------- merge
def _words(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 3}


def cluster(lines: list[tuple[str, str]], threshold: float = 0.45):
    """Cluster (source, text) pairs by word overlap. Heuristic, and labelled as such."""
    clusters: list[dict] = []
    for src, text in lines:
        ws = _words(text)
        if not ws:
            continue
        for c in clusters:
            inter = len(ws & c["words"])
            union = len(ws | c["words"]) or 1
            if inter / union >= threshold:
                c["sources"].append(src)
                c["variants"].append(text)
                c["words"] |= ws
                break
        else:
            clusters.append({"text": text, "sources": [src], "variants": [text],
                             "words": ws})
    for c in clusters:
        c.pop("words")
    return clusters


def ledger_label(decision: dict, limit: int = 120) -> str:
    """The ledger's decision column is one line of at most `limit` chars with no pipes.

    A framed decision sentence can legitimately be longer than that, so derive a
    label instead of crashing: use an explicit `ledger_label` if the decision object
    carries one, otherwise trim at the last word boundary that fits.
    """
    text = " ".join(str(decision.get("ledger_label")
                        or decision["decision"]).replace("|", "/").split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 3]
    if " " in cut:
        cut = cut[:cut.rindex(" ")]
    return cut.rstrip(" ,;:-") + "..."


def merge(decision: dict, results: list[dict]) -> dict:
    """Merge the six lens analyses. Deterministic — no extra model call."""
    members = [m["name"] for m in decision.get("members", [])]

    votes: dict[str, list] = {}
    for r in results:
        rec = str(r.get("recommendation", "")).upper().strip()
        if rec not in RECOMMENDATIONS:
            rec = "DEFER"
        votes.setdefault(rec, []).append(
            {"model": r["_model"], "lens": r["_lens"],
             "confidence": float(r.get("confidence") or 0.5),
             "headline": r.get("headline", "")})

    ranked = sorted(votes.items(),
                    key=lambda kv: (len(kv[1]), sum(v["confidence"] for v in kv[1])),
                    reverse=True)
    consensus = ranked[0][0] if ranked else "DEFER"
    unanimous = len(ranked) == 1 and bool(results)
    contested = len(ranked) > 1 and len(ranked[0][1]) == len(ranked[1][1])

    # Member coverage: who did the panel actually engage with, by name.
    coverage = {}
    for name in members:
        refs = []
        for r in results:
            named = any(str(e.get("name", "")).lower() == name.lower()
                        for e in (r.get("members_used") or [])
                        if isinstance(e, dict))
            in_text = re.search(rf"\b{re.escape(name)}\b", r.get("_raw", ""), re.I)
            if named or in_text:
                refs.append(f"{r['_model']}:{r['_lens']}")
        coverage[name] = {"referenced_by": refs, "count": len(refs)}

    gt = [r for r in results if r["_lens"] == "game_theory"]
    di = [r for r in results if r["_lens"] == "dialectic"]

    third_doors = cluster([(f"{r['_model']}", t) for r in gt
                           for t in (r.get("third_doors") or []) if isinstance(t, str)])
    decisive = [{"model": r["_model"], "lens": r["_lens"],
                 "fact": r.get("decisive_fact", "")} for r in results]

    f = decision.get("framing", {})
    owner = f.get("owner") or "unassigned"
    label = ledger_label(decision)
    row = build_row(_date.today().isoformat(), label,
                    decision.get("door_type", "1-way"), consensus, owner)

    return {
        "decision": decision["decision"],
        "decision_id": decision.get("id"),
        "door_type": decision.get("door_type", "1-way"),
        "owner": owner,
        "models_called": sorted({r["_model"] for r in results}),
        "lenses_run": sorted({r["_lens"] for r in results}),
        "analyses": len(results),
        "vote": {k: v for k, v in ranked},
        "consensus_recommendation": consensus,
        "unanimous": unanimous,
        "contested": contested,
        "member_coverage": coverage,
        "decisive_facts": decisive,
        "third_doors": third_doors,
        "game_theory": [{"model": r["_model"],
                         "players": r.get("players", []),
                         "equilibria": r.get("equilibria", []),
                         "natural_equilibrium": r.get("natural_equilibrium", ""),
                         "recommended_equilibrium": r.get("recommended_equilibrium", ""),
                         "reachable": r.get("reachable", {}),
                         "sequencing": r.get("sequencing", [])} for r in gt],
        "dialectic": [{"model": r["_model"],
                       "thesis": r.get("thesis", {}),
                       "antithesis": r.get("antithesis", {}),
                       "determinate_negation": r.get("determinate_negation", {}),
                       "sublation": r.get("sublation", ""),
                       "sublation_is_real": r.get("sublation_is_real"),
                       "what_it_dissolves": r.get("what_it_dissolves", ""),
                       "test_that_would_falsify": r.get("test_that_would_falsify", "")}
                      for r in di],
        "kill_criteria": [{"model": r["_model"], "lens": r["_lens"],
                           "text": r.get("kill_criteria", "")} for r in results],
        "what_would_change_the_answer": [
            {"model": r["_model"], "lens": r["_lens"],
             "text": r.get("what_would_change_the_answer", "")} for r in results],
        "ledger_row": row,
    }


# ---------------------------------------------------------------------- brief
def _bul(items):
    return "\n".join(f"- {i}" for i in items) if items else "- (none offered)"


def render_brief(decision: dict, m: dict) -> str:
    members = decision.get("members", [])
    out = [f"# Decision brief: {m['decision']}", "",
           f"**Recommendation:** {m['consensus_recommendation']}  ·  "
           f"**Door type:** {m['door_type']}  ·  **Owner:** {m['owner']}",
           f"**Panel:** {m['analyses']} analyses from "
           f"{', '.join(m['models_called'])} across {', '.join(m['lenses_run'])}",
           ""]
    if m["contested"]:
        out.append("> The panel is split. Treat the recommendation as the leading option, "
                   "not a settled answer.\n")
    elif m["unanimous"]:
        out.append("> The panel is unanimous.\n")

    out += ["## Recommendation", ""]
    for rec, voters in m["vote"].items():
        out.append(f"**{rec}** — {len(voters)} of {m['analyses']} analyses")
        for v in voters:
            out.append(f"  - {v['model']} / {v['lens']} (conf {v['confidence']}): "
                       f"{v['headline']}")
    out += ["", "### The facts each analysis called decisive", ""]
    out += [f"- **{d['model']} / {d['lens']}** — {d['fact']}" for d in m["decisive_facts"]]

    out += ["", "## Where the team diverged", "",
            "| Member | Role | Lean | Their single decisive reason | Engaged by |",
            "|---|---|---|---|---|"]
    for mem in members:
        cov = m["member_coverage"].get(mem["name"], {})
        out.append(f"| {mem['name']} | {mem.get('role', '')} | {mem.get('lean', '?')} "
                   f"| {mem.get('decisive_reason', '')} | {cov.get('count', 0)}/"
                   f"{m['analyses']} analyses |")
    unengaged = [n for n, c in m["member_coverage"].items() if c["count"] == 0]
    if unengaged:
        out.append(f"\n**Not engaged by any model: {', '.join(unengaged)}.** "
                   "Their input has been dropped — re-run before trusting this brief.")

    out += ["", "## Game theory", ""]
    for g in m["game_theory"]:
        out.append(f"### {g['model']}")
        out.append(f"- Natural equilibrium: {g['natural_equilibrium']}")
        out.append(f"- Recommended equilibrium: {g['recommended_equilibrium']}")
        reach = g.get("reachable") or {}
        out.append(f"- Reachable: {reach.get('verdict')} — {reach.get('why', '')}")
        if g.get("players"):
            out += ["", "| Player | Position | Interest | BATNA | Leverage |",
                    "|---|---|---|---|---|"]
            for p in g["players"]:
                out.append(f"| {p.get('name','')} | {p.get('position','')} | "
                           f"{p.get('interest','')} | {p.get('batna','')} | "
                           f"{p.get('leverage','')} |")
        if g.get("sequencing"):
            out += ["", "Sequencing:", _bul(g["sequencing"])]
        out.append("")

    out += ["## Third doors", "",
            "*(clustered across models by word overlap — a heuristic, read the variants)*", ""]
    if m["third_doors"]:
        for c in m["third_doors"]:
            out.append(f"- **{c['text']}** — proposed by {', '.join(sorted(set(c['sources'])))}")
    else:
        out.append("- No third door was found. The choice really is between the options above.")

    out += ["", "## Dialectic", ""]
    for d in m["dialectic"]:
        real = d.get("sublation_is_real")
        out += [f"### {d['model']}",
                f"- **Thesis:** {(d.get('thesis') or {}).get('claim', '')}",
                f"- **Antithesis:** {(d.get('antithesis') or {}).get('claim', '')}",
                f"- **Thesis fails because:** "
                f"{(d.get('determinate_negation') or {}).get('thesis_fails_because', '')}",
                f"- **Antithesis fails because:** "
                f"{(d.get('determinate_negation') or {}).get('antithesis_fails_because', '')}",
                f"- **Sublation"
                f"{' (self-reported as a real transformation)' if real else ' (self-reported as only a compromise)'}:** "
                f"{d.get('sublation', '')}",
                f"- **What it dissolves:** {d.get('what_it_dissolves', '')}",
                f"- **Falsified by:** {d.get('test_that_would_falsify', '')}", ""]

    out += ["## Kill criteria", ""]
    out += [f"- **{k['model']} / {k['lens']}** — {k['text']}" for k in m["kill_criteria"]]
    out += ["", "## What would change the answer", ""]
    out += [f"- **{w['model']} / {w['lens']}** — {w['text']}"
            for w in m["what_would_change_the_answer"]]

    out += ["", "## Ledger row", "",
            "| date | decision | type | recommendation | owner | outcome |",
            "|---|---|---|---|---|---|", m["ledger_row"], ""]
    return "\n".join(out)


# --------------------------------------------------------------------- driver
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decision-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lenses", default="game_theory,dialectic")
    ap.add_argument("--models", default=",".join(m["id"] for m in MODELS))
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--timeout", type=int, default=420)
    ap.add_argument("--force", action="store_true",
                    help="run the panel even on a 2-way door")
    args = ap.parse_args()

    decision = json.loads(Path(args.decision_file).read_text())
    door = decision.get("door_type", "1-way")
    if door == "2-way" and not args.force:
        print("This is a 2-way door. 2-way doors take the fast path: skip the panel, "
              "write a quick recommendation and one ledger row via scripts/ledger.py. "
              "Pass --force only if you have a specific reason to spend the panel on a "
              "reversible decision.", file=sys.stderr)
        return 2

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    log_path = outdir / "panel-log.jsonl"
    log_path.write_text("")

    run_id = uuid.uuid4().hex[:12]
    lenses = [x.strip() for x in args.lenses.split(",") if x.strip()]
    wanted = {x.strip() for x in args.models.split(",")}
    models = [m for m in MODELS if m["id"] in wanted]
    user = render_decision(decision)

    lock = threading.Lock()
    jobs = [(m, lens) for m in models for lens in lenses]
    results = []
    with futures.ThreadPoolExecutor(max_workers=len(jobs) or 1) as pool:
        futs = {pool.submit(run_one, m, lens, LENS_PROMPTS[lens], user,
                            args.max_tokens, args.timeout, run_id, log_path, lock):
                (m["id"], lens) for m, lens in jobs}
        for fut in futures.as_completed(futs):
            r = fut.result()
            if r is not None:
                results.append(r)

    if not results:
        print("No model returned a usable analysis. See panel-log.jsonl.",
              file=sys.stderr)
        return 1

    merged = merge(decision, results)
    merged["run_id"] = run_id
    merged["models_missing"] = [m["id"] for m in models
                                if m["id"] not in merged["models_called"]]
    (outdir / "panel.json").write_text(json.dumps(merged, indent=2))
    brief = render_brief(decision, merged)
    (outdir / "brief.md").write_text(brief)

    print(f"{merged['analyses']} analyses from {', '.join(merged['models_called'])}")
    if merged["models_missing"]:
        print(f"MISSING: {', '.join(merged['models_missing'])} — see panel-log.jsonl")
    print(f"recommendation: {merged['consensus_recommendation']}"
          f"{'  (CONTESTED)' if merged['contested'] else ''}")
    print(merged["ledger_row"])
    print(f"brief: {outdir / 'brief.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
