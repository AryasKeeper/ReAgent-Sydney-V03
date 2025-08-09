"""Agent Whisperer chat endpoint with SSE streaming"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import asyncio

from services.ai_router_fixed import fixed_ai_router as ai_router
from services.session_manager import session_manager
from services.web_search import web_search
from services.property_search import property_search
from services.response_variety import get_greeting, get_search_intro
from services.query_analyzer import query_analyzer, QueryType
from utils.streaming import format_sse_chunk
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    messages: List[ChatMessage] = Field(default_factory=list)

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Main chat endpoint that returns SSE stream
    Compatible with Vercel AI SDK v3.4.33
    """
    try:
        logger.info(f"Chat request - Session: {request.session_id}, Message: {request.message[:50]}...")
        
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
                    result = await web_search.search_weather_time(request.message)
                    yield format_sse_chunk(result)
                    
                elif query_type == QueryType.PROPERTY_SEARCH:
                    # Property search with intro
                    intro = get_search_intro()
                    yield format_sse_chunk(intro)
                    result = await property_search.search_properties(request.message)
                    yield format_sse_chunk(result)
                    
                elif query_type == QueryType.PROPERTY_ANALYSIS:
                    # Use AI for property analysis
                    history = [{"role": m.role, "content": m.content} for m in request.messages] if request.messages else []
                    # Add property context to the query
                    enhanced_message = f"As a Sydney real estate expert, {request.message}"
                    async for chunk in ai_router.process_message(
                        enhanced_message, 
                        request.session_id,
                        history
                    ):
                        yield format_sse_chunk(chunk)
                        
                elif query_type == QueryType.NEWS:
                    # For now, provide helpful response about news
                    yield format_sse_chunk("I'm currently unable to fetch live news. ")
                    yield format_sse_chunk("For the latest Sydney property news, check Domain.com.au or RealEstate.com.au. ")
                    yield format_sse_chunk("Is there something specific about Sydney real estate you'd like to know?")
                    
                elif query_type == QueryType.WEB_SEARCH:
                    # Use AI with web search context
                    history = [{"role": m.role, "content": m.content} for m in request.messages] if request.messages else []
                    async for chunk in ai_router.process_message(
                        request.message, 
                        request.session_id,
                        history
                    ):
                        yield format_sse_chunk(chunk)
                        
                else:  # QueryType.GENERAL_CHAT
                    # General AI conversation
                    history = [{"role": m.role, "content": m.content} for m in request.messages] if request.messages else []
                    async for chunk in ai_router.process_message(
                        request.message, 
                        request.session_id,
                        history
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
