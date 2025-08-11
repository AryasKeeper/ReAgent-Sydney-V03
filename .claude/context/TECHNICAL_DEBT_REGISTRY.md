# Technical Debt Registry
*Last Updated: 2025-08-11*
*Version: 1.0.0*

## Critical Priority (P0) - Security & Stability

### SEC-001: DEBUG Mode in Production
- **Impact**: Exposes sensitive data, stack traces, API keys
- **Location**: `backend/config.py` line ~41
- **Fix**: Set `DEBUG = False` or use environment variable
- **Effort**: 5 minutes
- **Risk if unfixed**: Data breach, API key exposure

### SEC-002: Optional Authentication
- **Impact**: API accessible without authentication
- **Location**: `backend/config.py` - REQUIRE_API_KEY defaults to False
- **Fix**: Set `REQUIRE_API_KEY = True`, implement JWT/OAuth2
- **Effort**: 2-4 hours
- **Risk if unfixed**: Unauthorized access, abuse

### SEC-003: API Keys in Logs
- **Impact**: Sensitive credentials exposed in application logs
- **Location**: Throughout codebase where settings are logged
- **Fix**: Implement credential masking in logging
- **Effort**: 2 hours
- **Risk if unfixed**: Credential theft

### SEC-004: Missing Input Validation
- **Impact**: Potential injection attacks, crashes
- **Location**: `api/agent_whisperer.py` - user message not validated
- **Fix**: Add Pydantic validators for all inputs
- **Effort**: 3 hours
- **Risk if unfixed**: Security vulnerabilities, service disruption

### SEC-005: Debug Endpoints Exposed
- **Impact**: Internal data exposed via debug routes
- **Location**: `backend/api/debug_browse.py`
- **Fix**: Disable in production or add authentication
- **Effort**: 1 hour
- **Risk if unfixed**: Information disclosure

## High Priority (P1) - Performance & Architecture

### PERF-001: Synchronous Redis Operations
- **Impact**: Blocks async event loop, degrades performance
- **Location**: `services/session_manager.py`
- **Fix**: Use aioredis for async operations
- **Effort**: 4 hours
- **Risk if unfixed**: 30-40% performance degradation

### PERF-002: No Connection Pooling
- **Impact**: Creates new connections per request
- **Location**: External service calls (OpenAI, Tavily, etc.)
- **Fix**: Implement httpx with connection pooling
- **Effort**: 6 hours
- **Potential gain**: 40% performance improvement

### ARCH-001: Four Duplicate AI Routers
- **Impact**: Maintenance nightmare, inconsistent behavior
- **Files**:
  - `services/ai_router.py`
  - `services/ai_router_simple.py`
  - `services/ai_router_tools.py`
  - `services/ai_router_responses.py`
- **Fix**: Consolidate into single configurable router
- **Effort**: 8 hours
- **Risk if unfixed**: Bugs, inconsistent behavior

### ARCH-002: Global Singleton Anti-pattern
- **Impact**: Prevents proper testing, tight coupling
- **Location**: Service instantiations (session_manager, query_analyzer)
- **Fix**: Implement dependency injection
- **Effort**: 12 hours
- **Risk if unfixed**: Untestable code, maintenance issues

### ARCH-003: Business Logic in API Layer
- **Impact**: Violates separation of concerns
- **Location**: `api/agent_whisperer.py` - chat_stream function
- **Fix**: Move to service layer
- **Effort**: 6 hours
- **Risk if unfixed**: Hard to test, maintain

## Medium Priority (P2) - Quality & Testing

### TEST-001: Zero Frontend Test Coverage
- **Impact**: No confidence in frontend changes
- **Location**: `frontend/` - no test files
- **Fix**: Set up Jest, React Testing Library
- **Effort**: 8 hours setup + ongoing
- **Risk if unfixed**: Frontend regressions

### TEST-002: No Unit Tests
- **Impact**: Only integration tests exist
- **Location**: Backend services lack unit tests
- **Fix**: Add unit tests for services
- **Effort**: 16 hours
- **Target**: 80% coverage

### TEST-003: Test Files in Root Directory
- **Impact**: Cluttered project structure
- **Location**: 25 test files in backend root
- **Fix**: Move to `tests/` directory
- **Effort**: 1 hour
- **Risk if unfixed**: Confusion, maintenance issues

