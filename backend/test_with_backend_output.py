"""Run backend and capture output"""
import subprocess
import time
import requests
import sys
import threading

def read_output(process):
    """Read and print backend output"""
    for line in process.stdout:
        print(f"[BACKEND] {line.strip()}")

# Start backend
print("Starting backend with output capture...")
process = subprocess.Popen(
    [sys.executable, "app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Start thread to read output
output_thread = threading.Thread(target=read_output, args=(process,))
output_thread.daemon = True
output_thread.start()

# Wait for server to start
print("Waiting for server to start...")
time.sleep(5)

# Test the endpoint
print("\n" + "=" * 50)
print("Testing chat endpoint...")
print("=" * 50)

url = "http://localhost:8000/api/v1/agent-whisperer/chat/stream"
payload = {
    "message": "Hello",
    "session_id": "test-capture",
    "messages": []
}

try:
    response = requests.post(url, json=payload, stream=True, timeout=3)
    print(f"Response status: {response.status_code}")
    
    for line in response.iter_lines(decode_unicode=True):
        if line:
            print(f"[RESPONSE] {line}")
    
except Exception as e:
    print(f"Error: {e}")

# Wait a bit more to see any error output
print("\nWaiting for any error output...")
time.sleep(3)

# Terminate
print("\nTerminating backend...")
process.terminate()
process.wait()