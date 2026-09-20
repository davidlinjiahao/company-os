#!/usr/bin/env python3
"""
Merge every per-source report for one role into a single ranked file, with
cross-source identity dedupe.

A candidate who shows up in two independent sources is a much stronger signal
than one who scores high in a single feed, so multi-source hits are ranked
first and labelled.

    merge.py --profile profiles/my-role.json
    merge.py --profile profiles/my-role.json --dry-run
"""
import re
import sys
from collections import defaultdict
from datetime import date

import sourcelib as sl

GH = re.compile(r"github\.com/([A-Za-z0-9_-]+)")
X = re.compile(r"(?:x\.com|twitter\.com)/([A-Za-z0-9_]{2,15})|(?:^|[\s>(])@([A-Za-z0-9_]{3,15})\b")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Handles that are never a person.
NOT_PEOPLE = {
    "issues", "pull", "wiki", "blog", "search", "trending", "marketplace",
    "settings", "explore", "topics", "collections", "events", "sponsors",
    "notifications", "new", "login", "signup", "orgs", "features", "about",
}
MAIL_HOSTS = {
    "gmail", "outlook", "proton", "protonmail", "icloud", "yahoo",
    "fastmail", "hotmail", "hey", "duck", "simplelogin",
}


def identities(block: str):
    ids = {("email", e.lower()) for e in EMAIL.findall(block)}
    gh = {h.lower() for h in GH.findall(block) if h.lower() not in NOT_PEOPLE and len(h) >= 3}
    if len(gh) == 1:  # a lone handle is the profile owner; many are repo links
        ids.add(("gh", next(iter(gh))))
    xs = set()
    for m in X.finditer(block):
        h = (m.group(1) or m.group(2) or "").lower()
        if h and h not in NOT_PEOPLE and h not in MAIL_HOSTS and len(h) >= 4:
            xs.add(h)
    if len(xs) == 1:
        ids.add(("x", next(iter(xs))))
    return ids


def parse_report(path):
    source = re.sub(rf"^\d{{4}}-\d{{2}}-\d{{2}}_.*?_(.+)\.md$", r"\1", path.name)
    entries = []
    for chunk in re.split(r"\n## ", path.read_text())[1:]:
        block = "## " + chunk.strip()
        m = re.search(r"score (\d+)", block)
        entries.append({
            "source": source,
            "block": block,
            "score": int(m.group(1)) if m else 0,
            "ids": identities(block),
        })
    return entries


def main() -> int:
    ap = sl.base_parser(__doc__)
    ap.add_argument("--date", default=date.today().isoformat(), help="report date prefix to merge (YYYY-MM-DD)")
    ap.add_argument("--top-single", type=int, default=50, help="how many single-source entries to keep")
    args = ap.parse_args()
    p = sl.load_or_die(args)

    d = sl.out_dir(args)
    pattern = f"{args.date}_{p.slug}_*.md"
    files = sorted(f for f in d.glob(pattern) if not f.name.endswith("_merged.md"))

    if args.dry_run:
        return sl.dry_run("merge", p, queries=[f"local glob {d}/{pattern}"],
                          extra={"files_found": [f.name for f in files], "top_single": args.top_single})

    if not files:
        print(f"no reports matching {d}/{pattern} — run the source scripts first.", file=sys.stderr)
        return 1

    entries = []
    for f in files:
        e = parse_report(f)
        print(f"  {f.name}: {len(e)} entries")
        entries.extend(e)

    parent = list(range(len(entries)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(entries)):
        for j in range(i):
            if entries[i]["ids"] & entries[j]["ids"]:
                parent[find(i)] = find(j)

    clusters = defaultdict(list)
    for i in range(len(entries)):
        clusters[find(i)].append(entries[i])

    merged = []
    for items in clusters.values():
        sources = sorted({it["source"] for it in items})
        top = max(it["score"] for it in items)
        merged.append({
            "sources": sources, "items": items,
            "score": min(sum(it["score"] for it in items), top * 2),
            "multi": len(sources) >= 2,
        })
    merged.sort(key=lambda m: (not m["multi"], -m["score"]))

    multi = [m for m in merged if m["multi"]]
    single = [m for m in merged if not m["multi"]]
    lines = [
        f"# {p.role} — merged sweep, {args.date}",
        "",
        f"{len(merged)} candidates from {len(files)} source reports · {len(multi)} appear in 2+ sources.",
        "",
        "> This is RAW SWEEP OUTPUT, not a candidate list. Nothing here has been",
        "> checked against the A-bar yet. Filtering is the next step, and it is",
        "> the step that decides quality.",
        "",
        "## Multi-source (highest prior)",
        "",
    ]
    if not multi:
        lines.append("_none — every candidate came from exactly one source._\n")
    for m in multi:
        lines.append(f"### {' + '.join(m['sources'])} — score {m['score']}")
        for it in m["items"]:
            lines.append(f"<details><summary>{it['source']}</summary>\n\n{it['block']}\n\n</details>")
        lines.append("")
    lines += ["## Single-source", ""]
    for m in single[: args.top_single]:
        lines.append(f"### [{m['items'][0]['source']}] — score {m['score']}")
        lines.append(m["items"][0]["block"])
        lines.append("")

    out = d / f"{args.date}_{p.slug}_merged.md"
    out.write_text("\n".join(lines))
    print(f"{len(merged)} candidates ({len(multi)} multi-source) → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
