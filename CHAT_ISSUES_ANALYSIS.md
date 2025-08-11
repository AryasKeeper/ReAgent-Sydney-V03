# Chat Issues Analysis & Solutions

## Problems Identified

### 1. **Markdown Not Rendering in Frontend**
- **Issue**: Text like `**Buyer Assistance**` showing raw instead of bold
- **Cause**: Frontend not parsing Markdown in SSE stream
- **Solution**: Frontend needs Markdown parser or backend should send plain text

### 2. **Property Query Not Using Web Search**
- **Issue**: "using up-to-date data" query returned generic response
- **Cause**: Query classified as PROPERTY_SEARCH instead of WEB_SEARCH
- **Why**: Property keywords are checked BEFORE web search keywords in some paths

### 3. **Generic Response Quality**
- **Issue**: Low-quality response with just a Domain.com.au link
- **Cause**: Fallback to mock data when Firecrawl fails
- **Solution**: Should use web browsing pipeline for "up-to-date" requests

## Root Cause Analysis

The query "Can you help me find 3-bedroom houses in Bondi under $5M using up-to-date data?" contains:
- Property keywords: "houses", "bedroom", "Bondi" 
- Web trigger: "up-to-date"

However, the issue is in `agent_whisperer.py`:
1. Query gets classified correctly as WEB_SEARCH
2. BUT with fallback logic, if web APIs are missing, it falls back to PROPERTY_SEARCH
3. The property search then uses its own fallback (mock data)

## Immediate Fixes Needed

### Fix 1: Ensure Web Search Executes for Property+Web Queries

```python
# In agent_whisperer.py, around line 108-116
elif query_type == QueryType.PROPERTY_SEARCH:
    # Check if this was originally a web search request
    if "up-to-date" in request.message.lower() or "live" in request.message.lower():
        # Force web search path
        summary, sources = await agentic_browse(request.message)
        yield format_sse_chunk(summary)
        if sources:
            yield format_sse_chunk(sources, "sources_meta")
    else:
        # Regular property search
        intro = get_search_intro()
        yield format_sse_chunk(intro)
        result = await property_search.search_properties(request.message)
        yield format_sse_chunk(result)
```

### Fix 2: Disable Markdown in Responses

The frontend isn't parsing Markdown. Either:
1. Update frontend to parse Markdown
2. OR send plain text from backend

For quick fix in backend:
```python
# Remove markdown formatting from AI responses
text = text.replace("**", "")  # Remove bold
text = text.replace("•", "-")   # Replace bullet points
```

### Fix 3: Better Property Web Search

When property queries request "up-to-date" data, use the web browsing pipeline:
```python
# In agentic_browse.py
if "property" in query.lower() or "house" in query.lower():
    # Add property-specific search terms
    enhanced_query = f"{query} site:domain.com.au OR site:realestate.com.au latest listings"
```

## Testing Commands

Test the classification:
```bash
curl -X POST http://localhost:8000/api/v1/debug/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "find 3-bedroom houses in Bondi under $5M using up-to-date data"}'
```

Test the full pipeline:
```bash
curl -X POST http://localhost:8000/api/v1/debug/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{"query": "find 3-bedroom houses in Bondi under $5M using up-to-date data"}'
```

## Verification Steps

1. **Check Classification**: Should be WEB_SEARCH not PROPERTY_SEARCH
2. **Check Execution**: Should use agentic_browse not property_search
3. **Check Response**: Should have real URLs and synthesized content
4. **Check Formatting**: No raw Markdown in frontend display

## Quick Workaround

For immediate testing, try these queries that force web search:
- "use live sources to find 3-bedroom houses in Bondi under $5M"
- "browse the web for Bondi property listings with 3 bedrooms"
- "search online for current Bondi real estate under $5M"

These should bypass the property search fallback and use the web browsing pipeline directly.