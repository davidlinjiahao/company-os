#!/usr/bin/env python3
"""
Shared library for the /source sweep scripts.

Everything role-specific lives in a ROLE PROFILE (a JSON file). No script in
this directory hardcodes a company, a stack, or a geography. Swap the profile,
get a different search.

Standard library only — the sweep must run in a sandbox with no pip install.

Run `python3 sourcelib.py --selftest` for a dependency-free smoke check.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

UA = "Mozilla/5.0 (compatible; source-sweep/2.0)"

CREDS_PATH = Path(
    os.environ.get("HIRING_SCRAPER_CREDENTIALS", Path.home() / ".hiring-scraper" / "credentials.json")
)

REQUIRED_TOP = ("role", "keywords")
DEFAULT_WEIGHTS = {"must": 4, "stack": 2, "location": 1}


class ProfileError(ValueError):
    """Raised when a role profile is missing or malformed."""


# --------------------------------------------------------------------------
# Role profile
# --------------------------------------------------------------------------


class RoleProfile:
    """A hiring need, in machine-readable form. See profiles/TEMPLATE.json."""

    def __init__(self, data: dict, path: Path | None = None):
        self.path = path
        self.data = data
        self._validate()

        self.role: str = data["role"].strip()
        self.context: str = (data.get("context") or "").strip()
        self.locations: list[str] = list(data.get("locations") or [])
        self.min_score: int = int(data.get("min_score", 6))
        self.weights: dict = {**DEFAULT_WEIGHTS, **(data.get("weights") or {})}
        kw = data["keywords"]
        self.must: list[str] = list(kw.get("must") or [])
        self.stack: list[str] = list(kw.get("stack") or [])
        self.loc_kw: list[str] = list(kw.get("location") or [])
        self.sources: dict = dict(data.get("sources") or {})
        self.abar_legs: list[str] = list(data.get("abar_legs") or [])
        self.exclude: list[str] = list(data.get("exclude") or [])

    # -- validation --------------------------------------------------------

    def _validate(self):
        d = self.data
        if not isinstance(d, dict):
            raise ProfileError("invalid role profile: top level must be a JSON object")
        for key in REQUIRED_TOP:
            if key not in d:
                raise ProfileError(
                    f"invalid role profile: missing required field '{key}'. "
                    "See profiles/TEMPLATE.json."
                )
        if not isinstance(d["role"], str) or not d["role"].strip():
            raise ProfileError("invalid role profile: 'role' must be a non-empty string")
        kw = d["keywords"]
        if not isinstance(kw, dict):
            raise ProfileError("invalid role profile: 'keywords' must be an object")
        must = kw.get("must")
        if not isinstance(must, list) or not must:
            raise ProfileError(
                "invalid role profile: 'keywords.must' must be a non-empty list — "
                "these are the signals that define the A-bar, and an empty list "
                "would silently sweep the whole internet."
            )

    @classmethod
    def load(cls, path) -> "RoleProfile":
        p = Path(path).expanduser()
        if not p.exists():
            raise ProfileError(f"invalid role profile: file not found: {p}")
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            raise ProfileError(f"invalid role profile: not valid JSON ({e})") from e
        return cls(data, p)

    # -- derived -----------------------------------------------------------

    @property
    def slug(self) -> str:
        s = unicodedata.normalize("NFKD", self.role)
        s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
        return s or "role"

    def source_cfg(self, name: str, **defaults) -> dict:
        cfg = dict(defaults)
        cfg.update(self.sources.get(name) or {})
        cfg.setdefault("enabled", True)
        return cfg

    def score(self, text: str):
        """(score, must_hits, stack_hits, location_hits). Word-boundary matched
        for ASCII terms; substring for CJK and other scripts with no word breaks."""
        if not text:
            return 0, [], [], []
        lower = text.lower()

        def hits(terms):
            found = []
            for t in terms:
                tl = t.lower()
                if not tl:
                    continue
                if tl.isascii():
                    if re.search(rf"(?<![a-z0-9]){re.escape(tl)}(?![a-z0-9])", lower):
                        found.append(t)
                elif tl in lower:
                    found.append(t)
            return found

        m, s, l = hits(self.must), hits(self.stack), hits(self.loc_kw)
        total = (
            len(m) * self.weights["must"]
            + len(s) * self.weights["stack"]
            + len(l) * self.weights["location"]
        )
        return total, m, s, l

    def summary(self) -> dict:
        """Deterministic, diffable view of everything a scraper will act on."""
        return {
            "role": self.role,
            "context": self.context,
            "locations": self.locations,
            "min_score": self.min_score,
            "weights": self.weights,
            "keywords": {"must": self.must, "stack": self.stack, "location": self.loc_kw},
            "sources": self.sources,
            "abar_legs": self.abar_legs,
            "exclude": self.exclude,
        }


# --------------------------------------------------------------------------
# Credentials — env first, then ~/.hiring-scraper/credentials.json. Never a vault.
# --------------------------------------------------------------------------


KNOWN_CREDS = (
    "GITHUB_TOKEN",
    "WAAS_COOKIE",
    "OPENAI_API_KEY",
    "EXA_API_KEY",
    "FIRECRAWL_API_KEY",
    "X_BEARER_TOKEN",
    "UNIPILE_DSN",
    "UNIPILE_API_KEY",
)


def creds() -> dict:
    out = {}
    if CREDS_PATH.exists():
        try:
            loaded = json.loads(CREDS_PATH.read_text())
            out.update({k: v for k, v in loaded.items() if isinstance(v, str) and v.strip()})
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ! could not read {CREDS_PATH}: {e}", file=sys.stderr)
    for k in set(out) | set(KNOWN_CREDS):
        v = os.environ.get(k, "")
        if v.strip():
            out[k] = v  # env always wins
    return out


def cred(name: str, why: str = "") -> str | None:
    """Fetch one credential, or return None with a skip message. Never raises —
    a missing credential degrades one lane, it does not fail the sweep."""
    v = creds().get(name)
    if v:
        return v
    hint = f" ({why})" if why else ""
    print(
        f"  ~ {name} not set{hint} — skipping this lane.\n"
        f"    set it in the environment, or add it to {CREDS_PATH} "
        f"(see credentials.example.json).",
        file=sys.stderr,
    )
    return None


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------


def curl(url: str, headers=None, timeout=30) -> bytes:
    """Shell out to curl. Some hosts fingerprint Python's TLS and refuse urllib."""
    args = ["curl", "-sS", "-L", "-A", UA, "--max-time", str(timeout)]
    for h in headers or []:
        args += ["-H", h]
    args.append(url)
    return subprocess.run(args, capture_output=True, check=True).stdout


