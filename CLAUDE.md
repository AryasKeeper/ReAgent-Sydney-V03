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
# Backend requires .env file with:
OPENAI_API_KEY=sk-your-key
# Optional: ANTHROPIC_API_KEY, TAVILY_API_KEY, FIRECRAWL_API_KEY
```

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