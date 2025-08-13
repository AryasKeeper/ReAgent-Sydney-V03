"""
Agent data models for ReAgent Sydney V03 API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class AgentStatus(str, Enum):
    """Agent availability status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class AgentCapability(str, Enum):
    """Agent capabilities"""
    PROPERTY_SEARCH = "property_search"
    PROPERTY_ANALYSIS = "property_analysis" 
    WEB_SEARCH = "web_search"
    WEATHER = "weather"
    NEWS = "news"
    GENERAL_CHAT = "general_chat"

class AgentInfo(BaseModel):
    """Information about an available agent"""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent description and capabilities")
    status: AgentStatus = Field(..., description="Current agent status")
    capabilities: List[AgentCapability] = Field(..., description="Agent capabilities")
    version: str = Field(..., description="Agent version")
    region: str = Field(default="ap-southeast-2", description="Agent deployment region")
    response_time_ms: Optional[int] = Field(None, description="Average response time in milliseconds")
    max_concurrent_sessions: int = Field(default=100, description="Maximum concurrent sessions")
    current_sessions: int = Field(default=0, description="Current active sessions")

class ChatMessage(BaseModel):
    """Chat message for agent invocation"""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")

class AgentInvokeRequest(BaseModel):
    """Request model for agent invocation"""
    message: str = Field(..., description="User message")
    session_id: str = Field(default="default", description="Session identifier")
    messages: List[ChatMessage] = Field(default_factory=list, description="Chat history")
    stream: bool = Field(default=True, description="Whether to stream response")
    user_id: Optional[str] = Field(None, description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class AgentResponse(BaseModel):
    """Response model for non-streaming agent invocation"""
    agent_id: str = Field(..., description="Agent that handled the request")
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")
    sources: Optional[List[str]] = Field(None, description="Sources used in response")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage statistics")
    response_time_ms: int = Field(..., description="Response time in milliseconds")

class AgentListResponse(BaseModel):
    """Response model for listing available agents"""
    agents: List[AgentInfo] = Field(..., description="List of available agents")
    total_count: int = Field(..., description="Total number of agents")
    active_count: int = Field(..., description="Number of active agents")