def get_json(url: str, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def clean_html(s: str) -> str:
    if not s:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "\n", s))


def field(text: str, names) -> str:
    """Pull `Label: value` style self-report fields out of free text."""
    if isinstance(names, str):
        names = [names]
    for name in names:
        pat = rf"^\s*\**\s*{re.escape(name)}\s*\**\s*[:：]\s*(.+?)$"
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()[:300]
    return ""


def dedupe(entries, key="author"):
    """Keep the highest-scoring entry per identity."""
    best = {}
    for e in entries:
        k = e.get(key)
        if not k:
            continue
        if k not in best or e.get("score", 0) > best[k].get("score", 0):
            best[k] = e
    return list(best.values())


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def out_dir(args) -> Path:
    d = Path(
        getattr(args, "out", None)
        or os.environ.get("SOURCE_OUT_DIR")
        or "candidates"
    ).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d


def report_path(args, profile: RoleProfile, source: str) -> Path:
    return out_dir(args) / f"{date.today().isoformat()}_{profile.slug}_{source}.md"


def write_report(entries, path: Path, title: str, render, min_score: int | None = None) -> Path:
    lines = [f"# {title} — {len(entries)} matches", ""]
    scores = sorted(e.get("score", e.get("_score", 0)) for e in entries)
    if scores:
        n = len(scores)
        p50, p90 = scores[n // 2], scores[min(n - 1, int(n * 0.9))]
        lines += [
            f"_Triage scores: min {scores[0]} · p50 {p50} · p90 {p90} · max {scores[-1]}"
            + (f" · cutoff {min_score}" if min_score is not None else "")
            + ". This is a keyword score, NOT a grade — it only says a human should look._",
            "",
        ]
        if n > 150 and min_score is not None and min_score <= p50:
            print(
                f"  ~ {n} entries kept and the cutoff ({min_score}) sits at or below the median "
                f"({p50}). The keyword filter is not discriminating for this profile — raise "
                f"min_score toward p90 ({p90}), or make the 'must' terms more specific.",
                file=sys.stderr,
            )
    for e in entries:
        lines.extend(render(e))
        lines.append("")
    path.write_text("\n".join(lines))
    return path


# --------------------------------------------------------------------------
# CLI plumbing
# --------------------------------------------------------------------------


def base_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--profile", required=True, help="path to a role profile JSON (see profiles/TEMPLATE.json)")
    p.add_argument("--out", help="output directory (default: ./candidates, or $SOURCE_OUT_DIR)")
    p.add_argument("--limit", type=int, default=0, help="cap on items fetched (0 = source default)")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="resolve the profile, print the exact queries this run would issue, make no network calls",
    )
    return p


def load_or_die(args) -> RoleProfile:
    """Load the profile, or exit(2) with a message naming the problem."""
    try:
        return RoleProfile.load(args.profile)
    except ProfileError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)


def dry_run(source: str, profile: RoleProfile, queries, extra=None) -> int:
    """Deterministic config dump. Diffing two profiles' dumps proves parameterization."""
    payload = {
        "DRY RUN": source,
        "profile_path": str(profile.path),
        "queries": list(queries),
        "profile": profile.summary(),
    }
    if extra:
        payload["resolved"] = extra
    print("DRY RUN — no network calls made")
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------


def _selftest() -> int:
    fixtures = Path(__file__).resolve().parent.parent / "evals" / "fixtures"
    p = RoleProfile.load(fixtures / "test-role.json")
    assert p.slug, "slug empty"
    s, m, st, lo = p.score("Founding engineer, shipped BLE + React Native app in San Francisco")
    assert s > 0 and m and lo, f"scoring produced nothing: {s} {m} {st} {lo}"
    s2, _, _, _ = p.score("I enjoy long walks")
    assert s2 == 0, "unrelated text scored non-zero"
    try:
        RoleProfile.load(fixtures / "bad-role.json")
    except ProfileError as e:
        assert "keywords" in str(e) or "role" in str(e), e
    else:
        raise AssertionError("bad profile did not raise")
    print("sourcelib selftest OK")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="run a dependency-free smoke check")
    a = ap.parse_args()
    sys.exit(_selftest() if a.selftest else (ap.print_help() or 0))
