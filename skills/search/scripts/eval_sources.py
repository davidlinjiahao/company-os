#!/usr/bin/env python3
"""Eval: Compare Parallel.ai + Firecrawl vs WebSearch-only.

Runs 5 diverse queries through each source and compares:
- Result count
- Unique domains (breadth)
- Date coverage (% of results with dates, confidence levels)
- Snippet length (depth of excerpts)
- URL overlap between sources

Usage:
    source ~/.company-os.env  # or export keys manually
    python3 skills/search/scripts/eval_sources.py

Requires: PARALLEL_API_KEY, FIRECRAWL_API_KEY in environment.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

# Add scripts dir to path (same pattern as last30days.py)
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from lib.parallel import search as parallel_search, normalize_results as parallel_normalize
from lib.firecrawl import search as firecrawl_search, normalize_results as firecrawl_normalize
from lib.websearch import extract_domain, extract_date_signals


EVAL_QUERIES = [
    "distributed systems architecture patterns 2025",
    "Claude Code MCP server best practices",
    "startup fundraising best practices 2025",
    "machine learning training dataset best practices",
    "1Password CLI team secret management developer workflow",
]


def google_search_baseline(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """Scrape Google search results as WebSearch baseline.

    Returns list of dicts with title, url, snippet.
    """
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}&num={num_results}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.9",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [WebSearch] Google fetch failed: {e}", file=sys.stderr)
        return []

    results = []
    # Extract search result blocks
    # Pattern: <a href="/url?q=URL&..."><h3>TITLE</h3></a>
    for match in re.finditer(
        r'<a[^>]*href="/url\?q=([^&"]+)&[^"]*"[^>]*>.*?<h3[^>]*>(.*?)</h3>',
        html,
        re.DOTALL,
    ):
        raw_url = urllib.parse.unquote(match.group(1))
        title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if raw_url.startswith("http") and title:
            results.append({"url": raw_url, "title": title, "snippet": ""})

    # Try to get snippets from nearby <span> tags
    # This is best-effort — Google HTML changes frequently
    for i, match in enumerate(
        re.finditer(r'class="[^"]*VwiC3b[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    ):
        snippet = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        if i < len(results):
            results[i]["snippet"] = snippet[:500]

    return results[:num_results]


def analyze_results(
    results: List[Dict[str, Any]], source_name: str
) -> Dict[str, Any]:
    """Analyze a set of results for eval metrics."""
    domains: Set[str] = set()
    dated = 0
    date_high = 0
    date_med = 0
    total_snippet_len = 0
    urls: Set[str] = set()

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        date = r.get("date")
        date_conf = r.get("date_confidence", "low")

        domain = extract_domain(url)
        if domain:
            domains.add(domain)
        urls.add(url.lower().rstrip("/"))

        if date:
            dated += 1
            if date_conf == "high":
                date_high += 1
            elif date_conf == "med":
                date_med += 1

        total_snippet_len += len(snippet)

    count = len(results)
    return {
        "source": source_name,
        "result_count": count,
        "unique_domains": len(domains),
        "domains": sorted(domains),
        "dated_results": dated,
        "date_pct": f"{dated/count*100:.0f}%" if count else "0%",
        "date_high": date_high,
        "date_med": date_med,
        "avg_snippet_len": int(total_snippet_len / count) if count else 0,
        "urls": urls,
    }


def run_eval():
    """Run the full eval."""
    parallel_key = os.environ.get("PARALLEL_API_KEY", "")
    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY", "")

    if not parallel_key:
        print("WARNING: PARALLEL_API_KEY not set — skipping Parallel.ai", file=sys.stderr)
    if not firecrawl_key:
        print("WARNING: FIRECRAWL_API_KEY not set — skipping Firecrawl", file=sys.stderr)

    all_results = []

    for i, query in enumerate(EVAL_QUERIES):
        print(f"\n{'='*60}")
        print(f"Query {i+1}/{len(EVAL_QUERIES)}: {query}")
        print(f"{'='*60}")

        query_results = {"query": query, "sources": {}}

        # 1. WebSearch baseline (Google scrape)
        print("  [1/3] WebSearch (Google)...", end="", flush=True)
        try:
            ws_raw = google_search_baseline(query, num_results=10)
            # Enrich with Date Detective
            ws_results = []
            for r in ws_raw:
                date, conf = extract_date_signals(r["url"], r["snippet"], r["title"])
                ws_results.append({
                    **r,
                    "date": date,
                    "date_confidence": conf,
                    "source_domain": extract_domain(r["url"]),
                })
            print(f" {len(ws_results)} results")
            query_results["sources"]["websearch"] = ws_results
        except Exception as e:
            print(f" ERROR: {e}")
            query_results["sources"]["websearch"] = []

        time.sleep(1)  # Rate limit

        # 2. Parallel.ai
        if parallel_key:
            print("  [2/3] Parallel.ai...", end="", flush=True)
            try:
                p_raw = parallel_search(parallel_key, query, max_results=10)
                p_items = parallel_normalize(p_raw)
                p_results = [item.to_dict() for item in p_items]
                print(f" {len(p_results)} results")
                query_results["sources"]["parallel"] = p_results
            except Exception as e:
                print(f" ERROR: {e}")
                query_results["sources"]["parallel"] = []
        else:
            query_results["sources"]["parallel"] = []

        time.sleep(0.5)

        # 3. Firecrawl
        if firecrawl_key:
            print("  [3/3] Firecrawl...", end="", flush=True)
            try:
                f_raw = firecrawl_search(firecrawl_key, query, limit=10)
                f_items = firecrawl_normalize(f_raw)
                f_results = [item.to_dict() for item in f_items]
                print(f" {len(f_results)} results")
                query_results["sources"]["firecrawl"] = f_results
            except Exception as e:
                print(f" ERROR: {e}")
                query_results["sources"]["firecrawl"] = []
        else:
            query_results["sources"]["firecrawl"] = []

        all_results.append(query_results)
        time.sleep(1)

    # Generate report
    print("\n\n")
    print("=" * 70)
    print("  EVAL REPORT: Parallel.ai + Firecrawl vs WebSearch-Only")
    print(f"  Generated: {datetime.now().isoformat()}")
    print("=" * 70)

    # Per-query analysis
    ws_totals = {"results": 0, "domains": set(), "dated": 0, "snippet_len": 0}
    p_totals = {"results": 0, "domains": set(), "dated": 0, "snippet_len": 0}
    f_totals = {"results": 0, "domains": set(), "dated": 0, "snippet_len": 0}
    combined_totals = {"results": 0, "domains": set(), "dated": 0, "unique_urls": set()}

    for qr in all_results:
        query = qr["query"]
        print(f"\n--- Query: {query} ---\n")

        ws = analyze_results(qr["sources"].get("websearch", []), "WebSearch")
        pa = analyze_results(qr["sources"].get("parallel", []), "Parallel.ai")
        fc = analyze_results(qr["sources"].get("firecrawl", []), "Firecrawl")

        # Print comparison table
        print(f"  {'Metric':<25} {'WebSearch':>12} {'Parallel':>12} {'Firecrawl':>12}")
        print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*12}")
        print(f"  {'Results':.<25} {ws['result_count']:>12} {pa['result_count']:>12} {fc['result_count']:>12}")
        print(f"  {'Unique domains':.<25} {ws['unique_domains']:>12} {pa['unique_domains']:>12} {fc['unique_domains']:>12}")
        print(f"  {'Has date (%)':.<25} {ws['date_pct']:>12} {pa['date_pct']:>12} {fc['date_pct']:>12}")
        print(f"  {'Date high-conf':.<25} {ws['date_high']:>12} {pa['date_high']:>12} {fc['date_high']:>12}")
        print(f"  {'Avg snippet len':.<25} {ws['avg_snippet_len']:>12} {pa['avg_snippet_len']:>12} {fc['avg_snippet_len']:>12}")

        # URL overlap
        ws_urls = ws["urls"]
        pa_urls = pa["urls"]
        fc_urls = fc["urls"]
        ws_pa_overlap = len(ws_urls & pa_urls)
        ws_fc_overlap = len(ws_urls & fc_urls)
        pa_fc_overlap = len(pa_urls & fc_urls)
        all_urls = ws_urls | pa_urls | fc_urls
        print(f"\n  URL overlap: WS∩P={ws_pa_overlap}  WS∩F={ws_fc_overlap}  P∩F={pa_fc_overlap}")
        print(f"  Combined unique URLs: {len(all_urls)}  (vs WebSearch-only: {len(ws_urls)})")

        # Unique results from Parallel/Firecrawl not in WebSearch
        p_unique = pa_urls - ws_urls
        f_unique = fc_urls - ws_urls
        new_urls = (pa_urls | fc_urls) - ws_urls
        print(f"  NEW URLs from P+F not in WebSearch: {len(new_urls)}")

        # Accumulate totals
        ws_totals["results"] += ws["result_count"]
        ws_totals["domains"].update(ws["domains"])
        ws_totals["dated"] += ws["dated_results"]
        ws_totals["snippet_len"] += ws["avg_snippet_len"] * ws["result_count"]

        p_totals["results"] += pa["result_count"]
        p_totals["domains"].update(pa["domains"])
        p_totals["dated"] += pa["dated_results"]
        p_totals["snippet_len"] += pa["avg_snippet_len"] * pa["result_count"]

        f_totals["results"] += fc["result_count"]
        f_totals["domains"].update(fc["domains"])
        f_totals["dated"] += fc["dated_results"]
        f_totals["snippet_len"] += fc["avg_snippet_len"] * fc["result_count"]

        combined_totals["domains"].update(ws["domains"])
        combined_totals["domains"].update(pa["domains"])
        combined_totals["domains"].update(fc["domains"])
        combined_totals["unique_urls"].update(all_urls)

    # Summary
    print("\n\n" + "=" * 70)
    print("  AGGREGATE SUMMARY (across all 5 queries)")
    print("=" * 70)

    print(f"\n  {'Metric':<30} {'WebSearch':>12} {'Parallel':>12} {'Firecrawl':>12} {'Combined':>12}")
    print(f"  {'-'*30} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")
    print(f"  {'Total results':.<30} {ws_totals['results']:>12} {p_totals['results']:>12} {f_totals['results']:>12} {ws_totals['results']+p_totals['results']+f_totals['results']:>12}")
    print(f"  {'Unique domains':.<30} {len(ws_totals['domains']):>12} {len(p_totals['domains']):>12} {len(f_totals['domains']):>12} {len(combined_totals['domains']):>12}")

    ws_date_pct = f"{ws_totals['dated']/ws_totals['results']*100:.0f}%" if ws_totals["results"] else "N/A"
    p_date_pct = f"{p_totals['dated']/p_totals['results']*100:.0f}%" if p_totals["results"] else "N/A"
    f_date_pct = f"{f_totals['dated']/f_totals['results']*100:.0f}%" if f_totals["results"] else "N/A"
    print(f"  {'Dated results (%)':.<30} {ws_date_pct:>12} {p_date_pct:>12} {f_date_pct:>12} {'':>12}")

    ws_avg_snip = int(ws_totals["snippet_len"] / ws_totals["results"]) if ws_totals["results"] else 0
    p_avg_snip = int(p_totals["snippet_len"] / p_totals["results"]) if p_totals["results"] else 0
    f_avg_snip = int(f_totals["snippet_len"] / f_totals["results"]) if f_totals["results"] else 0
    print(f"  {'Avg snippet length':.<30} {ws_avg_snip:>12} {p_avg_snip:>12} {f_avg_snip:>12} {'':>12}")

    # Verdict
    print("\n" + "-" * 70)
    print("  VERDICT")
    print("-" * 70)

    total_ws = ws_totals["results"]
    total_combined = ws_totals["results"] + p_totals["results"] + f_totals["results"]
    breadth_gain = len(combined_totals["domains"]) - len(ws_totals["domains"])

    print(f"\n  Adding Parallel.ai + Firecrawl provides:")
    print(f"    - {total_combined - total_ws} additional results ({total_combined} vs {total_ws})")
    print(f"    - {breadth_gain} more unique domains ({len(combined_totals['domains'])} vs {len(ws_totals['domains'])})")
    if p_totals["results"]:
        print(f"    - Parallel.ai: structured dates on {p_totals['dated']}/{p_totals['results']} results")
    if f_totals["results"]:
        print(f"    - Firecrawl: {f_totals['results']} results with optional page scraping")

    if total_combined > total_ws * 1.5:
        print(f"\n  >> RECOMMENDATION: Parallel+Firecrawl significantly expand coverage. KEEP.")
    elif total_combined > total_ws * 1.2:
        print(f"\n  >> RECOMMENDATION: Moderate improvement. Worth keeping for breadth.")
    else:
        print(f"\n  >> RECOMMENDATION: Marginal improvement. WebSearch alone may suffice.")

    # Save raw data
    output_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(output_path, "w") as f:
        # Convert sets to lists for JSON serialization
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Raw results saved to: {output_path}")


if __name__ == "__main__":
    run_eval()
