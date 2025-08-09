"""Test property search functionality"""
import requests
import json

url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"

# Test property search request
payload = {
    "message": "help me find 3-bedroom houses in Marrickville under $2.43M",
    "session_id": "test-property-search",
    "messages": []
}

try:
    print("Testing property search request...")
    print(f"Query: {payload['message']}")
    print("-" * 60)
    
    response = requests.post(url, json=payload, stream=True)
    print(f"Status: {response.status_code}\n")
    
    if response.status_code == 200:
        print("Response (first 1500 chars):")
        content = ""
        for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
            if chunk:
                content += chunk
                if len(content) >= 1500:
                    break
        print(content)
        print("\n[... response continues ...]")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")