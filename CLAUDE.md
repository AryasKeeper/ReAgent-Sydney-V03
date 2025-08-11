# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (FastAPI)
```bash
# Start backend server (port 8001)
cd backend
python app_simple.py

# Run tests
pytest tests/
pytest tests/test_health.py -v

# Install dependencies
pip install -r requirements.txt
```

### Frontend (Next.js 15)
```bash
# Start frontend dev server
cd frontend
npm run dev           # Port 3000
npm run dev:turbo    # With Turbopack

# Build and lint
npm run build
npm run lint

# Install dependencies
npm install
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env.local

# Backend requires .env file with:
OPENAI_API_KEY=sk-your-key
# Optional: ANTHROPIC_API_KEY, TAVILY_API_KEY, FIRECRAWL_API_KEY

# Frontend uses .env.local for development
# Production values configured in Vercel Dashboard
```

### Deployment Workflow (Dashboard + Git)

**Development to Production Flow**:
1. **Local Development**: Use `.env.local` for environment variables
2. **Git Push**: Push changes to GitHub repository
3. **Automatic Deployment**:
   - `main` branch → Production deployment
   - Feature branches → Preview deployments
4. **Environment Management**: Configure production secrets in Vercel Dashboard

**Vercel Dashboard Configuration**:
- Navigate to Project Settings → Environment Variables
- Add production API keys and configuration
- Sensitive values are encrypted and never exposed in code

**Rollback Procedure**:
1. Go to Vercel Dashboard → Deployments
2. Find previous stable deployment
3. Click "..." menu → "Promote to Production"
4. Instant rollback without code changes

## Architecture Overview

This is a Sydney real estate AI assistant with a FastAPI backend and Next.js frontend. The system uses Server-Sent Events (SSE) for streaming chat responses.

### Core Components

**Backend Service Architecture**:
- **AI Router** (`services/ai_router_simple.py`): OpenAI GPT integration with streaming support
- **Query Analyzer** (`services/query_analyzer.py`): Classifies queries into types (GREETING, PROPERTY_SEARCH, PROPERTY_ANALYSIS, WEATHER, TIME, NEWS, WEB_SEARCH, GENERAL)
- **Agent Whisperer API** (`api/agent_whisperer.py`): Main chat endpoint with SSE streaming
- **Session Manager** (`services/session_manager.py`): Manages user sessions with 30-minute timeout

**Frontend Architecture**:
- **Chat Interface** (`components/chat-interface.tsx`): Main chat UI with streaming message support
- **Agent Status Bar** (`components/agent-status-bar.tsx`): Shows connection status and agent activity
- **SSE Integration** (`app/api/chat/route.ts`): Handles SSE streaming from backend

### Critical Implementation Details

**SSE Format** (MUST maintain for Vercel AI SDK compatibility):
- Text chunks: `0:"content"\n`
- Finish signal: `d:{"finishReason":"stop"}\n`
- Implementation in `utils/streaming.py`

**API Endpoints**:
- Chat: `POST /api/v1/agent-whisperer/chat/stream`
- Health: `GET /health`

**CORS Configuration**:
- Allowed origins: localhost:3000, 3001
- Backend runs on port 8001 to avoid conflicts

### Key Design Patterns

1. **Query Routing**: Queries are analyzed and routed to appropriate handlers based on type
2. **Fallback Strategy**: Multiple fallbacks for external services (Firecrawl → Tavily → Mock data)
3. **Session Management**: Prevents repetitive greetings while maintaining context
4. **Streaming Architecture**: Async generators for memory-efficient streaming

### Common Development Tasks

**Adding Query Types**:
1. Update `QueryType` enum in `services/query_analyzer.py`
2. Add detection logic in `analyze_query()` method
3. Add handler in `api/agent_whisperer.py` chat_stream function

**Modifying AI Behavior**:
- Edit system prompt in `services/ai_router_simple.py`
- Adjust temperature and max_tokens for response characteristics

**Debugging Streaming Issues**:
- Check browser Network tab for SSE response format
- Verify format matches: `0:"text"\n`
- Check CORS headers are present
- Review `utils/streaming.py` for format issues

## Migration Status (AI SDK v5 & AI Elements)

### Current State
- **AI SDK**: v3.4.33 (stable) with v5 support available via feature flag
- **SSE Protocol**: Dual protocol support - v3 format (`0:"content"\n`) and v5 UI Message Stream
- **UI Components**: Custom AI Elements-style components

### Completed Migration Components
1. ✅ **Dual Protocol Support**: Backend detects and handles both v3 and v5 protocols automatically
2. ✅ **Transport Architecture**: Frontend v5 implementation with UI Message Stream support
3. ✅ **Protocol Detection**: Automatic detection via `x-vercel-ai-ui-message-stream: v1` header
4. ✅ **Feature Flag System**: Progressive rollout control via environment variables

### Migration Path (In Progress)
1. **AI SDK v5**: Transport-based architecture (✅ implemented, behind feature flag)
2. **UI Message Stream Protocol**: New SSE format (✅ backend support, ✅ frontend support)
3. **Official AI Elements**: Replace custom components incrementally (⏳ pending)

### Feature Flags
Control migration rollout via environment variables:
```bash
# Enable AI SDK v5 (default: false)
NEXT_PUBLIC_AI_SDK_V5_ENABLED=true

# Enable UI Message Stream Protocol (default: false)
NEXT_PUBLIC_UI_MESSAGE_STREAM_ENABLED=true

# Enable official AI Elements (default: false)
NEXT_PUBLIC_AI_ELEMENTS_ENABLED=true
```

### Sydney Region Optimization
- Functions deployed to `syd1` region for optimal performance
- Configuration in `vercel.json`
- Reduces latency for Australian users