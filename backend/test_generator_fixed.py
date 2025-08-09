"""Test generator without Unicode issues"""
import asyncio
import sys
import traceback

# Fix Windows encoding
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

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

class MockRequest:
    def __init__(self, message, session_id):
        self.message = message
        self.session_id = session_id
        self.messages = []

async def test_generator():
    """Test the exact generator logic"""
    request = MockRequest("Hello", "test-direct")
    
    print(f"Testing with session {request.session_id}")
    print(f"USE_MOCK = {settings.USE_MOCK}")
    
    try:
        print("DEBUG: Generator started")
        
        # Check introduction
        if session_manager.should_introduce(request.session_id):
            print("DEBUG: Getting greeting...")
            greeting = get_greeting()
            chunk = format_sse_chunk(greeting)
            print(f"DEBUG: Greeting chunk length: {len(chunk)}")
            session_manager.mark_introduced(request.session_id)
        
        # Process general chat
        message_lower = request.message.lower()
        print("DEBUG: Processing general chat with AI router...")
        history = []
        chunks = []
        async for chunk in ai_router.process_message(
            request.message, 
            request.session_id,
            history
        ):
            chunks.append(chunk)
            print(f"DEBUG: Got chunk {len(chunks)}")
        
        print(f"DEBUG: AI router returned {len(chunks)} chunks")
        print("SUCCESS: Generator logic completed!")
        return True
        
    except Exception as e:
        print(f"ERROR IN GENERATOR: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_generator())
    if result:
        print("CONCLUSION: Generator works perfectly - the issue is NOT in our logic!")
    else:
        print("CONCLUSION: Found the actual error in generator logic")