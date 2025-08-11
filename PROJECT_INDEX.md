# ReAgent Sydney V03 - Project Index

## 📚 Project Overview

**ReAgent Sydney V03** is an AI-powered real estate intelligence platform for the Sydney market, featuring an advanced conversational AI assistant with real-time property analysis capabilities.

### Key Features
- 🤖 GPT-4 Turbo powered conversational AI
- 🏠 Sydney real estate market expertise
- ⚡ Real-time streaming responses (SSE)
- 🎨 Modern Next.js 15 interface
- 🔄 Intelligent query routing and analysis

---

## 🏗️ Architecture Overview

```
ReAgent-Sydney-V03/
├── backend/          # FastAPI backend server
├── frontend/         # Next.js 15 application
├── docs/            # Documentation
└── tests/           # Test suites
```

---

## 📁 Backend Structure

### Core Application Files
| File | Purpose |
|------|---------|
| `app_simple.py` | Main application entry point (port 8001) |
| `config.py` | Configuration and environment management |
| `requirements.txt` | Python dependencies |

### API Endpoints (`/api`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check and service status |
| `/api/v1/agent-whisperer/chat/stream` | POST | Main chat endpoint with SSE streaming |
| `/metrics` | GET | Service metrics and performance data |

### Service Layer (`/services`)

#### AI & Intelligence Services
| Service | Class/Function | Purpose |
|---------|----------------|---------|
| `ai_router.py` | `AIRouter` | Routes between OpenAI and Anthropic models |
| `ai_router_simple.py` | `SimpleAIRouter` | Simplified GPT-only routing |
| `query_analyzer.py` | `QueryAnalyzer` | Classifies and analyzes user queries |
| `agentic_browse.py` | `agentic_browse()` | Web browsing and content extraction |

#### Property & Search Services
| Service | Class/Function | Purpose |
|---------|----------------|---------|
| `property_search.py` | `PropertySearchService` | Property search with fallback strategies |
| `web_search.py` | `WebSearchService` | General web search integration |
| `search_brave.py` | `BraveSearchService` | Brave search API integration |
| `scrape_js.py` | `JSRenderer` | JavaScript rendering for web scraping |

#### System Services
| Service | Class/Function | Purpose |
|---------|----------------|---------|
| `session_manager.py` | `SessionManager` | User session management |
| `rate_limit.py` | `check_rate_limit()` | Rate limiting implementation |
| `redis_store.py` | `RedisStore` | Redis integration for caching |
| `metrics.py` | `Stopwatch`, `incr_counter()` | Performance monitoring |
| `response_variety.py` | Various | Response variation utilities |

### Utilities (`/utils`)
| Utility | Purpose |
|---------|---------|
| `streaming.py` | SSE format utilities for Vercel AI SDK |
| `logging.py` | Logging configuration |
| `mock_data.py` | Mock data for testing |

### Query Types Supported
- `GREETING` - User greetings and introductions
- `PROPERTY_SEARCH` - Property search queries
- `PROPERTY_ANALYSIS` - Market analysis and property insights
- `WEATHER` - Weather information requests
- `TIME` - Time and date queries
- `NEWS` - News and updates
- `WEB_SEARCH` - General web searches
- `GENERAL_CHAT` - General conversation

---

## 🎨 Frontend Structure

### Pages & Routes (`/app`)
| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | `page.tsx` | Landing page with hero section |
| `/api/chat` | `route.ts` | API route for chat proxy |

### Components (`/components`)

#### Core UI Components
| Component | Purpose |
|-----------|---------|
| `chat-interface.tsx` | Main chat interface with message handling |
| `agent-status-bar.tsx` | Status bar showing agent activity |
| `theme-toggle.tsx` | Dark/light theme switcher |

#### AI Elements (`/ai-elements`)
| Component | Purpose |
|-----------|---------|
| `message.tsx` | Message display component |
| `response.tsx` | AI response wrapper |
| `input.tsx` | Chat input field |
| `reasoning.tsx` | Reasoning panel for AI thinking |
| `actions.tsx` | Message action buttons (copy, regenerate) |

#### Property Components (`/property`)
| Component | Purpose |
|-----------|---------|
| `property-cards.tsx` | Property listing card display |

#### Effects (`/effects`)
| Component | Purpose |
|-----------|---------|
| `grid-background.tsx` | Animated grid background effect |

