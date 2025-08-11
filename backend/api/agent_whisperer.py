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
from utils.streaming import format_sse_chunk, detect_protocol_version
from config import settings
from services.agentic_browse import agentic_browse
from services.rate_limit import check_rate_limit
from services.metrics import Stopwatch, incr_counter
from services.metrics_collector import metrics_collector

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
    Compatible with both Vercel AI SDK v3.4.33 (legacy) and v5 (UI Message Stream)
    """
    try:
        req_id = req.headers.get('x-request-id') or str(uuid.uuid4())
        logger.info(f"[{req_id}] Chat request - Session: {request.session_id}, Message: {request.message[:50]}...")
        
        # Detect protocol version from headers
        headers_dict = dict(req.headers)
        protocol_version = detect_protocol_version(headers_dict)
        logger.info(f"[{req_id}] Using protocol version: {protocol_version}")
        
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
            # Start metrics tracking
            is_experiment = headers_dict.get('x-experiment-active', 'false') == 'true'
            experiment_id = headers_dict.get('x-experiment-id')
            metrics_collector.start_request(
                req_id,
                request.session_id,
                'v5' if protocol_version == 'v5' else 'v3',
                protocol_version,
                is_experiment,
                experiment_id
            )
            
            try:
                logger.info(f"Generator start - Live Mode Active, Protocol: {protocol_version}")
                
                # Send message start for v5 protocol
                if protocol_version == "v5":
                    yield format_sse_chunk("", "message_start", protocol_version)
                    metrics_collector.record_first_byte(req_id)
                
                # Add greeting for new sessions
                if session_manager.should_introduce(request.session_id):
                    greeting = get_greeting()
                    chunk = format_sse_chunk(greeting, "text", protocol_version)
                    yield chunk
                    metrics_collector.record_chunk(req_id, len(chunk))
                    metrics_collector.record_first_message(req_id)
                    session_manager.mark_introduced(request.session_id)
                
                # Analyze query to determine type and parameters
                # Check if web APIs are available for fallback handling
                has_web_apis = bool(settings.BRAVE_API_KEY and 
                                   (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY))
                
                # Use fallback-aware analysis
                query_type, params, fallback_notice = query_analyzer.analyze_query_with_fallback(
                    request.message, 
                    request.session_id,
                    has_web_apis
                )
                logger.info(f"Query analyzed - Type: {query_type}, Params: {params}, Fallback: {fallback_notice}")
                
                # Show fallback notice if applicable
                if fallback_notice and settings.BROWSE_FALLBACK_NOTICE:
                    chunk = format_sse_chunk(f"{fallback_notice}\n\n", "text", protocol_version)
                    yield chunk
                    metrics_collector.record_chunk(req_id, len(chunk))
                
                # Route based on query type
                if query_type == QueryType.GREETING:
                    # Friendly greeting response
                    yield format_sse_chunk("Hello! I'm Agent Whisperer, your Sydney real estate AI assistant. ", "text", protocol_version)
                    yield format_sse_chunk("I can help you with property searches, market analysis, weather, news, and general questions. ", "text", protocol_version)
                    yield format_sse_chunk("What would you like to know?", "text", protocol_version)
                    
                elif query_type in [QueryType.WEATHER, QueryType.TIME]:
                    # Use web search for weather/time
                    timer = Stopwatch("weather_time").start()
                    result = await web_search.search_weather_time(request.message)
                    await timer.stop()
                    await incr_counter("weather_time")
                    yield format_sse_chunk(result, "text", protocol_version)
                    
                elif query_type == QueryType.PROPERTY_SEARCH:
                    # Check if user explicitly requested live/up-to-date data
                    query_lower = request.message.lower()
                    wants_live_data = any(term in query_lower for term in [
                        "up-to-date", "up to date", "live", "current", "latest", "real-time"
                    ])
                    
                    if wants_live_data and has_web_apis:
                        # Use web browsing for live property data
                        logger.info("Property query requests live data - using web browsing")
                        summary, sources = await agentic_browse(request.message)
                        
                        # Remove any markdown formatting from the response
                        summary = summary.replace("**", "").replace("*", "")
                        
                        # Send sources metadata first if available
                        if sources:
                            yield format_sse_chunk(sources, "sources_meta", protocol_version)
                        
                        # Send the synthesized content
                        yield format_sse_chunk(summary, "text", protocol_version)
                        
                        # Append sources in text for backward compatibility (no markdown)
                        if sources:
                            yield format_sse_chunk("\n\nSources:\n" + "\n".join(f"- {s}" for s in sources), "text", protocol_version)
                    else:
                        # Regular property search with intro
                        intro = get_search_intro()
                        yield format_sse_chunk(intro, "text", protocol_version)
                        timer = Stopwatch("property_search").start()
                        result = await property_search.search_properties(request.message)
                        await timer.stop()
                        await incr_counter("property_search")
                        yield format_sse_chunk(result, "text", protocol_version)
                    
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
                        yield format_sse_chunk(chunk, "text", protocol_version)
                        
                elif query_type == QueryType.NEWS:
                    # For now, provide helpful response about news
                    yield format_sse_chunk("I'm currently unable to fetch live news. ", "text", protocol_version)
                    yield format_sse_chunk("For the latest Sydney property news, check Domain.com.au or RealEstate.com.au. ", "text", protocol_version)
                    yield format_sse_chunk("Is there something specific about Sydney real estate you'd like to know?", "text", protocol_version)
                    
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
                                yield format_sse_chunk(chunk, "text", protocol_version)
                        except Exception as e:
                            logger.warning(f"WEB_SEARCH LLM tools path failed: {e}; falling back to agentic browse")
                    if not tried_llm:
                        summary, sources = await agentic_browse(request.message)
                        
                        # Remove any markdown formatting from the response
                        summary = summary.replace("**", "").replace("*", "")
                        
                        # Send sources metadata first (as SSE type 8)
                        if sources:
                            yield format_sse_chunk(sources, "sources_meta", protocol_version)
                        
                        # Then send the synthesized content
                        yield format_sse_chunk(summary, "text", protocol_version)
                        
                        # Optionally append sources in text format for backward compatibility (no markdown)
                        if sources:
                            yield format_sse_chunk("\n\nSources:\n" + "\n".join(f"- {s}" for s in sources), "text", protocol_version)
                        
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
                        yield format_sse_chunk(chunk, "text", protocol_version)
                
                # Send finish signal
                yield format_sse_chunk("", "finish", protocol_version)
                
                # Complete metrics tracking
                metrics_collector.complete_request(req_id)
                
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                logger.error(f"Stream generation error: {e}\nTraceback:\n{error_detail}")
                metrics_collector.record_error(req_id, str(e))
                yield format_sse_chunk("I encountered an error. Please try again.", "text", protocol_version)
                yield format_sse_chunk("", "finish", protocol_version)
                metrics_collector.complete_request(req_id)
        
        # Set appropriate headers based on protocol version
        response_headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Content-Type-Options": "nosniff",
            "X-Request-Id": req_id,
        }
        
        # Add v5-specific header if using UI Message Stream protocol
        if protocol_version == "v5":
            response_headers["x-vercel-ai-ui-message-stream"] = "v1"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream" if protocol_version == "v5" else "text/plain",
            headers=response_headers
        )
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Chat error: {e}\nTraceback:\n{error_detail}")
        async def error_stream():
            # Use v3 protocol for error responses when protocol_version is not available
            yield format_sse_chunk(
                "I'm having trouble processing your request. Please try again.",
                "text",
                "v3"
            )
            yield format_sse_chunk("", "finish", "v3")
        
        return StreamingResponse(
            error_stream(),
            media_type="text/plain"
        )
