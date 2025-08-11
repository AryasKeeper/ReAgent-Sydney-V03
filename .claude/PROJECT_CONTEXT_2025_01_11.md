# ReAgent Sydney V03 - Project Context
**Generated**: 2025-01-11  
**Project Phase**: Week 3-4 (STORY 3 - Streaming Protocol Migration)

## Executive Summary
Real estate AI assistant for Sydney market undergoing 8-week systematic migration to modern development platform with AI SDK v5, AI Elements, and enterprise observability. Successfully pivoted from Vercel CLI to Dashboard+Git workflow due to npm corruption blocker.

## Project Overview

### Technology Stack
- **Backend**: FastAPI, Python 3.11, OpenAI GPT-4o-mini/GPT-5
- **Frontend**: Next.js 15, React, Tailwind CSS
  - Current: AI SDK v3.4.33
  - Target: AI SDK v5 (migration in progress)
- **Infrastructure**: 
  - Vercel deployment (Sydney region syd1)
  - SSE streaming architecture
  - Git-based deployment workflow

### Performance Targets
- Response time: <100ms
- Uptime: 99.9%
- Page load: <3s
- Sydney region latency: <50ms

## Migration Status

### ✅ COMPLETED (Weeks 1-2)
1. **Development Environment Standardization**
   - Successfully bypassed npm corruption blocker
   - Implemented Dashboard+Git workflow
   - Configured Vercel Sydney region deployment

2. **AI SDK v5 Transport Architecture**
   - Dual-protocol support (v3 legacy + v5 UI Message Stream)
   - Zero-downtime migration capability
   - Backward compatibility maintained

3. **Feature Flag System**
   - Environment variable: `NEXT_PUBLIC_AI_SDK_V5_ENABLED`
   - Progressive rollout control
   - Protocol auto-detection via headers

4. **Web Browsing Fix**
   - Fixed query classification for "live sources" and "up-to-date" queries
   - Proper routing to WEB_SEARCH type
   - Removed markdown formatting from responses

### 🔄 IN PROGRESS (Weeks 3-4)
**STORY 3: Streaming Protocol Migration**
- Production testing of dual-protocol support
- Progressive v5 rollout
- Performance validation

### 📅 UPCOMING (Weeks 5-8)
- **Week 5-6**: STORY 4 - AI Elements integration
- **Week 6-7**: STORY 5 - CLI-based release pipeline (pending npm fix)
- **Week 7-8**: STORY 6 - Enterprise observability with OpenTelemetry

## Technical Architecture

### SSE Streaming Protocols

#### v3 Format (Legacy)
```
0:"content here"\n
d:{"finishReason":"stop"}\n
```

#### v5 Format (UI Message Stream)
```
data: {"type":"text-delta","textDelta":"content"}\n\n
data: {"type":"finish","finishReason":"stop"}\n\n
```

### Protocol Detection
Backend automatically detects protocol via request headers:
- Header: `x-vercel-ai-ui-message-stream: v1` → v5 protocol
- No header → v3 protocol (default for backward compatibility)

### Query Classification System
Priority-based classification:
1. **Explicit Keywords**: Direct matches (e.g., "what time", "weather")
2. **Greeting Detection**: First interaction handling
3. **Domain-Specific**: Property, suburb, market analysis
4. **Implicit Patterns**: News, web search indicators
5. **General Fallback**: Default AI conversation

### Error Handling Strategy
Graceful fallback chain:
```
Firecrawl API → Tavily API → Mock Data → Error Message
```

### Session Management
- 30-minute timeout
- Prevents repetitive greetings
- Context preservation across interactions

## Key Files Structure

### Backend
```
backend/
├── app_simple.py              # Main FastAPI application
├── api/
│   └── agent_whisperer.py     # Chat endpoint with SSE streaming
├── services/
│   ├── ai_router_simple.py    # OpenAI GPT integration
│   ├── query_analyzer.py      # Query classification logic
│   └── session_manager.py     # User session handling
└── utils/
    └── streaming.py            # Dual-protocol SSE implementation
```

### Frontend
```
frontend/
├── app/
│   ├── api/chat/route.ts      # SSE endpoint handler
│   └── page.tsx                # Main application page
├── components/
│   ├── chat-interface.tsx     # Main chat UI
│   └── agent-status-bar.tsx   # Connection status display
└── hooks/
    └── useAIChat.ts            # v3/v5 protocol switching logic
```

### Configuration
```
.env.example                    # Comprehensive environment template
vercel.json                     # Sydney region configuration
```

## Critical Implementation Details

### API Endpoints
- **Chat**: `POST /api/v1/agent-whisperer/chat/stream`
- **Health**: `GET /health`

### CORS Configuration
- Allowed origins: localhost:3000, localhost:3001
- Backend port: 8001 (avoids conflicts)

### Environment Variables
```bash
# Backend (.env)
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-xxx  # Optional
TAVILY_API_KEY=xxx        # Optional
FIRECRAWL_API_KEY=xxx      # Optional

# Frontend (.env.local)
NEXT_PUBLIC_AI_SDK_V5_ENABLED=false  # Feature flag
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Testing Status
- ✅ 19 protocol switching test cases passing
- ✅ Backward compatibility verified
- ✅ Query classification accuracy validated
- ✅ Session management tested
- ⏳ Production load testing pending

## Known Issues & Blockers

### Resolved
- ✅ Web browsing classification fixed
- ✅ npm corruption bypassed via Dashboard+Git workflow
- ✅ Markdown formatting in responses removed

### Active
- ⚠️ npm installation blocked on Windows (ERR_INVALID_ARG_TYPE)
  - Workaround: Dashboard+Git workflow
  - Long-term: Awaiting npm fix for CLI restoration

## Agent Coordination History

1. **Initial Analysis Agent**: Fixed web browsing classification issues
2. **Migration Strategy Agent**: Analyzed Vercel CLI vs Raindrop MCP
3. **DevOps Validation Agent**: Confirmed approach, identified npm blocker
4. **Strategic Pivot Agent**: Successfully implemented Dashboard+Git workflow
5. **Implementation Agent**: Completed dual-protocol support

## Development Commands

### Backend
```bash
cd backend
python app_simple.py        # Start server (port 8001)
pytest tests/ -v            # Run tests
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm run dev                 # Development server (port 3000)
npm run dev:turbo          # With Turbopack
npm run build              # Production build
npm run lint               # Code linting
```

## Next Steps (Week 3-4 Focus)

1. **Production Testing**
   - Deploy v5 protocol to staging
   - Monitor performance metrics
   - Validate streaming stability

2. **Progressive Rollout**
   - Enable v5 for 10% of traffic
   - Monitor error rates
   - Gradually increase to 100%

3. **Performance Validation**
   - Measure latency improvements
   - Validate Sydney region optimization
   - Confirm <100ms response times

4. **Documentation Update**
   - Update API documentation
   - Create migration guide
   - Document rollback procedures

## Success Metrics
- Zero-downtime migration achieved
- Backward compatibility maintained
- All tests passing (19/19)
- Ready for progressive v5 rollout
- Development workflow unblocked

## Contact & Resources
- Project: ReAgent Sydney V03
- Region: Sydney (syd1)
- Stack: FastAPI + Next.js 15 + AI SDK
- Status: Week 3-4 Migration Phase

---
*This context document captures the complete project state for seamless agent handoff and continuation of the AI SDK v5 migration work.*