#!/usr/bin/env python3
"""
Hacker News "Who wants to be hired?" — candidate side.

Pulls the last N monthly threads via the public Algolia API, scores every
top-level post against the role profile, writes a ranked markdown report.

No auth. High yield for US-remote and generalist roles; thin for niche
specialisms (people who post here self-describe in mainstream terms).

    hn_hired.py --profile profiles/my-role.json
    hn_hired.py --profile profiles/my-role.json --dry-run
"""
import sys
import time

import sourcelib as sl

ALGOLIA = "https://hn.algolia.com/api/v1"


def find_threads(n: int):
    url = f"{ALGOLIA}/search_by_date?tags=story,author_whoishiring&hitsPerPage=50"
    hits = sl.get_json(url).get("hits", [])
    threads = [
        {"id": h["objectID"], "title": h["title"], "created": h["created_at"]}
        for h in hits
        if "who wants to be hired" in (h.get("title") or "").lower()
    ]
    threads.sort(key=lambda t: t["created"], reverse=True)
    return threads[:n]


def fetch_comments(story_id: str):
    out, page = [], 0
    while True:
        url = f"{ALGOLIA}/search?tags=comment,story_{story_id}&hitsPerPage=1000&page={page}"
        hits = sl.get_json(url).get("hits", [])
        if not hits:
            break
        out.extend(hits)
        if len(hits) < 1000:
            break
        page += 1
        time.sleep(0.3)
    return [c for c in out if c.get("parent_id") == int(story_id)]


def render(m):
    url = f"https://news.ycombinator.com/item?id={m['id']}"
    lines = [f"## [{m['author']}]({url}) — score {m['score']} — {m['created']}"]
    for label, key in (
        ("Location", "location"), ("Remote", "remote"), ("Relocate", "relocate"),
        ("Tech", "tech"), ("Email", "email"), ("Résumé", "resume"),
    ):
        if m.get(key):
            lines.append(f"- **{label}**: {m[key]}")
    lines.append(
        f"- **Hits**: must={m['must']} · stack={m['stack']} · loc={m['loc']}"
    )
    lines.append(f"- **Thread**: {m['thread']}")
    return lines


def main() -> int:
    ap = sl.base_parser(__doc__)
    ap.add_argument("--threads", type=int, help="how many monthly threads to walk (default: profile, else 6)")
    args = ap.parse_args()
    p = sl.load_or_die(args)

    cfg = p.source_cfg("hn", threads=6)
    n = args.threads or int(cfg.get("threads", 6))

    if args.dry_run:
        return sl.dry_run(
            "hn",
            p,
            queries=[f"{ALGOLIA}/search_by_date?tags=story,author_whoishiring (latest {n} 'who wants to be hired' threads)"],
            extra={"threads": n, "min_score": p.min_score, "enabled": cfg.get("enabled", True)},
        )

    if not cfg.get("enabled", True):
        print("hn: disabled in this role profile — skipping.")
        return 0

    threads = find_threads(n)
    print(f"{len(threads)} threads")
    matches = []
    for t in threads:
        comments = fetch_comments(t["id"])
        print(f"  {t['title']}: {len(comments)} posts")
        for c in comments:
            text = sl.clean_html(c.get("comment_text", ""))
            s, must, stack, loc = p.score(text)
            if s < p.min_score:
                continue
            matches.append({
                "id": c["objectID"],
                "author": c.get("author"),
                "created": (c.get("created_at") or "")[:10],
                "thread": t["title"],
                "score": s, "must": must, "stack": stack, "loc": loc,
                "location": sl.field(text, "Location"),
                "remote": sl.field(text, "Remote"),
                "relocate": sl.field(text, ["Willing to relocate", "Relocate"]),
                "tech": sl.field(text, ["Technologies", "Tech", "Stack"]),
                "email": sl.field(text, "Email"),
                "resume": sl.field(text, ["Résumé", "Resume", "CV", "Résumé/CV"]),
            })
        time.sleep(0.4)

    uniq = sorted(sl.dedupe(matches), key=lambda m: m["score"], reverse=True)
    if args.limit:
        uniq = uniq[: args.limit]
    out = sl.write_report(uniq, sl.report_path(args, p, "hn"),
                          f"HN 'Who wants to be hired' — {p.role}", render, p.min_score)
    print(f"{len(matches)} raw → {len(uniq)} unique → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
