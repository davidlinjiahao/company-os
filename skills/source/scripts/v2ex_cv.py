#!/usr/bin/env python3
"""
V2EX — self-posted CVs (the /go/cv job-seeking node).

A high-signal slice of the Chinese-speaking developer world: indie-leaning,
often English-fluent, frequently people who have just left a large platform
company. Off by default — enable it in the role profile only when the role is
genuinely open to that market (`sources.v2ex.enabled: true`), and put the
matching non-English terms in `keywords` yourself. This script hardcodes no
language and no geography.

    v2ex_cv.py --profile profiles/my-role.json --dry-run
"""
import re
import sys
import time

import sourcelib as sl

BASE = "https://www.v2ex.com"


def topic_ids(node: str, page: int):
    body = sl.curl(f"{BASE}/go/{node}?p={page}").decode("utf-8", errors="replace")
    return sorted({m.group(1) for m in re.finditer(r'href="/t/(\d+)', body)}, reverse=True)


def fetch_topic(tid: str):
    body = sl.curl(f"{BASE}/t/{tid}").decode("utf-8", errors="replace")
    title_m = re.search(r"<h1>(.*?)</h1>", body, re.DOTALL)
    content_m = re.search(r'<div class="topic_content">(.*?)</div>\s*<div', body, re.DOTALL)
    author = ""
    for m in re.finditer(r'href="/member/([^"]+)"', body):
        cand = m.group(1)
        if "$" not in cand and "{" not in cand:  # skip sponsored-slot templates
            author = cand
            break
    return {
        "id": tid,
        "url": f"{BASE}/t/{tid}",
        "title": sl.clean_html(title_m.group(1)).strip() if title_m else "",
        "body": sl.clean_html(content_m.group(1)).strip() if content_m else "",
        "author": author,
    }


def render(m):
    lines = [f"## [{m['author']}]({m['url']}) — score {m['score']}"]
    lines.append(f"- **Title**: {m['title']}")
    for label, key in (("Location", "location"), ("Experience", "experience"),
                       ("Stack", "stack_field"), ("Contact", "contact")):
        if m.get(key):
            lines.append(f"- **{label}**: {m[key]}")
    lines.append(f"- **Hits**: must={m['must']} · stack={m['stack']} · loc={m['loc']}")
    lines.append(f"- **Snippet**: {re.sub(r'[ \t]+', ' ', m['body'])[:300]}")
    return lines


def main() -> int:
    ap = sl.base_parser(__doc__)
    ap.add_argument("--pages", type=int, help="node index pages to walk (default: profile, else 3)")
    args = ap.parse_args()
    p = sl.load_or_die(args)

    cfg = p.source_cfg("v2ex", enabled=False, node="cv", pages=3)
    node = cfg.get("node", "cv")
    pages = args.pages or int(cfg.get("pages", 3))

    if args.dry_run:
        return sl.dry_run("v2ex", p,
                          queries=[f"{BASE}/go/{node}?p={i}" for i in range(1, pages + 1)],
                          extra={"node": node, "pages": pages, "enabled": cfg.get("enabled", False)})

    if not cfg.get("enabled", False):
        print("v2ex: disabled in this role profile (default) — skipping.")
        return 0

    matches, seen = [], set()
    for page in range(1, pages + 1):
        try:
            ids = topic_ids(node, page)
        except Exception as e:  # noqa: BLE001 — one bad page must not kill the sweep
            print(f"  ! /go/{node} p{page}: {e}", file=sys.stderr)
            continue
        print(f"/go/{node} p{page}: {len(ids)} topics")
        for tid in ids:
            try:
                t = fetch_topic(tid)
            except Exception as e:  # noqa: BLE001
                print(f"  ! topic {tid}: {e}", file=sys.stderr)
                continue
            s, must, stack, loc = p.score(f"{t['title']}\n{t['body']}")
            if s < p.min_score or not t["author"] or t["author"] in seen:
                continue
            seen.add(t["author"])
            matches.append({
                **t, "score": s, "must": must, "stack": stack, "loc": loc,
                "location": sl.field(t["body"], ["Location", "City"]),
                "experience": sl.field(t["body"], ["Experience", "Years"]),
                "stack_field": sl.field(t["body"], ["Tech", "Stack", "Skills"]),
                "contact": sl.field(t["body"], ["Contact", "Email"]),
            })
            time.sleep(1.0)  # be polite

    matches.sort(key=lambda m: m["score"], reverse=True)
    if args.limit:
        matches = matches[: args.limit]
    out = sl.write_report(matches, sl.report_path(args, p, "v2ex"),
                          f"V2EX /go/{node} — {p.role}", render, p.min_score)
    print(f"{len(matches)} candidates → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
