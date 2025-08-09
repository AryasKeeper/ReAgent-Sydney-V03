"""Quick test of chat endpoint"""
import requests
import json

url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"
payload = {
    "message": "Hello",
    "session_id": "test-session-1",
    "messages": []
}

try:
    response = requests.post(url, json=payload, stream=True)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("\nFirst 500 chars of response:")
        content = ""
        for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
            if chunk:
                content += chunk
                if len(content) >= 500:
                    break
        print(content)
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")