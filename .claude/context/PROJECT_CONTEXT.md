# ReAgent Sydney V03 - Project Context
*Generated: 2025-08-11*
*Version: 1.0.0*

## Executive Summary

ReAgent Sydney V03 is a real estate AI assistant for the Sydney market, featuring a FastAPI backend and Next.js 15 frontend with Server-Sent Events (SSE) streaming. The project shows promise but requires immediate security fixes and architectural improvements.

**Project Health Score: 5.2/10** - Critical security vulnerabilities need immediate attention.

## Architecture Overview

### Technology Stack
- **Backend**: Python 3.x, FastAPI, Pydantic, OpenAI GPT, Redis
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Communication**: Server-Sent Events (SSE) for streaming
- **External Services**: OpenAI, Anthropic, Tavily, Firecrawl, Brave Search

### Core Pattern: SSE Streaming
```
Format: 0:"content"\n
Finish: d:{"finishReason":"stop"}\n
```
This format is critical for Vercel AI SDK compatibility.

## Current State Assessment

### Security (3/10) - CRITICAL
- ⚠️ DEBUG=True hardcoded in production
- ⚠️ API keys exposed in logs and debug endpoints
- ⚠️ Optional authentication (REQUIRE_API_KEY: False)
- ⚠️ Rate limiting fails open
- ⚠️ Missing input validation
- ⚠️ No security headers (CSP, X-Frame-Options)

### Code Quality (6.5/10)
- ✅ Good async/await patterns
- ✅ Pydantic models for validation
- ❌ 4 duplicate AI router implementations
- ❌ 25 test files scattered in root
- ❌ Business logic in API endpoints

### Architecture (6/10)
- ✅ Service layer separation
- ✅ Clear query routing
- ❌ Global singleton anti-pattern
- ❌ No dependency injection
- ❌ Mixed sync/async operations

### Performance (6/10)
- ❌ Synchronous Redis operations blocking event loop
- ❌ No connection pooling
- ❌ Missing caching layer
- ✅ Streaming architecture works well
- Potential 40-60% improvement available

### Testing (3/10)
- ❌ 0% frontend test coverage
- ❌ Only integration tests in backend
- ❌ No unit tests
- ❌ No CI/CD pipeline

## Key Design Patterns

### Query Routing System
```python
QueryType Enum → analyze_query() → Route to handler
Types: GREETING, PROPERTY_SEARCH, WEATHER, WEB_SEARCH, etc.
```

### Service Layer Architecture
- **AI Router**: OpenAI GPT integration with streaming
- **Query Analyzer**: Classification and routing
- **Session Manager**: 30-minute timeout, greeting control
- **Property Search**: Mock data with fallback

### Fallback Strategy
```
Primary: Firecrawl → Fallback: Tavily → Ultimate: Mock data
```

## Critical Issues Inventory

### Week 1 Priorities (Security)
1. Set DEBUG=False in production
2. Enable mandatory authentication (JWT/OAuth2)
3. Implement input validation with Pydantic
4. Remove debug endpoints in production
5. Add security headers

### Week 2-3 Priorities (Performance)
1. Implement connection pooling (40% gain expected)
2. Convert Redis operations to async
3. Consolidate 4 AI routers into 1
4. Add caching layer
5. Optimize bundle size

### Month 1 Priorities (Quality)
1. Set up frontend testing infrastructure
2. Add unit tests (target 80% coverage)
3. Implement CI/CD pipeline
4. Refactor to dependency injection
5. Move business logic to service layer

## Technical Debt

### Duplication
- 4 AI router implementations (ai_router.py, ai_router_simple.py, ai_router_tools.py, ai_router_responses.py)
- Should consolidate into single configurable router

### Anti-Patterns
- Global singletons preventing proper testing
- Mixed sync/async in SessionManager
- Business logic in API endpoints
- No dependency injection

### File Organization
- 25 test files in root directory
- Should be in tests/ directory
- Missing proper test structure

## Performance Metrics

### Current Performance
- Response time: 800-1500ms average
- Bundle size: Not measured
- Memory usage: Not monitored
- Error rate: Not tracked

### Target Performance
- Response time: 300-600ms (50-60% improvement)
- Bundle size: <500KB initial
- Memory usage: <500MB per instance
- Error rate: <0.1%

## Development Workflow

### Adding New Query Types
1. Update `QueryType` enum in `services/query_analyzer.py`
2. Add detection logic in `analyze_query()` method
3. Add handler in `api/agent_whisperer.py` chat_stream function

### Modifying AI Behavior
- Edit system prompt in `services/ai_router_simple.py`
- Adjust temperature and max_tokens for response characteristics

### Common Issues & Solutions
- **SSE Format Issues**: Check `utils/streaming.py` format_sse_chunk()
- **CORS Errors**: Verify allowed origins in app.py
- **Streaming Breaks**: Check browser Network tab for SSE format

## Recommended Roadmap

### Phase 1: Security (Week 1)
- [ ] Fix DEBUG mode
- [ ] Enable authentication
- [ ] Add input validation
- [ ] Remove debug endpoints
- [ ] Add security headers

### Phase 2: Performance (Weeks 2-3)
- [ ] Connection pooling
- [ ] Async Redis
- [ ] Consolidate routers
- [ ] Add caching
- [ ] Frontend optimization

### Phase 3: Quality (Month 1)
- [ ] Frontend testing setup
- [ ] Unit test coverage
- [ ] CI/CD pipeline
- [ ] Dependency injection
- [ ] Service layer refactor

### Phase 4: Features (Month 2+)
- [ ] Enhanced property search
- [ ] User preferences
- [ ] Analytics dashboard
- [ ] Advanced AI features

## Agent Coordination Notes

### Previous Agent Findings
- **code-reviewer**: Identified duplication, poor error handling
- **security-auditor**: Found critical vulnerabilities
- **architect-reviewer**: SOLID violations, missing patterns
- **performance-engineer**: Blocking operations, missing optimizations
- **test-automator**: Zero frontend coverage

### Coordination Patterns
- Security fixes must come first (blocking)
- Performance can be done in parallel with testing setup
- Architecture refactoring should follow security fixes
- Feature development only after core issues resolved

## Configuration & Environment

### Required Environment Variables
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-... (optional)
TAVILY_API_KEY=... (optional)
FIRECRAWL_API_KEY=... (optional)
BRAVE_API_KEY=... (optional)
REQUIRE_API_KEY=true (MUST SET)
DEBUG=false (MUST SET)
```

### Port Configuration
- Backend: 8001 (to avoid conflicts)
- Frontend: 3000 (standard Next.js)
- Redis: 6379 (if using)

## Success Metrics

### Short Term (1 month)
- Security score: 8/10
- Test coverage: 60%+
- Response time: <600ms
- Zero critical vulnerabilities

### Medium Term (3 months)
- Full test coverage (80%+)
- CI/CD pipeline active
- Performance targets met
- Clean architecture implemented

### Long Term (6 months)
- Production-ready system
- Scalable architecture
- Feature-complete
- Maintainable codebase

## Notes for Future Agents

1. **Always check security first** - The system has critical vulnerabilities
2. **Maintain SSE format** - Breaking this breaks the entire chat
3. **Test streaming locally** - Use browser Network tab to verify
4. **Consolidate before adding** - Fix duplication before new features
5. **Document decisions** - Update this context file with major changes

---
*This context file should be updated after major changes or architectural decisions.*