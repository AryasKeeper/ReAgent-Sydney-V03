"""Test script for GPT-5 and Claude 4 Sonnet integration"""
import asyncio
import httpx
import json

async def test_chat_endpoint():
    """Test the enhanced Agent Whisperer with GPT-5 and Claude 4"""
    
    base_url = "http://localhost:8000"
    
    # Test queries
    test_queries = [
        {
            "message": "Hello!",
            "expected": "greeting",
            "description": "Testing greeting response"
        },
        {
            "message": "What time is it in Sydney?",
            "expected": "time",
            "description": "Testing time query (should show AEDT)"
        },
        {
            "message": "What's the weather like in Sydney today?",
            "expected": "weather",
            "description": "Testing weather query"
        },
        {
            "message": "Find me 3-bedroom houses in Marrickville under $2.5M",
            "expected": "property_search",
            "description": "Testing property search"
        },
        {
            "message": "Analyze the Sydney property market trends",
            "expected": "complex_analysis",
            "description": "Testing complex analysis (should use Claude 4)"
        },
        {
            "message": "What are the best suburbs for first-time buyers?",
            "expected": "general_chat",
            "description": "Testing general real estate question (should use GPT-5)"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("Testing Enhanced Agent Whisperer with GPT-5 & Claude 4")
        print("=" * 60)
        
        for i, test in enumerate(test_queries, 1):
            print(f"\nTest {i}: {test['description']}")
            print(f"Query: {test['message']}")
            print("-" * 40)
            
            try:
                # Make request
                response = await client.post(
                    f"{base_url}/api/v1/agent-whisperer/chat/stream",
                    json={
                        "message": test["message"],
                        "session_id": f"test-session-{i}"
                    }
                )
                
                if response.status_code == 200:
                    # Collect full response
                    full_response = ""
                    for line in response.text.split('\n'):
                        if line.startswith('0:'):
                            # Extract the text content
                            content = line[2:]
                            if content.startswith('"') and content.endswith('"'):
                                content = content[1:-1]
                            full_response += content
                    
                    print(f"Response: {full_response[:200]}...")
                    print(f"✅ Status: Success")
                else:
                    print(f"❌ Error: Status {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("Testing Complete!")
        print("=" * 60)

if __name__ == "__main__":
    print("Starting Agent Whisperer Tests...")
    print("Make sure the backend is running on http://localhost:8000")
    print("And that you have added your API keys to .env file")
    print()
    asyncio.run(test_chat_endpoint())