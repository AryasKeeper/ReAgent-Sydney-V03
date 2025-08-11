"""
Debug endpoints for testing web browsing functionality
These endpoints help isolate and test each component of the browse pipeline
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import logging

from services.query_analyzer import query_analyzer, QueryType
from services.agentic_browse import (
    agentic_browse,
    extract_content_firecrawl,
    extract_content_browserless,
    extract_url_content,
    synthesize_content
)
from services.search_brave import brave_search
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])


class DebugQueryRequest(BaseModel):
    query: str


class DebugURLRequest(BaseModel):
    url: str


class DebugSynthesisRequest(BaseModel):
    query: str
    contents: List[Dict[str, str]]  # [{"url": "...", "content": "..."}]


@router.post("/classify")
async def debug_classify_query(request: DebugQueryRequest):
    """Test query classification to see if it triggers WEB_SEARCH."""
    query_type, params = query_analyzer.analyze_query(request.query)
    
    return {
        "query": request.query,
        "query_type": query_type.value,
        "is_web_search": query_type == QueryType.WEB_SEARCH,
        "parameters": params,
        "required_tools": query_analyzer.get_required_tools(query_type)
    }


@router.post("/brave-search")
async def debug_brave_search(request: DebugQueryRequest):
    """Test Brave search API directly."""
    if not settings.BRAVE_API_KEY:
        raise HTTPException(status_code=503, detail="BRAVE_API_KEY not configured")
    
    try:
        # Try search
        data = await brave_search.search(request.query, count=5)
        
        if not data:
            return {
                "success": False,
                "error": "No results from Brave API",
                "api_key_configured": bool(settings.BRAVE_API_KEY)
            }
        
        # Extract URLs
        urls = brave_search.extract_urls(data, limit=5)
        
        return {
            "success": True,
            "query": request.query,
            "urls_found": urls,
            "url_count": len(urls),
            "raw_result_count": len(data.get("web", {}).get("results", [])),
            "sample_result": data.get("web", {}).get("results", [])[0] if data.get("web", {}).get("results") else None
        }
    except Exception as e:
        logger.exception("Brave search debug error")
        return {
            "success": False,
            "error": str(e),
            "api_key_configured": bool(settings.BRAVE_API_KEY)
        }


@router.post("/extract-firecrawl")
async def debug_extract_firecrawl(request: DebugURLRequest):
    """Test Firecrawl content extraction."""
    if not settings.FIRECRAWL_API_KEY:
        raise HTTPException(status_code=503, detail="FIRECRAWL_API_KEY not configured")
    
    try:
        content = await extract_content_firecrawl(request.url)
        
        return {
            "success": content is not None,
            "url": request.url,
            "content_length": len(content) if content else 0,
            "content_preview": content[:500] if content else None,
            "api_key_configured": bool(settings.FIRECRAWL_API_KEY)
        }
    except Exception as e:
        logger.exception("Firecrawl debug error")
        return {
            "success": False,
            "error": str(e),
            "api_key_configured": bool(settings.FIRECRAWL_API_KEY)
        }


@router.post("/extract-browserless")
async def debug_extract_browserless(request: DebugURLRequest):
    """Test Browserless content extraction."""
    if not settings.BROWSERLESS_TOKEN:
        raise HTTPException(status_code=503, detail="BROWSERLESS_TOKEN not configured")
    
    try:
        content = await extract_content_browserless(request.url)
        
        return {
            "success": content is not None,
            "url": request.url,
            "content_length": len(content) if content else 0,
            "content_preview": content[:500] if content else None,
            "token_configured": bool(settings.BROWSERLESS_TOKEN)
        }
    except Exception as e:
        logger.exception("Browserless debug error")
        return {
            "success": False,
            "error": str(e),
            "token_configured": bool(settings.BROWSERLESS_TOKEN)
        }


@router.post("/extract-any")
async def debug_extract_any(request: DebugURLRequest):
    """Test content extraction with fallback chain."""
    try:
        content = await extract_url_content(request.url)
        
        # Determine which service was used
        service_used = "fallback_message"
        if "Firecrawl" in content[:100] if content else "":
            service_used = "firecrawl"
        elif "Browserless" in content[:100] if content else "":
            service_used = "browserless"
        elif "[Content from" in content:
            service_used = "none_available"
        
        return {
            "success": True,
            "url": request.url,
            "service_used": service_used,
            "content_length": len(content),
            "content_preview": content[:500],
            "firecrawl_configured": bool(settings.FIRECRAWL_API_KEY),
            "browserless_configured": bool(settings.BROWSERLESS_TOKEN)
        }
    except Exception as e:
        logger.exception("Content extraction debug error")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/synthesize")
async def debug_synthesize(request: DebugSynthesisRequest):
    """Test AI synthesis of content."""
    if not (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY):
        raise HTTPException(status_code=503, detail="No AI provider configured")
    
    try:
        # Convert to expected format
        contents = [(item["url"], item["content"]) for item in request.contents]
        
        synthesized = await synthesize_content(request.query, contents)
        
        return {
            "success": True,
            "query": request.query,
            "source_count": len(contents),
            "synthesis_length": len(synthesized),
            "synthesis": synthesized,
            "ai_provider": "OpenAI" if settings.OPENAI_API_KEY else "Anthropic"
        }
    except Exception as e:
        logger.exception("Synthesis debug error")
        return {
            "success": False,
            "error": str(e),
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "anthropic_configured": bool(settings.ANTHROPIC_API_KEY)
        }


@router.post("/full-pipeline")
async def debug_full_pipeline(request: DebugQueryRequest):
    """Test the complete browse pipeline end-to-end."""
    try:
        # Run full pipeline
        summary, sources = await agentic_browse(request.query)
        
        return {
            "success": True,
            "query": request.query,
            "summary_length": len(summary),
            "summary": summary,
            "sources": sources,
            "source_count": len(sources),
            "configuration": {
                "brave_api": bool(settings.BRAVE_API_KEY),
                "firecrawl_api": bool(settings.FIRECRAWL_API_KEY),
                "browserless_token": bool(settings.BROWSERLESS_TOKEN),
                "ai_provider": "OpenAI" if settings.OPENAI_API_KEY else "Anthropic" if settings.ANTHROPIC_API_KEY else "None"
            }
        }
    except Exception as e:
        logger.exception("Full pipeline debug error")
        return {
            "success": False,
            "error": str(e),
            "configuration": {
                "brave_api": bool(settings.BRAVE_API_KEY),
                "firecrawl_api": bool(settings.FIRECRAWL_API_KEY),
                "browserless_token": bool(settings.BROWSERLESS_TOKEN),
                "ai_provider": "OpenAI" if settings.OPENAI_API_KEY else "Anthropic" if settings.ANTHROPIC_API_KEY else "None"
            }
        }


@router.get("/config")
async def debug_config():
    """Check current configuration for web browsing."""
    return {
        "web_browsing_ready": bool(
            settings.BRAVE_API_KEY and 
            (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)
        ),
        "apis_configured": {
            "brave_search": bool(settings.BRAVE_API_KEY),
            "firecrawl": bool(settings.FIRECRAWL_API_KEY),
            "browserless": bool(settings.BROWSERLESS_TOKEN),
            "tavily": bool(settings.TAVILY_API_KEY),
            "openai": bool(settings.OPENAI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY)
        },
        "minimum_requirements_met": bool(
            settings.BRAVE_API_KEY and 
            (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)
        ),
        "optimal_setup": bool(
            settings.BRAVE_API_KEY and
            settings.FIRECRAWL_API_KEY and
            (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)
        ),
        "missing_for_minimum": [] if (settings.BRAVE_API_KEY and (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)) else
            (["BRAVE_API_KEY"] if not settings.BRAVE_API_KEY else []) +
            (["AI provider (OPENAI_API_KEY or ANTHROPIC_API_KEY)"] if not (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY) else [])
    }