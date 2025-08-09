"""Run backend with error handling"""
import sys
import os
os.chdir(r"C:\Users\jonah\Desktop\ReAgent\reagent-backend-v3")

try:
    import uvicorn
    from app import app
    
    print("Starting ReAgent Backend V3...")
    print("- GPT-5 Integration Active")
    print("- Claude 4 Sonnet Active")
    print("- Live Mode Enabled")
    print("\nServer starting on http://127.0.0.1:8000")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")