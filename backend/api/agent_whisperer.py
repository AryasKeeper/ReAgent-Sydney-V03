"""Agent Whisperer chat endpoint with SSE streaming"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import asyncio
import uuid

from services.ai_router import ai_router
from services.session_manager import session_manager
from services.web_search import web_search
from services.property_search import property_search
from services.response_variety import get_greeting, get_search_intro
from services.query_analyzer import query_analyzer, QueryType
from utils.streaming import format_sse_chunk
from config import settings
from services.agentic_browse import agentic_browse
from services.rate_limit import check_rate_limit
from services.metrics import Stopwatch, incr_counter

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    messages: List[ChatMessage] = Field(default_factory=list)

def _llm_prefs_for(query_type: QueryType):
    """Return (effort, verbosity, allowed_tools, tool_choice) for GPT-5 Responses API."""
    effort = "minimal"
    verbosity = "low"
    allowed_tools = None
    tool_choice = None

    if query_type == QueryType.PROPERTY_ANALYSIS:
        effort = "medium"
        verbosity = "medium"
    elif query_type in (QueryType.WEATHER, QueryType.TIME, QueryType.NEWS):
        allowed_tools = [{"type": "function", "name": "tavily_search"}]
        tool_choice = {"type": "allowed_tools", "mode": "auto", "tools": allowed_tools}
    elif query_type == QueryType.PROPERTY_SEARCH:
        allowed_tools = [{"type": "function", "name": "property_search"}]
        tool_choice = {"type": "allowed_tools", "mode": "required", "tools": allowed_tools}
    elif query_type == QueryType.WEB_SEARCH:
        allowed_tools = [
            {"type": "function", "name": "brave_search"},
            {"type": "function", "name": "firecrawl_scrape"},
        ]
        tool_choice = {"type": "allowed_tools", "mode": "auto", "tools": allowed_tools}
    return effort, verbosity, allowed_tools, tool_choice

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, req: Request):
    """
    Main chat endpoint that returns SSE stream
    Compatible with Vercel AI SDK v3.4.33
    """
    try:
        req_id = req.headers.get('x-request-id') or str(uuid.uuid4())
        logger.info(f"[{req_id}] Chat request - Session: {request.session_id}, Message: {request.message[:50]}...")
        # Optional API key enforcement
        if getattr(settings, 'REQUIRE_API_KEY', False):
            provided = req.headers.get('x-api-key')
            if not provided or provided != getattr(settings, 'API_KEY', None):
                raise HTTPException(status_code=401, detail="Invalid API key")

        # Basic per-session rate limit
        allowed, remaining = await check_rate_limit(request.session_id, limit=60, window_seconds=60)
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please slow down.")
        
        # Stream the response
        async def generate():
            try:
                logger.info(f"Generator start - Live Mode Active")
                
                # Add greeting for new sessions
                if session_manager.should_introduce(request.session_id):
                    greeting = get_greeting()
                    yield format_sse_chunk(greeting)
                    session_manager.mark_introduced(request.session_id)
                
                # Analyze query to determine type and parameters
                query_type, params = query_analyzer.analyze_query(request.message)
                logger.info(f"Query analyzed - Type: {query_type}, Params: {params}")
                
                # Route based on query type
                if query_type == QueryType.GREETING:
                    # Friendly greeting response
                    yield format_sse_chunk("Hello! I'm Agent Whisperer, your Sydney real estate AI assistant. ")
                    yield format_sse_chunk("I can help you with property searches, market analysis, weather, news, and general questions. ")
                    yield format_sse_chunk("What would you like to know?")
                    
                elif query_type in [QueryType.WEATHER, QueryType.TIME]:
                    # Use web search for weather/time
                    timer = Stopwatch("weather_time").start()
                    result = await web_search.search_weather_time(request.message)
                    await timer.stop()
                    await incr_counter("weather_time")
                    yield format_sse_chunk(result)
                    
                elif query_type == QueryType.PROPERTY_SEARCH:
                    # Property search with intro
                    intro = get_search_intro()
                    yield format_sse_chunk(intro)
                    timer = Stopwatch("property_search").start()
                    result = await property_search.search_properties(request.message)
                    await timer.stop()
                    await incr_counter("property_search")
                    yield format_sse_chunk(result)
                    
                elif query_type == QueryType.PROPERTY_ANALYSIS:
                    # Use AI for property analysis
                    history = [{"role": m.role, "content": m.content} for m in request.messages] if request.messages else []
                    # Add property context to the query
                    enhanced_message = f"As a Sydney real estate expert, {request.message}"
                    effort, verbosity, allowed_tools, tool_choice = _llm_prefs_for(query_type)
                    logger.info(f"LLM prefs - effort={effort}, verbosity={verbosity}, tools={(allowed_tools or [])}")
                    async for chunk in ai_router.process_message(
                        enhanced_message,
                        request.session_id,
                        history,
                        reasoning_effort=effort,
                        verbosity=verbosity,
                        allowed_tools=allowed_tools,
                        tool_choice=tool_choice,
                    ):
                        yield format_sse_chunk(chunk)
                        
                elif query_type == QueryType.NEWS:
                    # For now, provide helpful response about news
                    yield format_sse_chunk("I'm currently unable to fetch live news. ")
                    yield format_sse_chunk("For the latest Sydney property news, check Domain.com.au or RealEstate.com.au. ")
                    yield format_sse_chunk("Is there something specific about Sydney real estate you'd like to know?")
                    
                elif query_type == QueryType.WEB_SEARCH:
                    # Prefer LLM Responses API with allowed_tools; fallback to agentic pipeline
                    tried_llm = False
                    if getattr(settings, 'OPENAI_USE_RESPONSES', False):
                        try:
                            effort, verbosity, allowed_tools, tool_choice = _llm_prefs_for(QueryType.WEB_SEARCH)
                            history = [{"role": m.role, "content": m.content} for m in request.messages] if request.messages else []
                            logger.info(f"WEB_SEARCH via LLM tools - effort={effort}, verbosity={verbosity}, tools={allowed_tools}")
                            async for chunk in ai_router.process_message(
                                request.message,
                                request.session_id,
                                history,
                                reasoning_effort=effort,
                                verbosity=verbosity,
                                allowed_tools=allowed_tools,
                                tool_choice=tool_choice,
                            ):
                                tried_llm = True
                                yield format_sse_chunk(chunk)
                        except Exception as e:
                            logger.warning(f"WEB_SEARCH LLM tools path failed: {e}; falling back to agentic browse")
                    if not tried_llm:
                        summary, sources = await agentic_browse(request.message)
                        yield format_sse_chunk(summary)
                        if sources:
                            yield format_sse_chunk("\nSources:\n" + "\n".join(f"- {s}" for s in sources))
                        
                else:  # QueryType.GENERAL_CHAT
                    # General AI conversation
                    history = [{"role": m.role, "content": m.content} for m in request.messages] if request.messages else []
                    effort, verbosity, allowed_tools, tool_choice = _llm_prefs_for(QueryType.GENERAL_CHAT)
                    logger.info(f"LLM prefs - effort={effort}, verbosity={verbosity}, tools={(allowed_tools or [])}")
                    async for chunk in ai_router.process_message(
                        request.message,
                        request.session_id,
                        history,
                        reasoning_effort=effort,
                        verbosity=verbosity,
                        allowed_tools=allowed_tools,
                        tool_choice=tool_choice,
                    ):
                        yield format_sse_chunk(chunk)
                
                # Send finish signal
                yield format_sse_chunk("", "finish")
                
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                logger.error(f"Stream generation error: {e}\nTraceback:\n{error_detail}")
                yield format_sse_chunk("I encountered an error. Please try again.", "text")
                yield format_sse_chunk("", "finish")
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Content-Type-Options": "nosniff",
                "X-Request-Id": req_id,
            }
        )
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Chat error: {e}\nTraceback:\n{error_detail}")
        async def error_stream():
            yield format_sse_chunk(
                "I'm having trouble processing your request. Please try again.",
                "text"
            )
            yield format_sse_chunk("", "finish")
        
        return StreamingResponse(
            error_stream(),
            media_type="text/plain"
        )
