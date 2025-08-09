"""Start backend and test immediately"""
import subprocess
import time
import requests
import sys

# Start the backend process
print("Starting backend server...")
process = subprocess.Popen(
    [sys.executable, "app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Wait for server to start
print("Waiting for server to start...")
time.sleep(3)

# Test the endpoint
print("\nTesting chat endpoint...")
print("-" * 50)

url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"
payload = {
    "message": "Hello",
    "session_id": "test-with-logging",
    "messages": []
}

try:
    response = requests.post(url, json=payload, stream=True, timeout=3)
    print(f"Status: {response.status_code}\n")
    
    for chunk in response.iter_lines(decode_unicode=True):
        if chunk:
            print(chunk)
    
except requests.Timeout:
    print("Request timed out")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
print("\nServer output from startup:")
print("-" * 50)

# Get server output
for i in range(20):
    line = process.stdout.readline()
    if line:
        print(line.strip())
    else:
        break

# Keep server running for a moment to see any error output
time.sleep(2)

# Terminate server
print("\nTerminating server...")
process.terminate()
process.wait()