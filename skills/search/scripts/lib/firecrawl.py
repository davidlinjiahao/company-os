"""Firecrawl Search API client for search skill."""

from typing import Any, Dict, List, Optional

from . import http, schema
from .websearch import extract_date_signals, extract_domain


SEARCH_URL = "https://api.firecrawl.dev/v2/search"


def search(
    api_key: str,
    topic: str,
    limit: int = 10,
    time_filter: Optional[str] = None,
    scrape: bool = False,
) -> Dict[str, Any]:
    """Search via Firecrawl Search API.

    Args:
        api_key: Firecrawl API key (fc-...)
        topic: Search query
        limit: Number of results (max 20)
        time_filter: Time filter — 'qdr:d' (day), 'qdr:w' (week), 'qdr:m' (month)
        scrape: If True, also scrape page content (costs more credits)

    Returns:
        Raw API response dict
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "query": topic,
        "limit": min(limit, 20),
    }

    if time_filter:
        payload["tbs"] = time_filter

    if scrape:
        payload["scrapeOptions"] = {
            "formats": ["markdown"],
            "onlyMainContent": True,
        }

    return http.post(SEARCH_URL, payload, headers=headers, timeout=30)


def normalize_results(
    response: Dict[str, Any],
) -> List[schema.WebSearchItem]:
    """Normalize Firecrawl results to WebSearchItem objects.

    Firecrawl doesn't return dates, so we use Date Detective extraction.

    Args:
        response: Raw Firecrawl API response

    Returns:
        List of WebSearchItem objects
    """
    items = []

    # Results can be in response.data.web or response.data directly
    data = response.get("data", {})
    if isinstance(data, dict):
        results = data.get("web", [])
    elif isinstance(data, list):
        results = data
    else:
        results = []

    for i, result in enumerate(results):
        if not isinstance(result, dict):
            continue

        url = result.get("url", "")
        if not url:
            continue

        title = result.get("title", "")
        # Use markdown content if scraped, otherwise description
        snippet = result.get("markdown", result.get("description", ""))
        if snippet and len(snippet) > 500:
            snippet = snippet[:500]

        # Date Detective — extract from URL/snippet/title
        date, date_confidence = extract_date_signals(url, snippet or "", title)

        items.append(schema.WebSearchItem(
            id=f"F{i+1}",
            title=title[:200],
            url=url,
            source_domain=extract_domain(url),
            snippet=snippet or "",
            date=date,
            date_confidence=date_confidence,
            relevance=0.6,  # Firecrawl doesn't return relevance; default moderate
        ))

    return items
