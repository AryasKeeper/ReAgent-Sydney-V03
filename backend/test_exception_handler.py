"""Add diagnostic exception handler to catch silent failures"""
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List
import traceback
import sys
import uvicorn

# Force unbuffered output
sys.stdout = sys.stderr

app = FastAPI()

# Add global exception handler to catch ANY exception
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    """Catch and log ALL exceptions"""
    print(f"\n{'='*60}")
    print(f"CAUGHT EXCEPTION IN HANDLER")
    print(f"Exception Type: {type(exc).__name__}")
    print(f"Exception Message: {str(exc)}")
    print(f"Request URL: {request.url}")
    print(f"Request Method: {request.method}")
    print("Full Traceback:")
    traceback.print_exc()
    print(f"{'='*60}\n")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    messages: List[ChatMessage] = []

print("Loading services...")

try:
    # Try importing with detailed logging
    print("1. Importing ai_router...")
    from services.ai_router import ai_router
    print("   SUCCESS: ai_router imported")
    
    print("2. Importing session_manager...")
    from services.session_manager import session_manager
    print("   SUCCESS: session_manager imported")
    
    print("3. Importing other services...")
    from services.web_search import web_search
    from services.property_search import property_search
    from services.response_variety import get_greeting, get_search_intro
    from utils.streaming import format_sse_chunk
    print("   SUCCESS: All services imported")
    
except Exception as e:
    print(f"\nIMPORT ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Test endpoint with diagnostic output"""
    print(f"\nEndpoint called: session={request.session_id}")
    
    async def generate():
        print(f"Generator starting...")
        try:
            # Try the actual logic
            if session_manager.should_introduce(request.session_id):
                print("Getting greeting...")
                greeting = get_greeting()
                yield format_sse_chunk(greeting)
                session_manager.mark_introduced(request.session_id)
            
            # Simple mock response
            yield format_sse_chunk("Test response from diagnostic handler")
            yield format_sse_chunk("", "finish")
            print("Generator completed successfully")
            
        except Exception as e:
            print(f"ERROR IN GENERATOR: {e}")
            traceback.print_exc()
            yield format_sse_chunk(f"Error: {e}", "text")
            yield format_sse_chunk("", "finish")
    
    try:
        print("Creating StreamingResponse...")
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        print(f"ERROR creating response: {e}")
        traceback.print_exc()
        raise

@app.get("/test")
async def test():
    """Simple test endpoint"""
    return {"status": "ok", "services_loaded": True}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting diagnostic server on http://localhost:8001")
    print("Test with: curl -X POST http://localhost:8001/chat/stream -H 'Content-Type: application/json' -d '{\"message\":\"Hello\",\"session_id\":\"test\"}'")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")