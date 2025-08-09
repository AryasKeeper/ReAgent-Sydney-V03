"""Test chat functionality directly without FastAPI"""
import asyncio
import sys
import traceback

# Import all the services exactly as agent_whisperer does
from services.ai_router import ai_router
from services.session_manager import session_manager
from services.web_search import web_search
from services.property_search import property_search
from services.response_variety import get_greeting, get_search_intro
from utils.streaming import format_sse_chunk

async def test_chat():
    """Test the chat flow directly"""
    print("Testing chat flow...")
    print("-" * 50)
    
    session_id = "test-direct"
    message = "Hello"
    
    try:
        # Check if we should introduce ourselves
        if session_manager.should_introduce(session_id):
            greeting = get_greeting()
            print(f"Greeting: {greeting[:100]}...")
            session_manager.mark_introduced(session_id)
        
        # Test simple AI router response
        print("\nTesting AI router...")
        chunks = []
        async for chunk in ai_router.process_message(message, session_id, []):
            chunks.append(chunk)
            if len(chunks) <= 3:
                print(f"Chunk {len(chunks)}: {chunk[:50]}...")
        
        print(f"\nReceived {len(chunks)} chunks total")
        print("\nSUCCESS: Chat flow works!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat())