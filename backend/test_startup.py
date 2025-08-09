"""Test if app can start"""
import sys
import os

print("Testing app startup...")
print(f"Python: {sys.version}")
print(f"Working dir: {os.getcwd()}")

try:
    print("\n1. Testing imports...")
    from config import settings
    print(f"   Settings loaded: USE_MOCK={settings.USE_MOCK}")
    
    from services.query_analyzer import query_analyzer
    print(f"   Query analyzer loaded")
    
    from services.ai_router import ai_router
    print(f"   AI router loaded")
    
    print("\n2. Testing FastAPI app...")
    from app import app
    print(f"   App loaded: {app}")
    
    print("\n3. Starting server...")
    import uvicorn
    print("   Starting on http://127.0.0.1:8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()