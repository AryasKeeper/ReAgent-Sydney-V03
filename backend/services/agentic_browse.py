from typing import List, Tuple
from services.search_brave import brave_search
from services.property_search import PropertySearchService


property_service = PropertySearchService()


async def agentic_browse(query: str) -> Tuple[str, List[str]]:
    """Plan: Brave discovery → list sources; leverage existing fallbacks.

    Returns a tuple of (summary_text, sources).
    """
    urls: List[str] = []
    # Use cached search for performance
    data = await brave_search.search_cached(query, count=5, cache_key=f"brave:{query}")
    if data:
        urls = brave_search.extract_urls(data, limit=3)

    if urls:
        summary = (
            "I found relevant sources:\n- " + "\n- ".join(urls) +
            "\n\nI can open and extract details if you want specifics."
        )
        return summary, urls

    # Fallback to Tavily-based quick insight via existing service
    fallback = await property_service._tavily_property_search({})  # type: ignore[attr-defined]
    if fallback:
        return fallback, []

    return "I'm unable to find sources right now.", []


