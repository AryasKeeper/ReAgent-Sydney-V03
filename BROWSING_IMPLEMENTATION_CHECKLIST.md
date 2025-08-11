# Web Browsing Implementation Checklist

## ✅ Completed by Claude Code

### Phase 1: Query Classification Enhancement
- [x] Updated `backend/services/query_analyzer.py`
  - Added "live sources", "real-time", "browse" keywords
  - Enhanced `_needs_web_search()` function
  - Lines 192-205 updated

### Phase 2: Browse Pipeline Implementation  
- [x] Completely rewrote `backend/services/agentic_browse.py`
  - Implemented `extract_content_firecrawl()` function
  - Implemented `extract_content_browserless()` fallback
  - Created `extract_url_content()` with fallback chain
  - Built `synthesize_content()` for AI synthesis
  - Enhanced `agentic_browse()` with full pipeline

### Phase 3: SSE Formatting Enhancement
- [x] Updated `backend/utils/streaming.py`
  - Added `sources_meta` chunk type (SSE type 8)
  - Maintains backward compatibility
  - Lines 28-32 added

### Phase 4: Agent Whisperer Integration
- [x] Updated `backend/api/agent_whisperer.py`
  - Enhanced WEB_SEARCH handling (lines 142-176)
  - Added sources metadata streaming
  - Maintained fallback to text format

### Phase 5: Testing Infrastructure
- [x] Created `backend/test_web_browsing.py`
  - Query classification tests
  - Browse pipeline validation
  - SSE format verification
  - Comprehensive test suite

### Phase 6: Configuration Templates
- [x] Created `.env.browsing` template
  - All required API keys documented
  - Clear instructions for each service
  - Optional enhancements included

---

## 📋 DevOps Team Action Items

### Immediate Actions (5-10 minutes)

1. **Create .env file**
   ```bash
   cd backend
   cp .env.browsing .env
   ```

2. **Add API Keys to .env**
   - [ ] BRAVE_API_KEY (Required)
   - [ ] OPENAI_API_KEY or ANTHROPIC_API_KEY (Required)
   - [ ] FIRECRAWL_API_KEY (Recommended)
   - [ ] BROWSERLESS_TOKEN (Optional)

3. **Install any missing dependencies**
   ```bash
   pip install httpx pydantic-settings
   ```

### Testing Actions (10-15 minutes)

4. **Run the test script**
   ```bash
   cd backend
   python test_web_browsing.py
   ```
   
   Expected output:
   - Phase 1: Query Classification ✅
   - Phase 2: Browse Pipeline ✅ (if API keys set)
   - Phase 3: SSE Formatting ✅

5. **Start the backend server**
   ```bash
   python app.py
   # or
   uvicorn app:app --reload --port 8000
   ```

6. **Test with curl**
   ```bash
   curl -X POST http://localhost:8000/api/v1/agent-whisperer/chat/stream \
     -H "Content-Type: application/json" \
     -d '{"message":"use live sources to find latest AI news","session_id":"test"}'
   ```

### Frontend Integration (5 minutes)

7. **Start frontend**
   ```bash
   cd ../frontend
   npm run dev
   ```

8. **Test in browser**
   - Navigate to http://localhost:3005
   - Try: "use live sources for latest technology news"
   - Verify sources appear and content is synthesized

### Validation Checklist

9. **Core Functionality**
   - [ ] Query "use live sources" triggers WEB_SEARCH
   - [ ] Brave search returns URLs
   - [ ] Content extraction works (Firecrawl or Browserless)
   - [ ] AI synthesis generates coherent response
   - [ ] Sources displayed in frontend

10. **Fallback Testing**
    - [ ] Works without Firecrawl (falls back to Browserless)
    - [ ] Works without Browserless (returns URLs only)
    - [ ] Handles search failures gracefully

---

## 🔍 Debugging Guide

### If queries don't trigger web search:
1. Check query_analyzer.py line 192-205
2. Verify keywords are lowercase in query
3. Test with explicit: "browse the web for..."

### If Brave search fails:
1. Verify BRAVE_API_KEY in .env
2. Check API key validity at brave.com
3. Look for rate limiting in logs

### If content extraction fails:
1. Check Firecrawl/Browserless API keys
2. Verify URLs are accessible
3. Check timeout settings (10s Firecrawl, 15s Browserless)

### If synthesis fails:
1. Verify OpenAI/Anthropic API key
2. Check AI router configuration
3. Monitor token usage in synthesis prompt

### If SSE streaming breaks:
1. Verify format in streaming.py
2. Check frontend Vercel AI SDK version (v3.4.33)
3. Monitor browser console for SSE errors

---

## 📊 Success Metrics

When fully working, you should see:

1. **Backend logs showing**:
   ```
   Query analyzed - Type: QueryType.WEB_SEARCH
   Starting agentic browse for: [query]
   Found 3 URLs from Brave search
   Content extracted via Firecrawl for [url]
   Synthesizing content from 3 sources
   ```

2. **Frontend displaying**:
   - Synthesized content from multiple sources
   - Source URLs listed at bottom
   - Smooth streaming experience

3. **Test script showing**:
   ```
   ✅ ALL TESTS PASSED - Web browsing functionality is working!
   ```

---

## 🎯 Final Verification

Run this command to verify everything:
```bash
cd backend
python -c "
from services.query_analyzer import query_analyzer, QueryType
q = 'use live sources for AI news'
t, p = query_analyzer.analyze_query(q)
print(f'✅ Query classification: {t == QueryType.WEB_SEARCH}')

from config import settings
print(f'✅ Brave API key: {bool(settings.BRAVE_API_KEY)}')
print(f'✅ AI provider: {bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)}')
"
```

All three should show ✅ for basic functionality.

---

## 📝 Notes

- The implementation preserves all existing functionality
- No breaking changes to existing endpoints
- Fallback chains ensure resilience
- SSE format maintains Vercel AI SDK compatibility
- Sources delivered via both metadata and text for flexibility

**Implementation by**: Claude Code
**Date**: 2025-08-11
**Version**: Web Browsing v1.0