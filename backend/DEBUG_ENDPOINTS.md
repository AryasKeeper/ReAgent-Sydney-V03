# Debug Endpoints Reference

## Quick Test Commands

These debug endpoints help test each component of the web browsing pipeline independently.

### 1. Check Configuration
```bash
curl http://localhost:8000/api/v1/debug/config
```
Shows which APIs are configured and if minimum requirements are met.

### 2. Test Query Classification
```bash
curl -X POST http://localhost:8000/api/v1/debug/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "use live sources for AI news"}'
```
Should return `"is_web_search": true`

### 3. Test Brave Search
```bash
curl -X POST http://localhost:8000/api/v1/debug/brave-search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence news"}'
```
Returns URLs found by Brave search.

### 4. Test Content Extraction (Firecrawl)
```bash
curl -X POST http://localhost:8000/api/v1/debug/extract-firecrawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### 5. Test Content Extraction (Browserless)
```bash
curl -X POST http://localhost:8000/api/v1/debug/extract-browserless \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### 6. Test Content Extraction (Any Available)
```bash
curl -X POST http://localhost:8000/api/v1/debug/extract-any \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```
Tests the fallback chain: Firecrawl → Browserless → Fallback

### 7. Test AI Synthesis
```bash
curl -X POST http://localhost:8000/api/v1/debug/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is artificial intelligence?",
    "contents": [
      {"url": "https://example1.com", "content": "AI is machine intelligence..."},
      {"url": "https://example2.com", "content": "Artificial intelligence refers to..."}
    ]
  }'
```

### 8. Test Full Pipeline
```bash
curl -X POST http://localhost:8000/api/v1/debug/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{"query": "use live sources to find latest AI developments"}'
```
Runs the complete browse pipeline end-to-end.

## Debug Flow

1. **Start with config check** (`/debug/config`)
   - Verify all required APIs are configured
   - Check if minimum requirements are met

2. **Test query classification** (`/debug/classify`)
   - Ensure your test queries trigger WEB_SEARCH

3. **Test search** (`/debug/brave-search`)
   - Verify Brave API returns URLs

4. **Test extraction** (`/debug/extract-any`)
   - Check if content can be extracted from URLs

5. **Test synthesis** (`/debug/synthesize`)
   - Verify AI can synthesize content

6. **Test full pipeline** (`/debug/full-pipeline`)
   - Validate end-to-end functionality

## Common Issues

### "BRAVE_API_KEY not configured"
- Add `BRAVE_API_KEY=your-key` to `.env` file
- Restart the backend server

### "No AI provider configured"
- Add either `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` to `.env`
- Restart the backend server

### Content extraction returns null
- Check if Firecrawl or Browserless keys are configured
- Try different URLs (some sites block scraping)

### Synthesis fails
- Verify AI provider keys are valid
- Check token limits and rate limiting

## Python Test Script

```python
import httpx
import asyncio

async def test_browsing():
    async with httpx.AsyncClient() as client:
        # Check config
        r = await client.get("http://localhost:8000/api/v1/debug/config")
        config = r.json()
        print(f"Web browsing ready: {config['web_browsing_ready']}")
        
        # Test classification
        r = await client.post(
            "http://localhost:8000/api/v1/debug/classify",
            json={"query": "use live sources for news"}
        )
        result = r.json()
        print(f"Triggers web search: {result['is_web_search']}")
        
        # Test full pipeline
        r = await client.post(
            "http://localhost:8000/api/v1/debug/full-pipeline",
            json={"query": "latest technology news"}
        )
        result = r.json()
        print(f"Pipeline success: {result['success']}")
        if result['success']:
            print(f"Found {result['source_count']} sources")
            print(f"Summary length: {result['summary_length']} chars")

asyncio.run(test_browsing())
```

## Accessing Debug UI

When `DEBUG=true` in `.env`, visit:
- http://localhost:8000/docs - Swagger UI with all endpoints
- http://localhost:8000/redoc - Alternative API documentation

The debug endpoints will be listed under the "debug" tag.