### QUAL-001: No Error Boundaries
- **Impact**: Errors crash entire frontend
- **Location**: React components
- **Fix**: Add error boundaries
- **Effort**: 4 hours
- **Risk if unfixed**: Poor user experience

### QUAL-002: Inconsistent Error Handling
- **Impact**: Unpredictable failure modes
- **Location**: Throughout backend services
- **Fix**: Standardize error handling patterns
- **Effort**: 6 hours
- **Risk if unfixed**: Poor debugging, user experience

## Low Priority (P3) - Optimization & Enhancement

### OPT-001: No Caching Layer
- **Impact**: Repeated expensive operations
- **Location**: API responses, external service calls
- **Fix**: Implement Redis caching
- **Effort**: 8 hours
- **Potential gain**: 20-30% performance improvement

### OPT-002: Missing Response Compression
- **Impact**: Larger payload sizes
- **Location**: FastAPI responses
- **Fix**: Enable gzip compression
- **Effort**: 1 hour
- **Potential gain**: 60-70% bandwidth reduction

### OPT-003: No Bundle Optimization
- **Impact**: Larger frontend bundle
- **Location**: Next.js build config
- **Fix**: Implement code splitting, tree shaking
- **Effort**: 4 hours
- **Potential gain**: 30-40% bundle size reduction

### ENH-001: No Monitoring/Observability
- **Impact**: Blind to production issues
- **Location**: Entire application
- **Fix**: Add APM, logging, metrics
- **Effort**: 12 hours
- **Risk if unfixed**: Slow incident response

### ENH-002: No Rate Limiting on Frontend
- **Impact**: Potential for client-side abuse
- **Location**: Frontend API calls
- **Fix**: Implement client-side rate limiting
- **Effort**: 3 hours
- **Risk if unfixed**: API abuse

## Debt Metrics

### Total Technical Debt Score: 142 points
- Critical (P0): 5 items × 10 points = 50 points
- High (P1): 5 items × 6 points = 30 points  
- Medium (P2): 5 items × 4 points = 20 points
- Low (P3): 5 items × 2 points = 10 points
- Code duplication penalty: +32 points

### Estimated Total Effort: ~120 hours
- Critical fixes: ~15 hours
- High priority: ~40 hours
- Medium priority: ~35 hours
- Low priority: ~30 hours

### Risk Assessment
- **Security Risk**: CRITICAL - Immediate action required
- **Performance Risk**: HIGH - Significant user impact
- **Maintainability Risk**: HIGH - Increasing cost of change
- **Reliability Risk**: MEDIUM - Some failure modes exist

## Recommended Fix Order

### Sprint 1 (Week 1) - Security
1. SEC-001: Disable DEBUG mode (5 min)
2. SEC-002: Enable authentication (4 hrs)
3. SEC-004: Input validation (3 hrs)
4. SEC-003: Mask credentials (2 hrs)
5. SEC-005: Secure debug endpoints (1 hr)

### Sprint 2 (Week 2-3) - Performance
1. PERF-002: Connection pooling (6 hrs)
2. PERF-001: Async Redis (4 hrs)
3. ARCH-001: Consolidate routers (8 hrs)
4. OPT-002: Response compression (1 hr)

### Sprint 3 (Week 4-5) - Testing
1. TEST-001: Frontend test setup (8 hrs)
2. TEST-002: Backend unit tests (16 hrs)
3. TEST-003: Organize test files (1 hr)

### Sprint 4 (Week 6-7) - Architecture
1. ARCH-002: Dependency injection (12 hrs)
2. ARCH-003: Service layer refactor (6 hrs)
3. QUAL-002: Error handling (6 hrs)

### Ongoing - Optimization
- OPT-001: Caching layer
- OPT-003: Bundle optimization
- ENH-001: Monitoring
- ENH-002: Frontend rate limiting

## Success Criteria

### Short Term (1 month)
- All P0 security issues resolved
- Core performance issues fixed
- Basic test infrastructure in place

### Medium Term (3 months)
- 80% test coverage achieved
- All P1 issues resolved
- Architecture improvements complete

### Long Term (6 months)
- All technical debt addressed
- Monitoring and observability in place
- Clean, maintainable codebase

## Notes

- Security fixes must be deployed immediately
- Performance fixes can be batched
- Testing infrastructure enables safe refactoring
- Architecture improvements should be gradual
- Monitor metrics after each fix to validate improvements

---
*Update this registry as debt is added or resolved*