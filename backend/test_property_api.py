"""Quick test of property search through API"""
import requests
import json

url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"

payload = {
    "message": "Help me find 3-bedroom houses in Marrickville under $2.5M",
    "session_id": "test-restart",
    "messages": []
}

print("Testing property search after restart...")
print("-" * 50)

response = requests.post(url, json=payload, stream=True)

if response.status_code == 200:
    content = ""
    for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
        if chunk:
            content += chunk
            if len(content) <= 1000:
                print(chunk, end='', flush=True)
            elif len(content) == 1001:
                print("\n[... truncated for brevity ...]")
    
    # Check if we got the mock data
    if "Chapel Street" in content or "Livingstone Road" in content:
        print("\n\n✅ SUCCESS! Mock Scrapfly data is working!")
    else:
        print("\n\n⚠️ Not seeing expected mock data")
else:
    print(f"Error: {response.status_code}")