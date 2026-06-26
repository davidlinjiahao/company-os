"""Parallel.ai Search API client for search skill."""

from typing import Any, Dict, List, Optional

from . import http, schema
from .websearch import extract_domain


SEARCH_URL = "https://api.parallel.ai/v1beta/search"
BETA_HEADER = "search-extract-2025-10-10"


def search(
    api_key: str,
    topic: str,
    max_results: int = 10,
    exclude_domains: Optional[List[str]] = None,
    after_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Search via Parallel.ai Search API.

    Args:
        api_key: Parallel API key
        topic: Search topic / objective
        max_results: Max results to return
        exclude_domains: Domains to exclude (e.g., reddit.com, x.com)
        after_date: Only include results after this date (YYYY-MM-DD)

    Returns:
        Raw API response dict
    """
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "parallel-beta": BETA_HEADER,
    }

    payload: Dict[str, Any] = {
        "objective": topic,
        "search_queries": [topic],
        "max_results": max_results,
        "excerpts": {"max_chars_per_result": 3000},
    }

    source_policy: Dict[str, Any] = {}
    if exclude_domains:
        source_policy["exclude_domains"] = exclude_domains
    if after_date:
        source_policy["after_date"] = after_date
    if source_policy:
        payload["source_policy"] = source_policy

    return http.post(SEARCH_URL, payload, headers=headers, timeout=30)


def normalize_results(
    response: Dict[str, Any],
) -> List[schema.WebSearchItem]:
    """Normalize Parallel.ai results to WebSearchItem objects.

    Parallel.ai returns structured publish_date, so date_confidence is 'high'.

    Args:
        response: Raw Parallel.ai API response

    Returns:
        List of WebSearchItem objects
    """
    items = []
    results = response.get("results", [])

    for i, result in enumerate(results):
        url = result.get("url", "")
        if not url:
            continue

        title = result.get("title", "")
        excerpts = result.get("excerpts", [])
        snippet = excerpts[0][:500] if excerpts else ""
        publish_date = result.get("publish_date")

        items.append(schema.WebSearchItem(
            id=f"P{i+1}",
            title=title[:200],
            url=url,
            source_domain=extract_domain(url),
            snippet=snippet,
            date=publish_date,
            date_confidence="high" if publish_date else "low",
            relevance=0.7,  # Parallel.ai doesn't return relevance; default high
        ))

    return items
