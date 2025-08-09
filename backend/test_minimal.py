"""Minimal test to find the error"""
import sys
import traceback

print("Testing service imports step by step...")
print("-" * 50)

try:
    print("1. Importing config...")
    from config import settings
    print(f"   USE_MOCK = {settings.USE_MOCK}")
    
    print("\n2. Importing session_manager...")
    from services.session_manager import session_manager
    print(f"   Session manager: {session_manager}")
    
    print("\n3. Importing response_variety...")
    from services.response_variety import get_greeting
    greeting = get_greeting()
    print(f"   Greeting works: {len(greeting)} chars")
    
    print("\n4. Importing ai_router singleton...")
    from services.ai_router import ai_router
    print(f"   AI router: {ai_router}")
    print(f"   OpenAI client: {ai_router.openai_client}")
    print(f"   Anthropic client: {ai_router.anthropic_client}")
    
    print("\n5. Testing AI router process_message...")
    import asyncio
    async def test():
        chunks = []
        async for chunk in ai_router.process_message("Hello", "test", []):
            chunks.append(chunk)
        return chunks
    
    chunks = asyncio.run(test())
    print(f"   Got {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):
        print(f"   Chunk {i+1}: {chunk}")
    
    print("\n" + "=" * 50)
    print("ALL IMPORTS AND TESTS SUCCESSFUL!")
    
except Exception as e:
    print(f"\nERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()