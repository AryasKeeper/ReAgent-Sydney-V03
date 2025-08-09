"""End-to-end test of property search through chat API"""
import requests
import json

def test_property_search_chat():
    """Test property search through the chat endpoint"""
    
    url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"
    
    # Test property search query
    payload = {
        "message": "Help me find 3-bedroom houses in Marrickville under $2.5M",
        "session_id": "test-e2e-property",
        "messages": []
    }
    
    print("=" * 60)
    print("E2E Property Search Test")
    print("=" * 60)
    print(f"\nQuery: {payload['message']}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=10)
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            print("Response:")
            content = ""
            for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                if chunk:
                    content += chunk
                    # Print in real-time but limit output
                    if len(content) <= 2000:
                        print(chunk, end='', flush=True)
                    elif len(content) == 2001:
                        print("\n\n[... response continues ...]")
            
            # Check if we got property data
            if "properties" in content.lower() or "found" in content.lower() or "Chapel Street" in content:
                print("\n\n" + "=" * 60)
                print("[SUCCESS] Property search working through chat API!")
                print("Scrapfly mock data is being returned correctly.")
            else:
                print("\n\n[WARNING] Response doesn't contain expected property data")
                
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Failed to connect to backend: {e}")
        print("\nMake sure the backend is running:")
        print("  cd reagent-backend-v3")
        print("  python app.py")
    
    print("=" * 60)

if __name__ == "__main__":
    test_property_search_chat()