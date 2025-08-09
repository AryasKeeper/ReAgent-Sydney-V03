"""Test imports step by step"""
import sys
import traceback

print("Testing imports...")

try:
    print("1. Importing services.session_manager...")
    from services.session_manager import session_manager
    print(f"   SUCCESS: {session_manager}")
except ImportError as e:
    print(f"   IMPORT ERROR: {e}")
    traceback.print_exc()
except AttributeError as e:
    print(f"   ATTRIBUTE ERROR: {e}")
    traceback.print_exc()
    
try:
    print("\n2. Importing from services module...")
    from services import session_manager
    print(f"   SUCCESS: {session_manager}")
except Exception as e:
    print(f"   ERROR: {e}")
    
print("\n3. Checking what's in services module...")
import services
print(f"   dir(services): {dir(services)}")