#!/usr/bin/env python3
"""
GitHub — top contributors as candidates.

Two lanes, both driven by the role profile:
  1. CURATED repos (`sources.github.curated_repos`) — the high-signal lane.
     Twenty well-chosen repos in the role's domain beat any free-text search.
  2. TRENDING repos for the profile's languages — the breadth lane, noisier.

Ranks each contributor by open-to-work signal, profile keyword hits against
the role profile, and reach. Needs GITHUB_TOKEN for a real crawl (60 req/hr
without one); resolves it from the environment, then
~/.hiring-scraper/credentials.json. Never from a personal vault or keychain.

    github_contributors.py --profile profiles/my-role.json --dry-run
    GITHUB_TOKEN=... github_contributors.py --profile profiles/my-role.json
"""
import json
import re
import subprocess
import sys
import time

import sourcelib as sl

API = "https://api.github.com"
OPEN_TO_WORK = [
    "looking for", "open to", "available for", "freelance", "for hire",
    "seeking", "founding engineer", "ex-", "previously",
]


def gh(url: str, token: str | None):
    headers = ["Accept: application/vnd.github+json"]
    if token:
        headers.append(f"Authorization: Bearer {token}")
    return json.loads(sl.curl(url, headers=headers))


def trending(lang: str, since: str, n: int, token: str | None):
    body = sl.curl(f"https://github.com/trending/{lang}?since={since}").decode("utf-8", "replace")
    repos = []
    for m in re.finditer(r'<h2 class="h3 lh-condensed">\s*<a[^>]+href="/([^/"]+)/([^"]+)"', body):
        repos.append(f"{m.group(1)}/{m.group(2)}")
        if len(repos) >= n:
            break
    return repos


def contributors(repo: str, n: int, token: str | None):
    try:
        data = gh(f"{API}/repos/{repo}/contributors?per_page={n + 5}", token)
    except (subprocess.CalledProcessError, json.JSONDecodeError, TypeError) as e:
        print(f"  ! contributors {repo}: {e}", file=sys.stderr)
        return []
    if not isinstance(data, list):
        return []
    return [c["login"] for c in data if c.get("login") and "[bot]" not in c["login"]][:n]


def score_user(u: dict, p: sl.RoleProfile):
    blob = " ".join(filter(None, [u.get("bio"), u.get("location"), u.get("company")]))
    kw_score, must, stack, loc = p.score(blob)
    bio_hits = [k for k in OPEN_TO_WORK if k in (u.get("bio") or "").lower()]
    followers = u.get("followers", 0)
    reach = 6 if followers >= 5000 else 4 if followers >= 1000 else 2 if followers >= 200 else 1 if followers >= 50 else 0
    total = kw_score + (5 if u.get("hireable") else 0) + len(bio_hits) * 3 + reach
    return total, must, stack, loc, bio_hits


def render(u):
    lines = [f"## [{u['login']}]({u['url']}) — score {u['score']}"]
    for label, key in (("Name", "name"), ("Location", "location"), ("Company", "company"),
                       ("Email", "email"), ("Site", "blog")):
        if u.get(key):
            lines.append(f"- **{label}**: {u[key]}")
    if u.get("bio"):
        lines.append(f"- **Bio**: {u['bio'][:200]}")
    lines.append(f"- **Followers**: {u['followers']} · **Hireable flag**: {u['hireable']}")
    lines.append(f"- **Found via**: {', '.join(u['repos'][:3])} ({u['lane']})")
    lines.append(f"- **Hits**: must={u['must']} · stack={u['stack']} · loc={u['loc']} · open-to-work={u['bio_hits']}")
    return lines


def main() -> int:
    ap = sl.base_parser(__doc__)
    ap.add_argument("--skip-trending", action="store_true", help="curated repos only (highest signal-to-noise)")
    args = ap.parse_args()
    p = sl.load_or_die(args)

    cfg = p.source_cfg("github", languages=[], curated_repos=[], trending_since="weekly")
    curated = list(cfg.get("curated_repos") or [])
    langs = list(cfg.get("languages") or [])
    since = cfg.get("trending_since", "weekly")

    if args.dry_run:
        return sl.dry_run(
            "github", p,
            queries=[f"{API}/repos/{r}/contributors" for r in curated]
            + ([] if args.skip_trending else [f"https://github.com/trending/{l}?since={since}" for l in langs]),
            extra={"curated_repos": curated, "languages": langs, "trending_since": since,
                   "token_present": bool(sl.creds().get("GITHUB_TOKEN")),
                   "enabled": cfg.get("enabled", True)},
        )

    if not cfg.get("enabled", True):
        print("github: disabled in this role profile — skipping.")
        return 0
    if not curated and not langs:
        print("github: profile lists no curated_repos and no languages — nothing to sweep.", file=sys.stderr)
        return 0

    token = sl.cred("GITHUB_TOKEN", "5000 req/hr instead of 60")
    repos_per_lang = 25 if token else 3
    per_repo = 5 if token else 3
    pause = 0.1 if token else 1.0

    lanes = [("curated", r) for r in curated]
    if not args.skip_trending:
        for lang in langs:
            try:
                lanes += [("trending", r) for r in trending(lang, since, repos_per_lang, token)]
            except subprocess.CalledProcessError as e:
                print(f"  ! trending/{lang}: {e}", file=sys.stderr)

    seen = {}
    for lane, repo in lanes:
        print(f"  [{lane}] {repo}")
        for login in contributors(repo, per_repo, token):
            if login in seen:
                seen[login]["repos"].append(repo)
                continue
            try:
                u = gh(f"{API}/users/{login}", token)
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                print(f"  ! user {login}: {e}", file=sys.stderr)
                continue
            total, must, stack, loc, bio_hits = score_user(u, p)
            seen[login] = {
                "login": login, "url": u.get("html_url"), "name": u.get("name"),
                "location": u.get("location"), "company": u.get("company"),
                "bio": u.get("bio"), "email": u.get("email"), "blog": u.get("blog"),
                "followers": u.get("followers", 0), "hireable": u.get("hireable"),
                "repos": [repo], "lane": lane, "score": total,
                "must": must, "stack": stack, "loc": loc, "bio_hits": bio_hits,
            }
            time.sleep(pause)
        time.sleep(pause)

    users = sorted(seen.values(), key=lambda u: u["score"], reverse=True)
    if args.limit:
        users = users[: args.limit]
    out = sl.write_report(users, sl.report_path(args, p, "github"),
                          f"GitHub contributors — {p.role}", render, p.min_score)
    print(f"{len(lanes)} repos → {len(users)} contributors → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
