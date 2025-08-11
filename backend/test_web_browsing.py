#!/usr/bin/env python3
"""
Web Browsing Functionality Test Script
Tests the complete browse pipeline: Query Classification → Search → Extract → Synthesize
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.query_analyzer import query_analyzer, QueryType
from services.agentic_browse import agentic_browse
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_query_classification():
    """Test that queries are properly classified as WEB_SEARCH."""
    test_queries = [
        ("use live sources for latest AI news", True),
        ("what is the weather today", True),
        ("search for information about Python", True),
        ("hello how are you", False),
        ("find real-time stock prices", True),
        ("browse the internet for React tutorials", True),
        ("2 + 2", False),
    ]
    
    print("\n" + "="*60)
    print("PHASE 1: Query Classification Test")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for query, should_be_web_search in test_queries:
        query_type, params = query_analyzer.analyze_query(query)
        is_web_search = (query_type == QueryType.WEB_SEARCH)
        
        if is_web_search == should_be_web_search:
            status = "[PASS] PASS"
            passed += 1
        else:
            status = "[FAIL] FAIL"
            failed += 1
        
        print(f"{status} | Query: '{query[:40]}...' | Type: {query_type.value}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


async def test_browse_pipeline():
    """Test the complete browse pipeline."""
    print("\n" + "="*60)
    print("PHASE 2: Browse Pipeline Test")
    print("="*60)
    
    # Check API keys
    print("\nAPI Key Configuration:")
    print(f"  BRAVE_API_KEY: {'[PASS] Set' if settings.BRAVE_API_KEY else '[FAIL] Not set'}")
    print(f"  FIRECRAWL_API_KEY: {'[PASS] Set' if settings.FIRECRAWL_API_KEY else '[FAIL] Not set'}")
    print(f"  BROWSERLESS_TOKEN: {'[PASS] Set' if settings.BROWSERLESS_TOKEN else '[FAIL] Not set'}")
    print(f"  OPENAI_API_KEY: {'[PASS] Set' if settings.OPENAI_API_KEY else '[FAIL] Not set'}")
    
    if not settings.BRAVE_API_KEY:
        print("\n[WARNING]  WARNING: No Brave API key - search will fail")
        print("   Add BRAVE_API_KEY to your .env file")
        return False
    
    # Test the browse pipeline
    test_query = "use live sources to find the latest news about artificial intelligence"
    print(f"\nTesting browse pipeline with: '{test_query}'")
    print("-" * 40)
    
    try:
        summary, sources = await agentic_browse(test_query)
        
        print("\n[CONTENT] SYNTHESIZED CONTENT:")
        print(summary[:500] + "..." if len(summary) > 500 else summary)
        
        print("\n[SOURCES] SOURCES:")
        if sources:
            for i, source in enumerate(sources, 1):
                print(f"  {i}. {source}")
        else:
            print("  No sources returned")
        
        # Validate results
        has_content = len(summary) > 50
        has_sources = len(sources) > 0
        
        print("\n[VALIDATION] VALIDATION:")
        print(f"  Content synthesis: {'[PASS] Pass' if has_content else '[FAIL] Fail'}")
        print(f"  Source extraction: {'[PASS] Pass' if has_sources else '[FAIL] Fail'}")
        
        return has_content
        
    except Exception as e:
        print(f"\n[FAIL] Pipeline Error: {e}")
        logger.exception("Browse pipeline test failed")
        return False


async def test_sse_streaming():
    """Test SSE formatting for web search results."""
    print("\n" + "="*60)
    print("PHASE 3: SSE Streaming Format Test")
    print("="*60)
    
    from utils.streaming import format_sse_chunk
    
    # Test different chunk types
    test_cases = [
        ("Hello world", "text", '0:"Hello world"\n'),
        ("", "finish", 'd:{"finishReason":"stop"}\n'),
        (["https://example.com", "https://test.com"], "sources_meta", '8:["https://example.com", "https://test.com"]\n'),
        ("Error message", "error", 'd:{"finishReason":"error","error":"Error message"}\n'),
    ]
    
    passed = 0
    failed = 0
    
    for content, chunk_type, expected in test_cases:
        try:
            result = format_sse_chunk(content, chunk_type)
            if result == expected:
                print(f"[PASS] PASS | Type: {chunk_type:12} | Output: {result.strip()}")
                passed += 1
            else:
                print(f"[FAIL] FAIL | Type: {chunk_type:12}")
                print(f"         Expected: {expected.strip()}")
                print(f"         Got:      {result.strip()}")
                failed += 1
        except Exception as e:
            print(f"[FAIL] ERROR | Type: {chunk_type:12} | Error: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("WEB BROWSING FUNCTIONALITY TEST SUITE")
    print("="*60)
    
    # Run tests
    classification_ok = test_query_classification()
    browse_ok = await test_browse_pipeline()
    sse_ok = await test_sse_streaming()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"  Query Classification: {'[PASS] PASSED' if classification_ok else '[FAIL] FAILED'}")
    print(f"  Browse Pipeline:      {'[PASS] PASSED' if browse_ok else '[FAIL] FAILED'}")
    print(f"  SSE Formatting:       {'[PASS] PASSED' if sse_ok else '[FAIL] FAILED'}")
    
    all_passed = classification_ok and browse_ok and sse_ok
    
    if all_passed:
        print("\n[PASS] ALL TESTS PASSED - Web browsing functionality is working!")
    else:
        print("\n[FAIL] SOME TESTS FAILED - Please check the output above")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)