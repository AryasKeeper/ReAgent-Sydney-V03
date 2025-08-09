"""Test imports with debug prints"""
import sys
import os

# Add more detailed error handling
print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("-" * 50)

try:
    print("Step 1: Importing session_manager...")
    from services.session_manager import session_manager
    print("  SUCCESS")
    
    print("\nStep 2: Testing should_introduce method...")
    result = session_manager.should_introduce("test")
    print(f"  Result: {result}")
    print(f"  Type: {type(result)}")
    
    print("\nStep 3: Testing greeting...")
    from services.response_variety import get_greeting
    greeting = get_greeting()
    print(f"  Greeting length: {len(greeting)}")
    print(f"  First 50 chars: {greeting[:50]}...")
    
    print("\nStep 4: Testing format_sse_chunk...")
    from utils.streaming import format_sse_chunk
    chunk = format_sse_chunk("Hello")
    print(f"  Formatted chunk: {repr(chunk)}")
    
    print("\nStep 5: Testing AI router with mock mode...")
    from services.ai_router import AIRouter
    router = AIRouter()
    print(f"  Router created: {router}")
    
    # Test the mock response
    import asyncio
    async def test_mock():
        chunks = []
        async for chunk in router.process_message("Hello", "test", []):
            chunks.append(chunk)
            print(f"  Chunk {len(chunks)}: {chunk}")
        return chunks
    
    print("\nStep 6: Running async test...")
    chunks = asyncio.run(test_mock())
    print(f"  Total chunks: {len(chunks)}")
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()