"""Test AI router directly"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_router import AIRouter

async def test_ai_router():
    """Test AI router directly"""
    print("Testing AI Router...")
    print("-" * 50)
    
    # Create instance
    router = AIRouter()
    print(f"Router created: {router}")
    print(f"OpenAI client: {router.openai_client is not None}")
    print(f"Anthropic client: {router.anthropic_client is not None}")
    
    # Test processing a message
    print("\nProcessing test message...")
    try:
        chunks = []
        async for chunk in router.process_message("Hello", "test-session", []):
            chunks.append(chunk)
            print(f"Chunk: {chunk[:50]}...")
            if len(chunks) >= 3:
                break
        print(f"\nReceived {len(chunks)} chunks")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_router())