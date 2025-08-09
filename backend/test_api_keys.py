"""Test API keys to diagnose connection issues"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_openai():
    """Test OpenAI API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("[FAIL] OpenAI: No API key found")
        return False
        
    print(f"Testing OpenAI API key: {api_key[:10]}...")
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use a basic model for testing
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        
        print(f"[OK] OpenAI: Working! Response: {response.choices[0].message.content}")
        
        # Now test GPT-4
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        print(f"[OK] OpenAI GPT-4 Turbo: Working!")
        return True
        
    except Exception as e:
        print(f"[FAIL] OpenAI: Error - {e}")
        return False

async def test_anthropic():
    """Test Anthropic API key"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("[FAIL] Anthropic: No API key found")
        return False
        
    print(f"Testing Anthropic API key: {api_key[:10]}...")
    
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=api_key)
        
        # Test with Claude
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say hello"}]
        )
        
        print(f"[OK] Anthropic: Working! Response: {response.content[0].text}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Anthropic: Error - {e}")
        return False

async def test_tavily():
    """Test Tavily API key"""
    api_key = os.getenv("TAVILY_API_KEY")
    
    if not api_key:
        print("[FAIL] Tavily: No API key found")
        return False
        
    print(f"Testing Tavily API key: {api_key[:10]}...")
    
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": "test",
                    "search_depth": "basic",
                    "max_results": 1
                }
            )
            
            if response.status_code == 200:
                print(f"[OK] Tavily: Working!")
                return True
            else:
                print(f"[FAIL] Tavily: HTTP {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"[FAIL] Tavily: Error - {e}")
        return False

async def main():
    print("=" * 60)
    print("Testing API Keys for ReAgent Sydney")
    print("=" * 60)
    print()
    
    results = await asyncio.gather(
        test_openai(),
        test_anthropic(),
        test_tavily()
    )
    
    print()
    print("=" * 60)
    print("Summary:")
    print(f"OpenAI: {'[OK] Working' if results[0] else '[FAIL] Failed'}")
    print(f"Anthropic: {'[OK] Working' if results[1] else '[FAIL] Failed'}")
    print(f"Tavily: {'[OK] Working' if results[2] else '[FAIL] Failed'}")
    print("=" * 60)
    
    if not all(results):
        print("\n[WARN]  Some API keys are not working!")
        print("Please check your .env file and ensure:")
        print("1. API keys are valid and not expired")
        print("2. You have active subscriptions")
        print("3. Keys have proper permissions")

if __name__ == "__main__":
    asyncio.run(main())