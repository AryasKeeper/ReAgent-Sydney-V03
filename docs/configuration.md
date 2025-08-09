# Configuration

## Backend (`backend/config.py`)

Settings (with defaults):
- `DEBUG: bool = true`
- `USE_MOCK: bool = false`
- `OPENAI_API_KEY: Optional[str] = None`
- `ANTHROPIC_API_KEY: Optional[str] = None`
- `TAVILY_API_KEY: Optional[str] = None`
- `PERPLEXITY_API_KEY: Optional[str] = None`
- `FIRECRAWL_API_KEY: Optional[str] = None`
- `BACKEND_URL: str = "http://localhost:8000"`
- `SESSION_TIMEOUT_MINUTES: int = 30`
- `MAX_SESSIONS: int = 100`
- `MAX_REQUESTS_PER_MINUTE: int = 60`
- `ENABLE_VARIETY: bool = true`

Load behavior:
- Reads from `.env` (UTF-8), case sensitive, ignores extra keys

Example `.env`:
```env
DEBUG=true
USE_MOCK=false
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
TAVILY_API_KEY=...
FIRECRAWL_API_KEY=...
```

## Frontend

- `NEXT_PUBLIC_BACKEND_URL`: Backend base URL used by `app/api/chat/route.ts`
  - Example: `http://localhost:8000` (FastAPI default) or `http://localhost:8001` (when using `app_simple.py`)