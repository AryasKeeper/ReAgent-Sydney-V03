"""Test that greetings don't repeat in same session"""
import requests
import json
import time

url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"
session_id = "test-no-repeat-session"

def send_message(message, iteration):
    payload = {
        "message": message,
        "session_id": session_id,
        "messages": []
    }
    
    print(f"\n--- Request {iteration}: {message} ---")
    response = requests.post(url, json=payload, stream=True)
    
    if response.status_code == 200:
        content = ""
        for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
            if chunk:
                content += chunk
                if len(content) >= 500:
                    break
        
        # Check if greeting appears
        has_greeting = "Agent Whisperer" in content or "I'm Agent Whisperer" in content
        print(f"Has greeting: {has_greeting}")
        print(f"First 200 chars: {content[:200]}...")
    else:
        print(f"Error: {response.status_code}")

# Test multiple messages in same session
messages = [
    "Hello",
    "What's the weather like?",
    "Tell me about Marrickville",
    "Find houses under $2M"
]

for i, msg in enumerate(messages, 1):
    send_message(msg, i)
    time.sleep(0.5)  # Small delay between requests