#!/usr/bin/env python3
"""
Reddit — [FOR HIRE] and open-to-work posts.

Reads each subreddit's public RSS feed (no OAuth) and scores posts against
the role profile. Subreddits come from the profile: `sources.reddit.subreddits`.

Known limits: RSS returns ~25 recent posts with no pagination, and Reddit
rate-limits / 403s aggressively from datacentre IPs. Treat this as a
recurring trickle source, not a one-shot sweep. A blocked feed is reported,
not fatal.

    reddit_forhire.py --profile profiles/my-role.json
    reddit_forhire.py --profile profiles/my-role.json --dry-run
"""
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import sourcelib as sl

NS = {"atom": "http://www.w3.org/2005/Atom"}
DEFAULT_SUBS = ["forhire", "ExperiencedDevs"]
OPEN_TO_WORK = [
    "for hire", "looking for work", "looking for a job", "open to work",
    "available for hire", "seeking opportunities", "open to opportunities",
]


def feed_url(sub: str, sort: str) -> str:
    return f"https://www.reddit.com/r/{sub}/{sort}/.rss?limit=100"


MAX_FEED_BYTES = 8 * 1024 * 1024


def fetch(url: str) -> bytes:
    return subprocess.run(
        ["curl", "-sS", "-A", sl.UA, "--max-time", "30",
         "--max-filesize", str(MAX_FEED_BYTES), url],
        capture_output=True, check=True,
    ).stdout


def parse(xml_bytes: bytes):
    # stdlib ElementTree, deliberately: the sweep must run with no pip install.
    # Python's expat does not resolve external entities, so XXE is not reachable
    # here; the residual risk is entity-expansion blowup, which the curl
    # --max-filesize cap above bounds. Do not parse untrusted local files here.
    if len(xml_bytes) > MAX_FEED_BYTES:
        raise ET.ParseError("feed larger than cap — refusing to parse")
    root = ET.fromstring(xml_bytes)
    posts = []
    for e in root.findall("atom:entry", NS):
        author_el = e.find("atom:author/atom:name", NS)
        link_el = e.find("atom:link", NS)
        content_el = e.find("atom:content", NS)
        cat_el = e.find("atom:category", NS)
        posts.append({
            "title": (e.findtext("atom:title", "", NS) or "").strip(),
            "author": (author_el.text if author_el is not None else "").removeprefix("/u/").removeprefix("u/"),
            "url": link_el.get("href") if link_el is not None else "",
            "created": (e.findtext("atom:updated", "", NS) or "")[:10],
            "body": sl.clean_html(content_el.text if content_el is not None else ""),
            "flair": cat_el.get("label") if cat_el is not None else "",
        })
    return posts


def is_open_to_work(post: dict) -> bool:
    blob = f"{post.get('title','')} {post.get('flair','')} {post.get('body','')}".lower()
    return any(p in blob for p in OPEN_TO_WORK)


def render(m):
    lines = [f"## [{m['author']}]({m['url']}) — score {m['score']} — r/{m['sub']} — {m['created']}"]
    lines.append(f"- **Title**: {m['title']}")
    for label, key in (("Location", "location"), ("Remote", "remote"),
                       ("Relocate", "relocate"), ("Tech", "tech"),
                       ("Rate", "rate"), ("Contact", "contact")):
        if m.get(key):
            lines.append(f"- **{label}**: {m[key]}")
    lines.append(f"- **Hits**: must={m['must']} · stack={m['stack']} · loc={m['loc']}")
    return lines


def main() -> int:
    ap = sl.base_parser(__doc__)
    ap.add_argument("--sort", default="new", choices=["new", "hot"], help="feed sort order")
    args = ap.parse_args()
    p = sl.load_or_die(args)

    cfg = p.source_cfg("reddit", subreddits=DEFAULT_SUBS)
    subs = list(cfg.get("subreddits") or DEFAULT_SUBS)

    if args.dry_run:
        return sl.dry_run("reddit", p,
                          queries=[feed_url(s, args.sort) for s in subs],
                          extra={"subreddits": subs, "sort": args.sort,
                                 "open_to_work_markers": OPEN_TO_WORK,
                                 "enabled": cfg.get("enabled", True)})

    if not cfg.get("enabled", True):
        print("reddit: disabled in this role profile — skipping.")
        return 0

    matches, blocked = [], []
    for sub in subs:
        print(f"r/{sub}")
        try:
            posts = parse(fetch(feed_url(sub, args.sort)))
        except (subprocess.CalledProcessError, ET.ParseError) as e:
            print(f"  ! blocked or unparseable: {e}", file=sys.stderr)
            blocked.append(sub)
            continue
        kept = 0
        for post in posts:
            if not is_open_to_work(post):
                continue
            s, must, stack, loc = p.score(f"{post['title']}\n{post['body']}")
            if s < p.min_score:
                continue
            matches.append({
                "sub": sub, "score": s, "must": must, "stack": stack, "loc": loc,
                **{k: post[k] for k in ("title", "author", "url", "created")},
                "location": sl.field(post["body"], ["Location", "Country"]),
                "remote": sl.field(post["body"], "Remote"),
                "relocate": sl.field(post["body"], ["Willing to relocate", "Relocate"]),
                "tech": sl.field(post["body"], ["Technologies", "Stack", "Skills"]),
                "rate": sl.field(post["body"], ["Rate", "Salary"]),
                "contact": sl.field(post["body"], ["Contact", "Email"]),
            })
            kept += 1
        print(f"  {len(posts)} posts → {kept} kept")
        time.sleep(2)

    uniq = sorted(sl.dedupe(matches), key=lambda m: m["score"], reverse=True)
    if args.limit:
        uniq = uniq[: args.limit]
    out = sl.write_report(uniq, sl.report_path(args, p, "reddit"),
                          f"Reddit open-to-work — {p.role}", render, p.min_score)
    if blocked:
        print(f"! blocked feeds (report these as un-swept): {', '.join(blocked)}", file=sys.stderr)
    print(f"{len(matches)} raw → {len(uniq)} unique → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
