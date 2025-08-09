"""FINAL TEST - Absolute minimal FastAPI server"""
print("Starting final test...")

# Test 1: Can we even import FastAPI?
try:
    from fastapi import FastAPI
    print("[OK] FastAPI imported successfully")
except Exception as e:
    print(f"[FAIL] FastAPI import failed: {e}")
    exit(1)

# Test 2: Can we create an app?
try:
    app = FastAPI()
    print("[OK] FastAPI app created")
except Exception as e:
    print(f"[FAIL] App creation failed: {e}")
    exit(1)

# Test 3: Can we add a route?
try:
    @app.get("/")
    def root():
        return {"test": "working"}
    print("[OK] Route added")
except Exception as e:
    print(f"[FAIL] Route failed: {e}")
    exit(1)

# Test 4: Can we run the server?
try:
    import uvicorn
    print("[OK] Uvicorn imported")
    print("\n" + "="*50)
    print("Starting server on http://127.0.0.1:9999/")
    print("Test with: curl http://127.0.0.1:9999/")
    print("="*50 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=9999, log_level="debug")
except Exception as e:
    print(f"[FAIL] Server failed: {e}")
    import traceback
    traceback.print_exc()