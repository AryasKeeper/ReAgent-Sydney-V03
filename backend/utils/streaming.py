"""
SSE streaming utilities for Vercel AI SDK compatibility
Supports both v3 (legacy) and v5 (UI Message Stream) protocols
"""
import json
from typing import Any, Dict, Optional
import uuid

def format_sse_chunk(content: str, chunk_type: str = "text", protocol_version: str = "v3") -> str:
    """
    Format chunks for Vercel AI SDK
    
    Supports two protocols:
    - v3 (legacy): Original format for AI SDK v3.4.33
    - v5 (UI Message Stream): New transport-based format for AI SDK v5
    
    Protocol is determined by:
    1. Explicit protocol_version parameter
    2. Request header 'x-vercel-ai-ui-message-stream: v1' (indicates v5)
    """
    if protocol_version == "v5":
        return format_v5_chunk(content, chunk_type)
    else:
        return format_v3_chunk(content, chunk_type)

def format_v3_chunk(content: str, chunk_type: str = "text") -> str:
    """
    Format chunks for Vercel AI SDK v3.4.33 (legacy)
    
    IMPORTANT: This format is proven to work:
    - Text chunks: 0:"content"\n
    - Finish signal: d:{"finishReason":"stop"}\n
    - Sources metadata: 8:["source_meta"]\n
    
    DO NOT use 'data:' prefix or double newlines - they will break!
    """
    if chunk_type == "text":
        # Properly escape content as JSON string
        escaped_content = json.dumps(content)
        return f'0:{escaped_content}\n'
    
    elif chunk_type == "finish":
        # Finish signal with proper format
        return 'd:{"finishReason":"stop"}\n'
    
    elif chunk_type == "sources_meta":
        # Source metadata as array (SSE type 8)
        # content should be a list of source URLs
        sources_json = json.dumps(content if isinstance(content, list) else [content])
        return f'8:{sources_json}\n'
    
    elif chunk_type == "error":
        # Error format
        return f'd:{{"finishReason":"error","error":{json.dumps(content)}}}\n'
    
    else:
        raise ValueError(f"Unknown chunk type: {chunk_type}")

def format_v5_chunk(content: Any, chunk_type: str = "text") -> str:
    """
    Format chunks for Vercel AI SDK v5 (UI Message Stream protocol)
    
    Uses structured JSON messages with type field:
    - text-delta: Incremental text content
    - finish: Stream completion
    - tool-call: Tool invocation (for future use)
    - error: Error message
    """
    if chunk_type == "text":
        message = {
            "type": "text-delta",
            "textDelta": content
        }
        return f'data: {json.dumps(message)}\n\n'
    
    elif chunk_type == "finish":
        message = {
            "type": "finish",
            "finishReason": "stop",
            "usage": {
                "promptTokens": 0,
                "completionTokens": 0
            }
        }
        return f'data: {json.dumps(message)}\n\n'
    
    elif chunk_type == "sources_meta":
        # In v5, sources can be sent as tool-result messages
        message = {
            "type": "tool-result",
            "toolName": "web_search",
            "result": content if isinstance(content, list) else [content]
        }
        return f'data: {json.dumps(message)}\n\n'
    
    elif chunk_type == "error":
        message = {
            "type": "error",
            "error": {
                "message": content,
                "type": "stream_error"
            }
        }
        return f'data: {json.dumps(message)}\n\n'
    
    elif chunk_type == "message_start":
        # Start of a new assistant message
        message = {
            "type": "message-start",
            "id": str(uuid.uuid4()),
            "role": "assistant"
        }
        return f'data: {json.dumps(message)}\n\n'
    
    else:
        raise ValueError(f"Unknown chunk type: {chunk_type}")

def detect_protocol_version(headers: Dict[str, str]) -> str:
    """
    Detect which streaming protocol to use based on request headers
    
    Returns:
        "v5" if UI Message Stream header is present
        "v3" otherwise (default/legacy)
    """
    # Check for v5 UI Message Stream header
    if headers.get("x-vercel-ai-ui-message-stream") == "v1":
        return "v5"
    
    # Check for explicit version header (for testing)
    if headers.get("x-ai-sdk-version") == "5":
        return "v5"
    
    # Default to v3 for backward compatibility
    return "v3"