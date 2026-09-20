#!/usr/bin/env python3
"""
Y Combinator Work at a Startup — two modes.

  --mode jobs        public job board, no auth. Mostly COMPETITOR CALIBRATION:
                     who else is hiring this role, what they pay, where.
                     Feed the findings back into the scorecard.
  --mode candidates  candidate side, auth-gated. Needs WAAS_COOKIE (the full
                     Cookie: header from a logged-in browser). Without it this
                     mode reports a skip and exits 0 — it never fails the sweep.

WaaS runs on Inertia.js: page state lives in a `data-page` attribute, which we
unescape and parse as JSON.

    yc_waas.py --mode jobs --profile profiles/my-role.json --dry-run
"""
import html
import json
import re
import subprocess
import sys
import time

import sourcelib as sl

BASE = "https://www.workatastartup.com"
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def get_page(path: str, cookie: str | None = None) -> dict:
    args = ["curl", "-sS", "-L", "--max-time", "30", "-A", BROWSER_UA,
            "-H", "Accept: text/html,application/xhtml+xml", "-H", "Accept-Encoding: identity"]
    if cookie:
        args += ["-H", f"Cookie: {cookie}"]
    args.append(f"{BASE}{path}")
    body = subprocess.run(args, capture_output=True, check=True).stdout.decode("utf-8", "replace")
    m = re.search(r'data-page="([^"]+)"', body)
    if not m:
        return {}
    return json.loads(html.unescape(m.group(1)))


# ---------------------------------------------------------------- jobs mode


def render_job(j):
    lines = [f"## [{j.get('title','?')} @ {j.get('companyName','?')} ({j.get('companyBatch','')})]"
             f"({j.get('applyUrl') or BASE + '/companies/' + (j.get('companySlug') or '')}) — score {j['_score']}"]
    for label, key in (("Location", "location"), ("Salary", "salary"),
                       ("Role type", "roleType"), ("Company", "companyOneLiner")):
        if j.get(key):
            lines.append(f"- **{label}**: {j[key]}")
    lines.append(f"- **Hits**: must={j['_must']} · stack={j['_stack']} · loc={j['_loc']}")
    return lines


def run_jobs(p: sl.RoleProfile, args) -> int:
    seen, paths = {}, ["/jobs"]
    props = get_page("/jobs").get("props", {}) or {}
    for j in props.get("jobs", []):
        seen[j["id"]] = j
    for rl in props.get("roleLinks", []):
        if rl.get("path") and rl["path"] not in paths:
            paths.append(rl["path"])
    for path in paths[1:]:
        print(f"  GET {path}")
        try:
            for j in (get_page(path).get("props", {}) or {}).get("jobs", []):
                seen.setdefault(j["id"], j)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"  ! {path}: {e}", file=sys.stderr)
        time.sleep(0.5)

    matches = []
    for j in seen.values():
        text = " ".join(filter(None, [j.get("title"), j.get("companyOneLiner"), j.get("location"),
                                      j.get("roleType"), j.get("companyName"), j.get("salary")]))
        s, must, stack, loc = p.score(text)
        if s < p.min_score:
            continue
        j.update({"_score": s, "_must": must, "_stack": stack, "_loc": loc})
        matches.append(j)
    matches.sort(key=lambda j: j["_score"], reverse=True)
    if args.limit:
        matches = matches[: args.limit]
    out = sl.write_report(matches, sl.report_path(args, p, "waas-jobs"),
                          f"YC WaaS — who else is hiring for {p.role}", render_job, p.min_score)
    print(f"{len(seen)} jobs → {len(matches)} relevant → {out}")
    return 0


# ---------------------------------------------------------- candidates mode


def render_cand(c):
    lines = [f"## [{c['name']}]({c['url']}) — score {c['score']}"]
    for k in ("location", "willingToRelocate", "headline", "oneliner", "skills", "summary"):
        v = c["raw"].get(k)
        if not v:
            continue
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v[:10])
        lines.append(f"- **{k}**: {str(v)[:300]}")
    lines.append(f"- **Hits**: must={c['must']} · stack={c['stack']} · loc={c['loc']}")
    return lines


def run_candidates(p: sl.RoleProfile, args, filters) -> int:
    cookie = sl.cred("WAAS_COOKIE", "candidate side is login-gated")
    if not cookie:
        return 0
    cards = {}
    for f in filters:
        path = "/candidates" + (f"?{f}" if f else "")
        print(f"  GET {path}")
        try:
            data = get_page(path, cookie)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"  ! {path}: {e}", file=sys.stderr)
            continue
        component = data.get("component", "")
        if "login" in component.lower() or "HomePage" in component:
            print("  ! WAAS_COOKIE expired or wrong — re-copy it from a logged-in browser "
                  "(DevTools → Network → any request → Cookie header).", file=sys.stderr)
            return 0
        props = data.get("props", {}) or {}
        found = (props.get("candidates") or props.get("profiles")
                 or props.get("users") or props.get("results") or [])
        print(f"    {len(found)} cards")
        for c in found:
            cid = c.get("id") or c.get("slug") or c.get("username")
            if cid:
                cards.setdefault(cid, c)
        time.sleep(1.0)

    if not cards:
        print("  no candidate cards parsed — the page shape may have changed. "
              "Report this lane as UN-SWEPT rather than empty.", file=sys.stderr)

    matches = []
    for c in cards.values():
        s, must, stack, loc = p.score(json.dumps(c, ensure_ascii=False))
        if s < p.min_score:
            continue
        matches.append({
            "name": c.get("name") or c.get("displayName") or c.get("username"),
            "url": f"{BASE}/candidates/{c.get('id') or c.get('slug')}",
            "score": s, "must": must, "stack": stack, "loc": loc, "raw": c,
        })
    matches.sort(key=lambda m: m["score"], reverse=True)
    if args.limit:
        matches = matches[: args.limit]
    out = sl.write_report(matches, sl.report_path(args, p, "waas-candidates"),
                          f"YC WaaS candidates — {p.role}", render_cand, p.min_score)
    print(f"{len(cards)} cards → {len(matches)} matches → {out}")
    return 0


def main() -> int:
    ap = sl.base_parser(__doc__)
    ap.add_argument("--mode", choices=["jobs", "candidates"], default="jobs")
    args = ap.parse_args()
    p = sl.load_or_die(args)

    cfg = p.source_cfg("waas", candidate_filters=[""])
    filters = list(cfg.get("candidate_filters") or [""])

    if args.dry_run:
        queries = ([f"{BASE}/jobs (+ every discovered roleLink)"] if args.mode == "jobs"
                   else [f"{BASE}/candidates" + (f"?{f}" if f else "") for f in filters])
        return sl.dry_run(f"waas-{args.mode}", p, queries=queries,
                          extra={"mode": args.mode, "candidate_filters": filters,
                                 "cookie_present": bool(sl.creds().get("WAAS_COOKIE")),
                                 "enabled": cfg.get("enabled", True)})

    if not cfg.get("enabled", True):
        print("waas: disabled in this role profile — skipping.")
        return 0
    return run_jobs(p, args) if args.mode == "jobs" else run_candidates(p, args, filters)


if __name__ == "__main__":
    sys.exit(main())
