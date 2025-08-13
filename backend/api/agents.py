"""
Agents API endpoints for ReAgent Sydney V03
Handles agent listing and invocation
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import logging
import time
import uuid

from models.agents import (
    AgentInfo, 
    AgentStatus, 
    AgentCapability, 
    AgentInvokeRequest, 
    AgentResponse, 
    AgentListResponse,
    ChatMessage
)
from services.jwt_auth import jwt_auth
from services.ai_router import ai_router
from services.query_analyzer import query_analyzer, QueryType
from services.property_search import property_search
from services.web_search import web_search
from services.agentic_browse import agentic_browse
from utils.streaming import format_sse_chunk, detect_protocol_version
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Available agents configuration
AVAILABLE_AGENTS = {
    "agent-whisperer": AgentInfo(
        agent_id="agent-whisperer",
        name="Agent Whisperer",
        description="Sydney real estate AI assistant with property search, market analysis, and general chat capabilities",
        status=AgentStatus.ACTIVE,
        capabilities=[
            AgentCapability.PROPERTY_SEARCH,
            AgentCapability.PROPERTY_ANALYSIS,
            AgentCapability.WEB_SEARCH,
            AgentCapability.WEATHER,
            AgentCapability.NEWS,
            AgentCapability.GENERAL_CHAT
        ],
        version="3.0.0-spike",
        region="ap-southeast-2",
        response_time_ms=450,
        max_concurrent_sessions=100,
        current_sessions=0
    ),
    "property-specialist": AgentInfo(
        agent_id="property-specialist",
        name="Property Specialist",
        description="Specialized agent for Sydney property searches and market analysis",
        status=AgentStatus.ACTIVE,
        capabilities=[
            AgentCapability.PROPERTY_SEARCH,
            AgentCapability.PROPERTY_ANALYSIS
        ],
        version="3.0.0-spike",
        region="ap-southeast-2",
        response_time_ms=320,
        max_concurrent_sessions=50,
        current_sessions=0
    ),
    "web-researcher": AgentInfo(
        agent_id="web-researcher",
        name="Web Researcher",
        description="Web search and browsing specialist for real-time information gathering",
        status=AgentStatus.ACTIVE,
        capabilities=[
            AgentCapability.WEB_SEARCH,
            AgentCapability.NEWS,
            AgentCapability.WEATHER
        ],
        version="3.0.0-spike",
        region="ap-southeast-2",
        response_time_ms=580,
        max_concurrent_sessions=30,
        current_sessions=0
    )
}

@router.get("/agents/list", response_model=AgentListResponse)
async def list_agents(request: Request):
    """
    List all available agents
    
    Returns information about available agents, their capabilities, and current status.
    JWT authentication required in staging/production.
    """
    try:
        # JWT authentication if required
        if getattr(settings, 'REQUIRE_JWT_AUTH', True):
            jwt_payload = jwt_auth.require_jwt_auth(request)
            logger.info(f"JWT authenticated request for agent list - User: {jwt_payload.get('sub')}")
        
        # Get all available agents
        agents = list(AVAILABLE_AGENTS.values())
        active_agents = [agent for agent in agents if agent.status == AgentStatus.ACTIVE]
        
        return AgentListResponse(
            agents=agents,
            total_count=len(agents),
            active_count=len(active_agents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent list")

@router.post("/agents/{agent_id}/invoke")
async def invoke_agent(
    agent_id: str, 
    invoke_request: AgentInvokeRequest,
    request: Request
):
    """
    Invoke a specific agent with a message
    
    Supports both streaming and non-streaming responses.
    JWT authentication required in staging/production.
    """
    try:
        # JWT authentication if required
        jwt_payload = None
        if getattr(settings, 'REQUIRE_JWT_AUTH', True):
            jwt_payload = jwt_auth.require_jwt_auth(request)
            logger.info(f"JWT authenticated agent invoke - User: {jwt_payload.get('sub')}, Agent: {agent_id}")
        
        # Validate agent exists
        if agent_id not in AVAILABLE_AGENTS:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        agent_info = AVAILABLE_AGENTS[agent_id]
        
        # Check agent status
        if agent_info.status != AgentStatus.ACTIVE:
            raise HTTPException(status_code=503, detail=f"Agent '{agent_id}' is not available")
        
        start_time = time.time()
        
        if invoke_request.stream:
            # Return streaming response
            return await _stream_agent_response(agent_id, invoke_request, request)
        else:
            # Return non-streaming response
            return await _non_stream_agent_response(agent_id, invoke_request, start_time)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        raise HTTPException(status_code=500, detail="Agent invocation failed")

async def _stream_agent_response(agent_id: str, invoke_request: AgentInvokeRequest, request: Request):
    """Handle streaming agent response"""
    
    # Detect protocol version
    headers_dict = dict(request.headers)
    protocol_version = detect_protocol_version(headers_dict)
    
    async def generate():
        try:
            # Route based on agent capabilities
            agent_info = AVAILABLE_AGENTS[agent_id]
            
            if agent_id == "agent-whisperer":
                # Use full agent whisperer logic
                async for chunk in _agent_whisperer_stream(invoke_request, protocol_version):
                    yield chunk
            elif agent_id == "property-specialist":
                # Property-focused agent
                async for chunk in _property_specialist_stream(invoke_request, protocol_version):
                    yield chunk
            elif agent_id == "web-researcher":
                # Web research focused agent
                async for chunk in _web_researcher_stream(invoke_request, protocol_version):
                    yield chunk
            else:
                yield format_sse_chunk("Agent not implemented", "text", protocol_version)
            
            # Send finish signal
            yield format_sse_chunk("", "finish", protocol_version)
            
        except Exception as e:
            logger.error(f"Streaming error for agent {agent_id}: {e}")
            yield format_sse_chunk("I encountered an error. Please try again.", "text", protocol_version)
            yield format_sse_chunk("", "finish", protocol_version)
    
    # Set appropriate headers
    response_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Content-Type-Options": "nosniff",
    }
    
    if protocol_version == "v5":
        response_headers["x-vercel-ai-ui-message-stream"] = "v1"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream" if protocol_version == "v5" else "text/plain",
        headers=response_headers
    )

async def _non_stream_agent_response(agent_id: str, invoke_request: AgentInvokeRequest, start_time: float) -> AgentResponse:
    """Handle non-streaming agent response"""
    
    try:
        # Collect streamed response into a single response
        response_parts = []
        sources = []
        
        # Simple implementation - in production this would be more sophisticated
        if agent_id == "property-specialist":
            result = await property_search.search_properties(invoke_request.message)
            response_parts.append(result)
        elif agent_id == "web-researcher":
            summary, web_sources = await agentic_browse(invoke_request.message)
            response_parts.append(summary)
            sources.extend(web_sources or [])
        else:
            # Default to general chat
            response_parts.append("I'm an AI assistant ready to help with your questions.")
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return AgentResponse(
            agent_id=agent_id,
            response="".join(response_parts),
            session_id=invoke_request.session_id,
            sources=sources if sources else None,
            usage={"response_time_ms": response_time_ms},
            response_time_ms=response_time_ms
        )
        
    except Exception as e:
        logger.error(f"Non-streaming response error for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")

async def _agent_whisperer_stream(invoke_request: AgentInvokeRequest, protocol_version: str):
    """Stream response from agent whisperer (full functionality)"""
    
    # Analyze query type
    query_type, params, fallback_notice = query_analyzer.analyze_query_with_fallback(
        invoke_request.message, 
        invoke_request.session_id,
        has_web_apis=bool(settings.BRAVE_API_KEY)
    )
    
    if query_type == QueryType.PROPERTY_SEARCH:
        result = await property_search.search_properties(invoke_request.message)
        yield format_sse_chunk(result, "text", protocol_version)
    elif query_type == QueryType.WEB_SEARCH:
        summary, sources = await agentic_browse(invoke_request.message)
        if sources:
            yield format_sse_chunk(sources, "sources_meta", protocol_version)
        yield format_sse_chunk(summary, "text", protocol_version)
    else:
        # Use AI router for general chat
        history = [{"role": m.role, "content": m.content} for m in invoke_request.messages]
        async for chunk in ai_router.process_message(
            invoke_request.message,
            invoke_request.session_id,
            history
        ):
            yield format_sse_chunk(chunk, "text", protocol_version)

async def _property_specialist_stream(invoke_request: AgentInvokeRequest, protocol_version: str):
    """Stream response from property specialist agent"""
    yield format_sse_chunk("I'm your Sydney property specialist. Let me help you with property information.", "text", protocol_version)
    result = await property_search.search_properties(invoke_request.message)
    yield format_sse_chunk(result, "text", protocol_version)

async def _web_researcher_stream(invoke_request: AgentInvokeRequest, protocol_version: str):
    """Stream response from web researcher agent"""
    yield format_sse_chunk("I'm researching the latest information for you...", "text", protocol_version)
    summary, sources = await agentic_browse(invoke_request.message)
    if sources:
        yield format_sse_chunk(sources, "sources_meta", protocol_version)
    yield format_sse_chunk(summary, "text", protocol_version)

@router.get("/agents/{agent_id}")
async def get_agent_info(agent_id: str, request: Request) -> AgentInfo:
    """
    Get detailed information about a specific agent
    
    JWT authentication required in staging/production.
    """
    try:
        # JWT authentication if required
        if getattr(settings, 'REQUIRE_JWT_AUTH', True):
            jwt_payload = jwt_auth.require_jwt_auth(request)
            logger.info(f"JWT authenticated agent info request - User: {jwt_payload.get('sub')}, Agent: {agent_id}")
        
        if agent_id not in AVAILABLE_AGENTS:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        return AVAILABLE_AGENTS[agent_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent info for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent information")