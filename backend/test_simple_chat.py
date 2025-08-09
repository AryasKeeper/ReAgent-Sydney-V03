"""Simple test to check if chat endpoint returns anything"""
import requests

url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"

# Test 1: Simple hello
print("Test 1: Simple hello")
print("-" * 50)
payload = {
    "message": "Hello",
    "session_id": "test-simple",
    "messages": []
}

try:
    response = requests.post(url, json=payload, stream=True, timeout=3)
    print(f"Status: {response.status_code}")
    
    content = ""
    for chunk in response.iter_lines(decode_unicode=True):
        if chunk:
            content += chunk + "\n"
            if len(content) < 500:
                print(chunk)
    
    if "error" in content.lower():
        print("\nError detected in response!")
    else:
        print("\nResponse received successfully")
        
except requests.Timeout:
    print("Request timed out after 3 seconds")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)

# Test 2: Property search
print("\nTest 2: Property search")
print("-" * 50)
payload = {
    "message": "Find me houses in Marrickville",
    "session_id": "test-property",
    "messages": []
}

try:
    response = requests.post(url, json=payload, stream=True, timeout=5)
    print(f"Status: {response.status_code}")
    
    content = ""
    for chunk in response.iter_lines(decode_unicode=True):
        if chunk:
            content += chunk + "\n"
            if len(content) < 500:
                print(chunk)
    
    if "Chapel Street" in content or "mock" in content.lower():
        print("\nMock data detected - Scrapfly mock mode is working!")
    elif "error" in content.lower():
        print("\nError detected in response!")
    else:
        print("\nResponse received (check content)")
        
except requests.Timeout:
    print("Request timed out after 5 seconds")
except Exception as e:
    print(f"Error: {e}")