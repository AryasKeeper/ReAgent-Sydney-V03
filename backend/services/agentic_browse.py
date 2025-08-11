"""
Enhanced Agentic Browse Service with Full Pipeline
Implements: Brave Search → Firecrawl → Browserless → AI Synthesis
"""
import asyncio
import httpx
import logging
from typing import List, Tuple, Dict, Optional
from services.search_brave import brave_search
from services.property_search import PropertySearchService
from config import settings
from services.ai_router import ai_router

logger = logging.getLogger(__name__)
property_service = PropertySearchService()


async def extract_content_firecrawl(url: str) -> Optional[str]:
    """Extract content from URL using Firecrawl API."""
    if not getattr(settings, "FIRECRAWL_API_KEY", None):
        logger.warning("Firecrawl API key not configured")
        return None
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.firecrawl.dev/v0/scrape",
                headers={"Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}"},
                json={
                    "url": url,
                    "formats": ["markdown"],
                    "onlyMainContent": True
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("markdown", "")
            logger.warning(f"Firecrawl returned {response.status_code} for {url}")
    except Exception as e:
        logger.error(f"Firecrawl error for {url}: {e}")
    return None


async def extract_content_browserless(url: str) -> Optional[str]:
    """Fallback: Extract content using Browserless API."""
    if not getattr(settings, "BROWSERLESS_TOKEN", None):
        logger.warning("Browserless token not configured")
        return None
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://chrome.browserless.io/content",
                headers={"Authorization": f"Bearer {settings.BROWSERLESS_TOKEN}"},
                json={
                    "url": url,
                    "waitForSelector": "body",
                    "bestAttempt": True
                }
            )
            if response.status_code == 200:
                return response.text[:5000]  # Limit content size
            logger.warning(f"Browserless returned {response.status_code} for {url}")
    except Exception as e:
        logger.error(f"Browserless error for {url}: {e}")
    return None


async def extract_url_content(url: str) -> str:
    """Extract content from URL with fallback chain."""
    # Try Firecrawl first
    content = await extract_content_firecrawl(url)
    if content:
        logger.info(f"Content extracted via Firecrawl for {url}")
        return content[:3000]  # Limit for synthesis
    
    # Fallback to Browserless
    content = await extract_content_browserless(url)
    if content:
        logger.info(f"Content extracted via Browserless for {url}")
        return content[:3000]
    
    # Final fallback: return URL only
    logger.warning(f"No content extraction available for {url}")
    return f"[Content from {url} could not be extracted]"


async def synthesize_content(query: str, contents: List[Tuple[str, str]]) -> str:
    """
    Synthesize extracted content into a coherent response.
    Non-streaming to avoid nested SSE issues.
    """
    if not contents:
        return "I couldn't extract content from the sources."
    
    # Build synthesis prompt
    synthesis_prompt = f"""Based on the following sources, provide a comprehensive answer to: {query}

Sources:
"""
    for url, content in contents:
        synthesis_prompt += f"\n---\nSource: {url}\n{content[:1500]}\n"
    
    synthesis_prompt += "\n---\nSynthesize the above information into a clear, informative response."
    
    try:
        # Use AI router for synthesis (non-streaming)
        response = ""
        async for chunk in ai_router.process_message(
            synthesis_prompt,
            session_id="synthesis",
            history=[],
            reasoning_effort="medium",
            verbosity="medium"
        ):
            response += chunk
        
        return response if response else "I found sources but couldn't synthesize them properly."
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        return "I found relevant sources but encountered an error during synthesis."


async def agentic_browse(query: str) -> Tuple[str, List[str]]:
    """
    Full browse pipeline: Search → Extract → Synthesize
    Returns: (synthesized_content, source_urls)
    """
    logger.info(f"Starting agentic browse for: {query}")
    
    # Step 1: Brave Search for URLs
    urls: List[str] = []
    data = await brave_search.search_cached(query, count=5, cache_key=f"brave:{query}")
    
    if data:
        urls = brave_search.extract_urls(data, limit=3)
        logger.info(f"Found {len(urls)} URLs from Brave search")
    
    if not urls:
        # Fallback to Tavily if no Brave results
        logger.warning("No URLs from Brave, trying Tavily fallback")
        fallback = await property_service._tavily_property_search({})  # type: ignore[attr-defined]
        if fallback:
            return fallback, []
        return "I couldn't find any relevant sources for your query.", []
    
    # Step 2: Extract content from URLs (parallel)
    logger.info(f"Extracting content from {len(urls)} URLs")
    extraction_tasks = [extract_url_content(url) for url in urls]
    contents = await asyncio.gather(*extraction_tasks)
    
    # Pair URLs with their content
    url_content_pairs = [(url, content) for url, content in zip(urls, contents) if content]
    
    if not url_content_pairs:
        # If no content extracted, return URLs only
        logger.warning("No content extracted, returning URLs only")
        summary = "I found these sources but couldn't extract their content:\n"
        summary += "\n".join(f"- {url}" for url in urls)
        return summary, urls
    
    # Step 3: Synthesize content
    logger.info(f"Synthesizing content from {len(url_content_pairs)} sources")
    synthesized = await synthesize_content(query, url_content_pairs)
    
    # Return synthesized content with source attribution
    return synthesized, urls