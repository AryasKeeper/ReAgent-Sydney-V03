"""
SSE streaming utilities for Vercel AI SDK compatibility
CRITICAL: Must match exact format expected by @ai-sdk/react v0.0.70
"""
import json
from typing import Any

def format_sse_chunk(content: str, chunk_type: str = "text") -> str:
    """
    Format chunks for Vercel AI SDK v3.4.33
    
    IMPORTANT: This format is proven to work:
    - Text chunks: 0:"content"\n
    - Finish signal: d:{"finishReason":"stop"}\n
    
    DO NOT use 'data:' prefix or double newlines - they will break!
    """
    if chunk_type == "text":
        # Properly escape content as JSON string
        escaped_content = json.dumps(content)
        return f'0:{escaped_content}\n'
    
    elif chunk_type == "finish":
        # Finish signal with proper format
        return 'd:{"finishReason":"stop"}\n'
    
    elif chunk_type == "error":
        # Error format
        return f'd:{{"finishReason":"error","error":{json.dumps(content)}}}\n'
    
    else:
        raise ValueError(f"Unknown chunk type: {chunk_type}")