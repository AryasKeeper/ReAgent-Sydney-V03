# Context Index - ReAgent Sydney V03
*Last Updated: 2025-08-11*
*Version: 1.0.0*

## Context File Directory

### 📋 PROJECT_CONTEXT.md
**Purpose**: Main project overview and current state
**Contents**:
- Architecture overview
- Technology stack
- Current assessment (security, quality, performance, testing)
- Key design patterns
- Development workflow
- Recommended roadmap
- Success metrics

**When to use**: Starting work on the project, understanding overall state

---

### 🔧 TECHNICAL_DEBT_REGISTRY.md
**Purpose**: Comprehensive technical debt tracking
**Contents**:
- Prioritized issue list (P0-P3)
- Impact assessments
- Effort estimates
- Risk analysis
- Fix recommendations
- Sprint planning

**When to use**: Planning fixes, understanding priorities, estimating work

---

### 📘 IMPLEMENTATION_GUIDE.md
**Purpose**: Step-by-step implementation instructions
**Contents**:
- Quick security fixes
- Performance optimizations
- Router consolidation strategy
- Testing setup
- DI pattern implementation
- CI/CD pipeline
- Common pitfalls

**When to use**: Actually implementing fixes, need code examples

---

## Quick Reference

### Critical Security Issues (Fix Immediately)
- DEBUG=True in production → See IMPLEMENTATION_GUIDE.md section 1
- Optional authentication → See IMPLEMENTATION_GUIDE.md section 2
- Missing input validation → See IMPLEMENTATION_GUIDE.md section 3

### Performance Bottlenecks
- No connection pooling → See IMPLEMENTATION_GUIDE.md "Performance Quick Wins"
- Sync Redis operations → See IMPLEMENTATION_GUIDE.md "Async Redis Operations"
- 4 duplicate routers → See IMPLEMENTATION_GUIDE.md "Router Consolidation"

### Testing Gaps
- 0% frontend coverage → See IMPLEMENTATION_GUIDE.md "Frontend Testing Setup"
- No unit tests → See IMPLEMENTATION_GUIDE.md "Backend Unit Test Example"

### Architecture Issues
- Global singletons → See IMPLEMENTATION_GUIDE.md "Dependency Injection Pattern"
- Business logic in API → See TECHNICAL_DEBT_REGISTRY.md ARCH-003

## Key File Locations

### Backend Structure
```
backend/
├── api/
│   ├── agent_whisperer.py    # Main chat endpoint (needs refactoring)
│   └── debug_browse.py        # Debug endpoints (remove in prod)
├── services/
│   ├── ai_router*.py          # 4 files to consolidate
│   ├── query_analyzer.py      # Query classification (working well)
│   └── session_manager.py     # Needs async Redis
├── utils/
│   └── streaming.py           # SSE format (DO NOT BREAK)
└── config.py                  # Settings (NEEDS SECURITY FIXES)
```

### Frontend Structure
```
frontend/
├── app/
│   └── api/chat/route.ts      # SSE client handler
├── components/
│   ├── chat-interface.tsx     # Main chat UI
│   └── agent-status-bar.tsx   # Connection status
└── [NO TEST FILES]            # Needs test infrastructure
```

## Agent Coordination History

### Review Agents Used
1. **code-reviewer**: Found duplication, configuration issues
2. **security-auditor**: Identified critical vulnerabilities
3. **architect-reviewer**: Found SOLID violations
4. **performance-engineer**: Found blocking operations
5. **test-automator**: Found zero frontend coverage

### Recommended Next Agents
1. **Security specialist**: Implement authentication system
2. **Performance engineer**: Implement connection pooling
3. **Test engineer**: Set up frontend testing
4. **Refactoring specialist**: Consolidate routers
5. **DevOps engineer**: Set up CI/CD pipeline

## SSE Format (CRITICAL - DO NOT CHANGE)
```
Text chunks: 0:"content"\n
Finish signal: d:{"finishReason":"stop"}\n
```
This format is required for Vercel AI SDK compatibility.

## Environment Variables Required
```env
# Security (MUST SET)
DEBUG=false
REQUIRE_API_KEY=true
API_KEY=your-secure-key

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-... (optional)

# External Services (optional)
TAVILY_API_KEY=...
FIRECRAWL_API_KEY=...
BRAVE_API_KEY=...
```

## Performance Targets
- Current: 800-1500ms response time
- Target: 300-600ms (50-60% improvement)
- Method: Connection pooling + async Redis + caching

## Testing Targets
- Current: 0% frontend, minimal backend
- Target: 80% unit, 70% integration
- Method: Jest + React Testing Library + pytest

## Security Checklist
- [ ] DEBUG=False in production
- [ ] Mandatory authentication enabled
- [ ] Input validation on all endpoints
- [ ] API keys removed from logs
- [ ] Debug endpoints disabled in production
- [ ] Security headers added
- [ ] Rate limiting enforced
- [ ] Session security implemented

## Quick Commands

### Run Backend
```bash
cd backend
python app_simple.py  # Port 8001
```

### Run Frontend
```bash
cd frontend
npm run dev  # Port 3000
```

### Run Tests
```bash
# Backend
cd backend
pytest tests/ -v

# Frontend (after setup)
cd frontend
npm test
```

## Notes for Context Updates

When updating context files:
1. Update version number and date
2. Keep sections organized
3. Include code examples where helpful
4. Cross-reference other context files
5. Update this index if adding new files

## Contact Points

- Main API: `POST /api/v1/agent-whisperer/chat/stream`
- Health check: `GET /health`
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8001`

---
*Use this index to quickly navigate the context files and find needed information*