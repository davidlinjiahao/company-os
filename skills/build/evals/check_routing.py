#!/usr/bin/env python3
"""Routing-coverage checker for the /build dispatcher.

Pre-registered before the rebuilt skill existed. Verifies that the routing table in
skills/build/references/routing.md names 100% of the frozen practice-skill inventory
(GOLD.md section 1) and gives every one of them a non-empty "skip when" rule.

Also re-derives the inventory from the live environment and reports drift. Live drift that
ADDS a practice skill not in the gold list is a hard failure (the coverage claim would be
stale). Live drift that removes one is a warning (the machine changed; the contract did not).

Exit 0 only on full coverage.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ROUTING = SKILL_DIR / "references" / "routing.md"
GOLD = SKILL_DIR / "evals" / "GOLD.md"

# Frozen inventory (GOLD.md §1). Denominator of the coverage metric.
GOLD_SKILLS = [
    "brainstorming",
    "writing-plans",
    "executing-plans",
    "subagent-driven-development",
    "dispatching-parallel-agents",
    "using-git-worktrees",
    "test-driven-development",
    "systematic-debugging",
    "verification-before-completion",
    "requesting-code-review",
    "receiving-code-review",
    "finishing-a-development-branch",
    "using-superpowers",
    "writing-skills",
    "frontend-design",
    "dataviz",
]

# Skills the harness provides with no on-disk path; cannot be discovered by globbing.
HARNESS_PROVIDED = {"dataviz"}

EMPTY_CELL = {"", "-", "--", "n/a", "na", "tbd", "todo", "?"}


def live_inventory() -> tuple[set[str], list[str]]:
    """Re-derive the practice-skill inventory from disk. Returns (names, notes)."""
    notes: list[str] = []
    found: set[str] = set()
    cache = Path.home() / ".claude" / "plugins" / "cache" / "claude-plugins-official"

    sp_root = cache / "superpowers"
    if sp_root.is_dir():
        versions = sorted((d for d in sp_root.iterdir() if d.is_dir()), key=lambda p: p.name)
        if versions:
            skills_dir = versions[-1] / "skills"
            notes.append(f"superpowers version used: {versions[-1].name}")
            if skills_dir.is_dir():
                found |= {d.name for d in skills_dir.iterdir() if (d / "SKILL.md").exists()}
    else:
        notes.append("superpowers plugin cache not found on this machine")

    fd_root = cache / "frontend-design"
    if fd_root.is_dir():
        for skill_md in fd_root.glob("*/skills/*/SKILL.md"):
            found.add(skill_md.parent.name)
    else:
        notes.append("frontend-design plugin cache not found on this machine")

    found |= HARNESS_PROVIDED
    return found, notes


def parse_routing_rows(text: str) -> dict[str, str]:
    """Map skill name -> its 'skip when' cell, from every markdown table with a Skip column."""
    rows: dict[str, str] = {}
    lines = text.splitlines()
    skip_idx: int | None = None
    in_table = False

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            skip_idx = None
            continue

        cells = [c.strip() for c in stripped.strip("|").split("|")]

        if not in_table:
            lowered = [c.lower() for c in cells]
            hits = [i for i, c in enumerate(lowered) if "skip" in c]
            if hits:
                skip_idx = hits[0]
                in_table = True
            continue

        if set(stripped) <= set("|-: "):  # separator row
            continue

        if skip_idx is None or skip_idx >= len(cells):
            continue

        skip_cell = cells[skip_idx]
        for name in GOLD_SKILLS:
            # match the skill name in any cell of the row, ignoring the skip cell itself
            row_text = " ".join(c for i, c in enumerate(cells) if i != skip_idx)
            if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", row_text):
                # first table wins; later tables must not clobber a good entry
                if name not in rows or rows[name].lower() in EMPTY_CELL:
                    rows[name] = skip_cell
    return rows


def main() -> int:
    if not ROUTING.exists():
        print(f"FAIL: routing table not found at {ROUTING}")
        print("ROUTING COVERAGE: 0/%d" % len(GOLD_SKILLS))
        print("MISSING: " + ", ".join(GOLD_SKILLS))
        return 1

    text = ROUTING.read_text(encoding="utf-8")
    rows = parse_routing_rows(text)

    present = [s for s in GOLD_SKILLS if s in rows]
    missing = [s for s in GOLD_SKILLS if s not in rows]
    with_skip = [s for s in present if rows[s].strip().lower() not in EMPTY_CELL]
    no_skip = [s for s in present if rows[s].strip().lower() in EMPTY_CELL]

    total = len(GOLD_SKILLS)
    print(f"ROUTING COVERAGE: {len(present)}/{total}")
    print("MISSING: " + (", ".join(missing) if missing else "none"))
    print(f"SKIP-RULE COVERAGE: {len(with_skip)}/{total}")
    if no_skip:
        print("NO-SKIP-RULE: " + ", ".join(no_skip))

    live, notes = live_inventory()
    for n in notes:
        print(f"NOTE: {n}")
    extra = sorted(live - set(GOLD_SKILLS))
    absent = sorted(set(GOLD_SKILLS) - live)
    print("LIVE-DRIFT-EXTRA: " + (", ".join(extra) if extra else "none"))
    print("LIVE-DRIFT-ABSENT: " + (", ".join(absent) if absent else "none"))

    ok = not missing and not no_skip and not extra
    if extra:
        print("FAIL: live environment has practice skills absent from the frozen gold list; "
              "coverage denominator is stale. Update GOLD.md and re-run.")
    print("RESULT: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
