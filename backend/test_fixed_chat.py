"""Test the fixed chat endpoint"""
import requests
import json

url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"

print("Testing fixed chat endpoint...")
print("-" * 50)

# Test 1: Simple greeting
payload = {
    "message": "Hello",
    "session_id": "test-fixed",
    "messages": []
}

try:
    response = requests.post(url, json=payload, stream=True, timeout=5)
    print(f"Status: {response.status_code}\n")
    
    full_response = ""
    for line in response.iter_lines(decode_unicode=True):
        if line:
            full_response += line + "\n"
            print(line)
    
    print("\n" + "-" * 50)
    
    # Check what we got
    if "error" in full_response.lower():
        print("❌ Still getting error response")
        print("\nCheck backend console for error details!")
    elif "whisperer" in full_response.lower() or "sydney" in full_response.lower():
        print("✅ SUCCESS! Chat is working with greeting!")
    elif "understand" in full_response.lower():
        print("✅ SUCCESS! Mock mode is working!")
    else:
        print("⚠️ Unexpected response")
        
except requests.Timeout:
    print("Request timed out")
except Exception as e:
    print(f"Error: {e}")