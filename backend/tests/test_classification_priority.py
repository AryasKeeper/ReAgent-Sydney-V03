#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Query Classification
Tests priority ordering, negation handling, session memory, and fallback behavior
"""
import sys
from pathlib import Path
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.query_analyzer import QueryAnalyzer, QueryType


def test_explicit_web_search_triggers():
    """Test that all explicit triggers properly activate web search."""
    analyzer = QueryAnalyzer()
    
    test_cases = [
        # Core triggers
        ("use live sources for AI news", QueryType.WEB_SEARCH),
        ("browse the web for information", QueryType.WEB_SEARCH),
        ("search online for Python tutorials", QueryType.WEB_SEARCH),
        ("get information from the web", QueryType.WEB_SEARCH),
        
        # Time-based triggers
        ("real-time stock prices", QueryType.WEB_SEARCH),
        ("up-to-date COVID statistics", QueryType.WEB_SEARCH),
        ("latest information about Tesla", QueryType.WEB_SEARCH),
        ("today's news headlines", QueryType.WEB_SEARCH),
        
        # Additional aliases
        ("latest from the web about crypto", QueryType.WEB_SEARCH),
        ("pull from web the weather data", QueryType.WEB_SEARCH),
        ("real time data on markets", QueryType.WEB_SEARCH),
        ("provide source links for climate change", QueryType.WEB_SEARCH),
        ("with citations about quantum computing", QueryType.WEB_SEARCH),
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*60)
    print("TEST: Explicit Web Search Triggers")
    print("="*60)
    
    for query, expected in test_cases:
        query_type, _ = analyzer.analyze_query(query)
        if query_type == expected:
            print(f"[PASS] PASS: '{query[:40]}...'")
            passed += 1
        else:
            print(f"[FAIL] FAIL: '{query[:40]}...' - Got {query_type}, expected {expected}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_negation_handling():
    """Test that negations properly prevent web search."""
    analyzer = QueryAnalyzer()
    
    test_cases = [
        # Direct negations
        ("don't use live sources", QueryType.GENERAL_CHAT),
        ("do not browse the web", QueryType.GENERAL_CHAT),
        ("no need to search online", QueryType.GENERAL_CHAT),
        ("without using live sources", QueryType.GENERAL_CHAT),
        
        # Negations with context
        ("tell me about AI but don't use live sources", QueryType.GENERAL_CHAT),
        ("weather forecast without real-time data", QueryType.WEATHER),
        ("property prices but skip web search", QueryType.PROPERTY_SEARCH),  # No analysis verb
        
        # Should still trigger (negation not near trigger or not negating the trigger)
        ("use live sources even if others don't", QueryType.WEB_SEARCH),
        ("I don't care, use live sources", QueryType.WEB_SEARCH),
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*60)
    print("TEST: Negation Handling")
    print("="*60)
    
    for query, expected in test_cases:
        query_type, _ = analyzer.analyze_query(query)
        if query_type == expected:
            print(f"[PASS] PASS: '{query[:40]}...'")
            passed += 1
        else:
            print(f"[FAIL] FAIL: '{query[:40]}...' - Got {query_type}, expected {expected}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_priority_override():
    """Test that explicit web search overrides domain-specific keywords."""
    analyzer = QueryAnalyzer()
    
    test_cases = [
        # Web search should override weather
        ("use live sources for Sydney weather", QueryType.WEB_SEARCH),
        ("browse the web for weather forecast", QueryType.WEB_SEARCH),
        
        # Web search should override property
        ("use live sources for property trends", QueryType.WEB_SEARCH),
        ("real-time property data in Bondi", QueryType.WEB_SEARCH),
        
        # Web search should override news
        ("browse the web for latest news", QueryType.WEB_SEARCH),
        ("live sources for breaking news", QueryType.WEB_SEARCH),
        
        # Domain without explicit (should use domain classification)
        ("weather in Sydney", QueryType.WEATHER),
        ("property search in Bondi", QueryType.PROPERTY_SEARCH),
        ("latest property listings", QueryType.PROPERTY_SEARCH),
        ("what's the time", QueryType.TIME),
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*60)
    print("TEST: Priority Override (Explicit > Domain)")
    print("="*60)
    
    for query, expected in test_cases:
        query_type, _ = analyzer.analyze_query(query)
        if query_type == expected:
            print(f"[PASS] PASS: '{query[:40]}...'")
            passed += 1
        else:
            print(f"[FAIL] FAIL: '{query[:40]}...' - Got {query_type}, expected {expected}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_session_preferences():
    """Test session preference memory for web search."""
    analyzer = QueryAnalyzer()
    session_id = "test_session_123"
    
    print("\n" + "="*60)
    print("TEST: Session Preference Memory")
    print("="*60)
    
    # Test enabling persistent web search
    query_type, params = analyzer.analyze_query("always use live sources", session_id)
    assert query_type == QueryType.WEB_SEARCH
    assert session_id in analyzer.session_preferences
    print("[PASS] Enabled persistent web search")
    
    # Test that subsequent queries use web search
    query_type, params = analyzer.analyze_query("what's the weather", session_id)
    assert query_type == QueryType.WEB_SEARCH
    assert params.get("session_forced") == True
    print("[PASS] Regular query forced to web search")
    
    # Test disabling persistent web search
    query_type, _ = analyzer.analyze_query("stop using live sources", session_id)
    assert query_type == QueryType.GENERAL_CHAT
    assert session_id not in analyzer.session_preferences
    print("[PASS] Disabled persistent web search")
    
    # Test that queries now use normal classification
    query_type, _ = analyzer.analyze_query("what's the weather", session_id)
    assert query_type == QueryType.WEATHER
    print("[PASS] Regular query uses normal classification")
    
    print("\nAll session preference tests passed!")
    return True


def test_implicit_web_search():
    """Test implicit web search triggers (lower priority)."""
    analyzer = QueryAnalyzer()
    
    test_cases = [
        # Should trigger implicit web search
        ("what is machine learning", QueryType.WEB_SEARCH),
        ("who is the CEO of Apple", QueryType.WEB_SEARCH),
        ("how to bake a cake", QueryType.WEB_SEARCH),
        ("explain quantum computing", QueryType.WEB_SEARCH),
        
        # Domain takes precedence over implicit
        ("what is the weather today", QueryType.WEATHER),  # Weather domain wins
        ("tell me about property prices", QueryType.PROPERTY_ANALYSIS),  # Property wins
        
        # Greetings take precedence
        ("hello there", QueryType.GREETING),
        ("hi, how are you", QueryType.GREETING),
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*60)
    print("TEST: Implicit Web Search (Fallback)")
    print("="*60)
    
    for query, expected in test_cases:
        query_type, _ = analyzer.analyze_query(query)
        if query_type == expected:
            print(f"[PASS] PASS: '{query[:40]}...'")
            passed += 1
        else:
            print(f"[FAIL] FAIL: '{query[:40]}...' - Got {query_type}, expected {expected}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_fallback_behavior():
    """Test fallback behavior when web APIs are unavailable."""
    analyzer = QueryAnalyzer()
    session_id = "test_fallback"
    
    print("\n" + "="*60)
    print("TEST: Fallback Behavior (Missing APIs)")
    print("="*60)
    
    test_cases = [
        # Web search with property context → Property fallback
        ("use live sources for property data", QueryType.PROPERTY_SEARCH, 
         "Note: Live sources unavailable, using cached property data."),
        
        # Web search with weather context → Weather fallback
        ("browse the web for weather updates", QueryType.WEATHER,
         "Note: Live sources unavailable, using weather service."),
        
        # Web search with news context → News fallback
        ("real-time news updates", QueryType.NEWS,
         "Note: Live sources unavailable, using cached news."),
        
        # Web search with no domain → General fallback
        ("use live sources for AI research", QueryType.GENERAL_CHAT,
         "Note: Live sources unavailable, using AI knowledge base."),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_type, expected_notice in test_cases:
        # Test with APIs unavailable
        query_type, params, notice = analyzer.analyze_query_with_fallback(
            query, session_id, has_web_apis=False
        )
        
        if query_type == expected_type and notice == expected_notice:
            print(f"[PASS] PASS: '{query[:40]}...' -> {expected_type.value}")
            passed += 1
        else:
            print(f"[FAIL] FAIL: '{query[:40]}...'")
            print(f"  Expected: {expected_type.value}, Got: {query_type.value}")
            print(f"  Expected notice: {expected_notice}")
            print(f"  Got notice: {notice}")
            failed += 1
    
    # Test with APIs available (no fallback)
    query = "use live sources for latest news"
    query_type, _, notice = analyzer.analyze_query_with_fallback(
        query, session_id, has_web_apis=True
    )
    
    if query_type == QueryType.WEB_SEARCH and notice is None:
        print(f"[PASS] PASS: With APIs available, no fallback occurs")
        passed += 1
    else:
        print(f"[FAIL] FAIL: With APIs available, should not fallback")
        failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_classification_ordering():
    """Test the complete classification priority chain."""
    analyzer = QueryAnalyzer()
    
    print("\n" + "="*60)
    print("TEST: Classification Priority Chain")
    print("="*60)
    
    # The priority order should be:
    # 1. Session preferences
    # 2. Explicit web search
    # 3. Greeting
    # 4. Domain-specific (weather, time, news, property, calculation)
    # 5. Implicit web search
    # 6. General chat
    
    test_chain = [
        ("hello", QueryType.GREETING, "Greeting beats everything except session/explicit"),
        ("weather today", QueryType.WEATHER, "Domain beats implicit/general"),
        ("what is AI", QueryType.WEB_SEARCH, "Implicit beats general"),
        ("let's chat", QueryType.GENERAL_CHAT, "General is default"),
        ("use live sources hello", QueryType.WEB_SEARCH, "Explicit beats greeting"),
        ("use live sources for weather", QueryType.WEB_SEARCH, "Explicit beats domain"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected, reason in test_chain:
        query_type, _ = analyzer.analyze_query(query)
        if query_type == expected:
            print(f"[PASS] PASS: {reason}")
            passed += 1
        else:
            print(f"[FAIL] FAIL: {reason}")
            print(f"  Query: '{query}' - Got {query_type}, expected {expected}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("COMPREHENSIVE CLASSIFICATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Explicit Triggers", test_explicit_web_search_triggers),
        ("Negation Handling", test_negation_handling),
        ("Priority Override", test_priority_override),
        ("Session Preferences", test_session_preferences),
        ("Implicit Search", test_implicit_web_search),
        ("Fallback Behavior", test_fallback_behavior),
        ("Classification Order", test_classification_ordering),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[FAIL] ERROR in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, success in results:
        status = "[PASS] PASSED" if success else "[FAIL] FAILED"
        print(f"{name:25} {status}")
        if not success:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n[SUCCESS] ALL TESTS PASSED! Classification system working correctly.")
        return 0
    else:
        print("\n[WARNING] SOME TESTS FAILED. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)