"""Minimal working chat endpoint"""
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
    """Working chat endpoint"""
    
    async def generate():
        # Test 1: Just return a simple message
        yield '0:"Hello from test endpoint"\n'
        yield 'd:{"finishReason":"stop"}\n'
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    print("Starting test server on http://localhost:8003")
    print("Test with: curl -X POST http://localhost:8003/chat/stream -H 'Content-Type: application/json' -d '{\"message\":\"Hello\"}'")
    uvicorn.run(app, host="0.0.0.0", port=8003)