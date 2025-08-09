"""Test the generator function directly"""
import asyncio
import sys
import traceback

print("Testing generator function directly...")
print("-" * 50)

# Import everything
try:
    from services.ai_router import ai_router
    from services.session_manager import session_manager
    from services.web_search import web_search
    from services.property_search import property_search
    from services.response_variety import get_greeting, get_search_intro
    from utils.streaming import format_sse_chunk
    from config import settings
    print("All imports successful")
except Exception as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    sys.exit(1)

# Create a mock request
class MockRequest:
    def __init__(self, message, session_id):
        self.message = message
        self.session_id = session_id
        self.messages = []

async def test_generator():
    """Test the exact generator logic from agent_whisperer.py"""
    request = MockRequest("Hello", "test-direct")
    
    print(f"Testing with session {request.session_id}")
    print(f"USE_MOCK = {settings.USE_MOCK}")
    
    # The exact generator logic from agent_whisperer.py
    try:
        print("DEBUG: Generator started")
        
        print("DEBUG: Checking should_introduce...")
        if session_manager.should_introduce(request.session_id):
            print("DEBUG: Getting greeting...")
            greeting = get_greeting()
            chunk = format_sse_chunk(greeting)
            print(f"DEBUG: Greeting chunk: {chunk[:50]}...")
            session_manager.mark_introduced(request.session_id)
        
        # Detect query type
        message_lower = request.message.lower()
        print(f"DEBUG: Message lower: {message_lower}")
        
        # Handle weather/time queries
        if any(word in message_lower for word in ["weather", "time", "temperature"]):
            print("DEBUG: Processing weather query...")
            result = await web_search.search_weather_time(request.message)
            chunk = format_sse_chunk(result)
            print(f"DEBUG: Weather result chunk")
        
        # Handle property searches
        elif any(word in message_lower for word in ["property", "house", "apartment", "bedroom", "real estate", "buy", "sale", "find"]):
            print("DEBUG: Processing property search...")
            intro = get_search_intro()
            chunk1 = format_sse_chunk(intro)
            print(f"DEBUG: Property intro chunk")
            
            result = await property_search.search_properties(request.message)
            chunk2 = format_sse_chunk(result)
            print(f"DEBUG: Property result chunk")
        
        # General chat
        else:
            print("DEBUG: Processing general chat with AI router...")
            history = []  # Empty for this test
            chunks = []
            async for chunk in ai_router.process_message(
                request.message, 
                request.session_id,
                history
            ):
                chunks.append(chunk)
                print(f"DEBUG: AI router chunk: {chunk[:30]}...")
        
        # Send finish signal
        finish_chunk = format_sse_chunk("", "finish")
        print(f"DEBUG: Finish chunk: {finish_chunk}")
        
        print("\n✅ Generator logic completed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR IN GENERATOR: {e}")
        print(f"Error type: {type(e).__name__}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generator())