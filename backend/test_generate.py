"""Test the generate function directly"""
import asyncio
from api.agent_whisperer import chat_stream
from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    messages: List[ChatMessage] = []

async def test():
    request = ChatRequest(
        message="Hello",
        session_id="test-direct",
        messages=[]
    )
    
    try:
        response = await chat_stream(request)
        print("Response type:", type(response))
        
        # Try to consume the stream
        async for chunk in response.body_iterator:
            print(chunk.decode() if isinstance(chunk, bytes) else chunk, end='')
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())