#### Utilities (`/utils`)
| Utility | Purpose |
|---------|---------|
| `cn.ts` | Class name utility for conditional styling |

---

## ⚙️ Configuration

### Environment Variables

#### Required
- `OPENAI_API_KEY` - OpenAI API key for GPT models

#### Optional
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude
- `TAVILY_API_KEY` - Tavily search API
- `FIRECRAWL_API_KEY` - Firecrawl web scraping
- `BRAVE_API_KEY` - Brave search API
- `BROWSERLESS_TOKEN` - Browserless rendering
- `REDIS_URL` - Redis connection URL

### Configuration Settings (`config.py`)
- `DEBUG` - Debug mode (default: True)
- `USE_MOCK` - Use mock data (default: False)
- `OPENAI_MODEL` - Primary OpenAI model
- `SESSION_TIMEOUT_MINUTES` - Session timeout (default: 30)
- `MAX_SESSIONS` - Maximum concurrent sessions (default: 100)
- `MAX_REQUESTS_PER_MINUTE` - Rate limit (default: 60)

---

## 🚀 Quick Start Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python app_simple.py  # Starts on port 8001
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # Starts on port 3000
```

### Testing
```bash
# Backend tests
cd backend
pytest tests/

# Specific test
pytest tests/test_health.py -v
```

---

## 📊 API Response Format

### SSE Stream Format
```
# Text chunk
0:"content text here"\n

# Finish signal
d:{"finishReason":"stop"}\n

# Error signal
d:{"finishReason":"error","error":"error message"}\n
```

### Chat Request Format
```json
{
  "message": "User message",
  "session_id": "unique-session-id",
  "messages": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ]
}
```

---

## 🔄 Data Flow

1. **User Input** → Frontend chat interface
2. **API Route** → Next.js `/api/chat` proxy
3. **Backend** → FastAPI `/api/v1/agent-whisperer/chat/stream`
4. **Query Analysis** → Classify query type
5. **Service Routing** → Route to appropriate service
6. **AI Processing** → Generate response
7. **SSE Stream** → Stream response to frontend
8. **UI Update** → Display in chat interface

---

## 📝 Development Notes

### Critical Files for Modifications
1. **Adding new query types**: `services/query_analyzer.py`
2. **Modifying AI behavior**: `services/ai_router_simple.py`
3. **Changing SSE format**: `utils/streaming.py`
4. **Adding API endpoints**: `api/agent_whisperer.py`
5. **Updating UI components**: `components/chat-interface.tsx`

### Common Tasks
- **Add new service**: Create in `/services`, import in relevant API endpoint
- **Modify chat flow**: Update `api/agent_whisperer.py` chat_stream function
- **Change UI styling**: Edit Tailwind classes in components
- **Add environment variable**: Update `config.py` Settings class

---

## 🐛 Debugging Tips

1. **Check SSE format**: Browser Network tab → look for `0:"text"\n` format
2. **Backend logs**: Check console output from `app_simple.py`
3. **Frontend console**: Check browser console for errors
4. **CORS issues**: Verify allowed origins in backend middleware
5. **API keys**: Ensure `.env` file has valid keys

---

## 📚 Additional Documentation

- [Backend README](./backend/README.md) - Backend specific details
- [Frontend README](./frontend/README.md) - Frontend specific details
- [Configuration Guide](./docs/configuration.md) - Detailed configuration
- [CLAUDE.md](./CLAUDE.md) - AI assistant guidance

---

## 🔗 Key Dependencies

### Backend
- FastAPI 0.115.5
- Uvicorn 0.32.1
- OpenAI 1.58.1
- Anthropic 0.40.0
- Pydantic 2.10.3

### Frontend
- Next.js 15.4.6
- React 19.1.1
- Vercel AI SDK 3.4.33
- Tailwind CSS 3.4.1
- Framer Motion 11.15.0

---

## 📈 Version History

- **v0.3.0** - First fully functional release (Current)
  - Production-ready MVP
  - Stable SSE streaming
  - Complete query routing
  - Session management

---

## 🎯 Project Status

**Current Phase**: Production-Ready MVP
**Development Time**: 25+ hours
**Stability**: Functional with known issues
**Next Steps**: Security hardening, database integration, real property data