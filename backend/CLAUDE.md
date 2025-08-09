# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start the backend server (default port 8000)
python app.py

# Alternative: start with uvicorn directly
uvicorn app:app --reload --port 8000

# Windows: Use batch script
start_backend.bat
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v

# Run async tests
pytest tests/test_streaming.py -v
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file from template (copy from ../reagent-sydney-v0.2/backend/.env)
cp ../reagent-sydney-v0.2/backend/.env .env
```

## Architecture Overview

This is a FastAPI-based backend for the ReAgent real estate AI assistant. The system uses SSE (Server-Sent Events) streaming for real-time chat responses, compatible with Vercel AI SDK v3.4.33.

### Core Services Architecture

**AI Router (`services/ai_router.py`)**
- Routes between OpenAI (GPT-4o-mini/GPT-5) and Anthropic (Claude) based on query complexity
- Supports OpenAI Responses API for GPT-5 with reasoning_effort and verbosity parameters
- Falls back gracefully when API keys are missing

**Query Analyzer (`services/query_analyzer.py`)**
- Classifies queries into types: GREETING, PROPERTY_SEARCH, PROPERTY_ANALYSIS, WEATHER, TIME, NEWS, WEB_SEARCH, GENERAL
- Extracts parameters from natural language queries
- Determines routing strategy for each query type

**Property Search (`services/property_search.py`)**
- Triple fallback strategy: Firecrawl → Tavily → Mock data
- Handles anti-scraping measures gracefully
- Returns structured property listings

**Session Management (`services/session_manager.py`)**
- In-memory session tracking (consider Redis for production)
- Prevents repetitive greetings per session
- 30-minute timeout, max 100 concurrent sessions

### SSE Streaming Format

**CRITICAL**: The backend uses a specific SSE format for Vercel AI SDK compatibility:
- Text chunks: `0:"content"\n`
- Finish signal: `d:{"finishReason":"stop"}\n`
- DO NOT use `data:` prefix or `\n\n` terminators

Implementation in `utils/streaming.py`:
```python
def format_sse_chunk(content: str, chunk_type: str = "text") -> str:
    if chunk_type == "finish":
        return 'data: {"finishReason":"stop"}\n\n'
    return f'0:"{content}"\n'
```

### API Endpoint Structure

**Main Chat Endpoint**: `POST /api/v1/agent-whisperer/chat/stream`
- Accepts: `{message: str, session_id: str, messages: List[ChatMessage]}`
- Returns: SSE stream with formatted chunks
- Handles query routing based on type

**Health Check**: `GET /health`
- Returns service status and available models

### Configuration Management

All settings in `config.py` via environment variables:
- `DEBUG`: Enable debug mode and API docs
- `USE_MOCK`: Use mock data instead of real APIs
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`: AI model keys
- `OPENAI_USE_RESPONSES`: Enable GPT-5 Responses API path
- `OPENAI_REASONING_EFFORT`: Control GPT-5 reasoning depth
- `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `BRAVE_API_KEY`: Search/scraping services

### CORS Configuration

Configured for local development:
- Allowed origins: localhost:3000, 3001, 3002
- Credentials: true
- Methods/Headers: all allowed

### Key Design Decisions

1. **Streaming Architecture**: Uses async generators for memory-efficient streaming
2. **Service Layer Pattern**: Clean separation between API routes and business logic
3. **Fallback Strategy**: Multiple fallbacks for external services to ensure reliability
4. **Session Tracking**: Prevents repetitive interactions while maintaining context
5. **Query Classification**: Smart routing based on query intent rather than keywords alone

### Common Development Tasks

**Adding a New Query Type**:
1. Add enum value to `QueryType` in `services/query_analyzer.py`
2. Update `analyze_query()` method with detection logic
3. Add handler in `api/agent_whisperer.py` chat_stream function
4. Update `_llm_prefs_for()` if specific AI settings needed

**Modifying SSE Format**:
- Only edit `utils/streaming.py:format_sse_chunk()`
- Test with frontend to ensure compatibility

**Adding New AI Model**:
- Update `services/ai_router.py` with new client initialization
- Add API key to `config.py` Settings class
- Implement streaming method following existing patterns

**Debugging Streaming Issues**:
1. Check browser Network tab for SSE response
2. Verify format matches exactly: `0:"text"\n`
3. Ensure CORS headers are present
4. Check `utils/streaming.py` for format issues

### Testing Approach

- Unit tests in `tests/` directory
- Use `pytest-asyncio` for async endpoint testing
- Mock external services when testing business logic
- Test SSE format compliance separately