"""Create a working version of the chat endpoint"""
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List
import uvicorn

app = FastAPI()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    messages: List[ChatMessage] = Field(default_factory=list)

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Working chat endpoint based on our successful test"""
    
    # Import inside function to avoid any initialization issues
    from services.session_manager import session_manager
    from services.response_variety import get_greeting
    from services.ai_router import ai_router
    from utils.streaming import format_sse_chunk
    
    async def generate():
        # Check if we should introduce ourselves
        if session_manager.should_introduce(request.session_id):
            greeting = get_greeting()
            yield format_sse_chunk(greeting)
            session_manager.mark_introduced(request.session_id)
        
        # Process with AI router (we know this works in mock mode)
        history = [{"role": m.role, "content": m.content} for m in request.messages] if request.messages else []
        async for chunk in ai_router.process_message(
            request.message, 
            request.session_id,
            history
        ):
            yield format_sse_chunk(chunk)
        
        # Send finish signal
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

@app.get("/test")
async def test():
    return {"status": "working"}

if __name__ == "__main__":
    print("Starting working endpoint on http://localhost:8002")
    print("Test with:")
    print("curl -X POST http://localhost:8002/chat/stream -H 'Content-Type: application/json' -d '{\"message\":\"Hello\",\"session_id\":\"test\"}'")
    uvicorn.run(app, host="0.0.0.0", port=8002)