"""Debug script to see the actual error in chat endpoint"""
import requests
import logging

# Enable logging to see backend errors
logging.basicConfig(level=logging.DEBUG)

url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"

payload = {
    "message": "Hello",
    "session_id": "debug-error",
    "messages": []
}

print("Sending request to chat endpoint...")
print("-" * 50)

try:
    response = requests.post(url, json=payload, stream=True)
    print(f"Status Code: {response.status_code}\n")
    
    print("Response:")
    for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
    print("\n")
    
except Exception as e:
    print(f"Request error: {e}")

print("-" * 50)
print("\nNow check the backend console/terminal for the actual error traceback!")
print("The error details should be logged there.")