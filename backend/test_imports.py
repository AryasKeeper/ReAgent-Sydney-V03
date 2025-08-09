"""Test if imports are working correctly"""
import sys
import traceback

print("Testing imports...")
print("-" * 50)

try:
    print("1. Importing services.ai_router...")
    from services.ai_router import ai_router
    print("   SUCCESS: ai_router imported")
    print(f"   Type: {type(ai_router)}")
    
    print("\n2. Importing services.session_manager...")
    from services.session_manager import session_manager
    print("   SUCCESS: session_manager imported")
    print(f"   Type: {type(session_manager)}")
    print(f"   Has should_introduce: {hasattr(session_manager, 'should_introduce')}")
    
    print("\n3. Importing services.web_search...")
    from services.web_search import web_search
    print("   SUCCESS: web_search imported")
    print(f"   Type: {type(web_search)}")
    
    print("\n4. Importing services.property_search...")
    from services.property_search import property_search
    print("   SUCCESS: property_search imported")
    print(f"   Type: {type(property_search)}")
    
    print("\n5. Importing services.response_variety...")
    from services.response_variety import get_greeting, get_search_intro
    print("   SUCCESS: response_variety functions imported")
    
    print("\n" + "=" * 50)
    print("ALL IMPORTS SUCCESSFUL!")
    
    # Test a simple call
    print("\nTesting session_manager.should_introduce...")
    result = session_manager.should_introduce("test-session")
    print(f"Result: {result}")
    
except Exception as e:
    print(f"\nERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()