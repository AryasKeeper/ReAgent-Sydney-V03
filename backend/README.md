# ReAgent Backend V3

Clean, modular backend for Agent Whisperer MVP with proper SSE streaming for Vercel AI SDK compatibility.

## Features

- ✅ Correct SSE format for Vercel AI SDK v3.4.33
- ✅ No repetitive greetings (session tracking)
- ✅ Response variety for natural conversation
- ✅ Triple fallback for property search (Firecrawl → Tavily → Mock)
- ✅ Weather/time search via Tavily
- ✅ Claude/GPT intelligent routing
- ✅ CORS configured for localhost:3000, 3001, 3002

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the `.env` file from V2 (it has all the API keys):
```bash
cp ../reagent-sydney-v0.2/backend/.env .env
```

Or create a new `.env` file:
```env
DEBUG=true
USE_MOCK=false

# AI Model API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Web Search
TAVILY_API_KEY=your_tavily_key

# Property Search
FIRECRAWL_API_KEY=your_firecrawl_key
```

### 3. Run the Server

```bash
uvicorn app:app --reload --port 8000
```

Or directly with Python:
```bash
python app.py
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "service": "ReAgent Backend V3",
  "timestamp": "2024-01-09T10:00:00",
  "mode": "live",
  "models_available": {
    "openai": true,
    "anthropic": true,
    "tavily": true,
    "firecrawl": true
  }
}
```

### Chat Stream (SSE)
```bash
curl -X POST http://localhost:8000/api/v1/agent-whisperer/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the weather in Sydney?","session_id":"test"}'
```

Response format (SSE):
```
0:"The weather in Sydney is currently 22°C with partly cloudy skies."
d:{"finishReason":"stop"}
```

## SSE Format (CRITICAL)

This backend uses the exact format required by Vercel AI SDK:

- **Text chunks**: `0:"content"\n`
- **Finish signal**: `d:{"finishReason":"stop"}\n`

⚠️ **DO NOT** use `data:` prefix or `\n\n` terminators - they will break the frontend!

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DEBUG` | Enable debug mode | No | `true` |
| `USE_MOCK` | Use mock data instead of real APIs | No | `false` |
| `OPENAI_API_KEY` | OpenAI API key | Yes* | None |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Yes* | None |
| `TAVILY_API_KEY` | Tavily search API key | Yes* | None |
| `FIRECRAWL_API_KEY` | Firecrawl scraping API key | No | None |

*At least one AI key (OpenAI or Anthropic) is required

## Mock Mode

For testing without API keys:
```bash
USE_MOCK=true uvicorn app:app --reload
```

This will:
- Return mock AI responses
- Use sample property data
- Provide mock weather/time information

## Architecture

```
app.py              # FastAPI application with CORS
config.py           # Environment configuration
api/
  health.py         # Health check endpoint
  agent_whisperer.py # Main chat endpoint with SSE
services/
  ai_router.py      # Claude/GPT routing logic
  web_search.py     # Tavily integration for weather/time
  property_search.py # Triple fallback property search
  session_manager.py # Session tracking (no repetitive greetings)
  response_variety.py # Response templates for variety
utils/
  streaming.py      # SSE formatting (Vercel AI SDK compatible)
  logging.py        # Logging configuration
  mock_data.py      # Fallback mock property data
```

## Testing

### Basic Test
```python
pytest tests/
```

### Test SSE Format
```python
from utils.streaming import format_sse_chunk

# Should output: 0:"Hello"\n
print(format_sse_chunk("Hello"))

# Should output: d:{"finishReason":"stop"}\n
print(format_sse_chunk("", "finish"))
```

## Troubleshooting

### CORS Issues
- Ensure frontend is running on localhost:3000, 3001, or 3002
- Check CORS middleware in app.py

### SSE Not Working
- Verify format matches exactly: `0:"text"\n` not `data: text\n\n`
- Check network tab for streaming response

### No Properties Found
- Firecrawl may be blocked by anti-scraping
- Falls back to Tavily then mock data automatically
- Mock data always returns 5 properties

## Production Considerations

1. Add Redis for session management (currently in-memory)
2. Implement rate limiting per session
3. Add comprehensive error tracking
4. Use environment-specific configurations
5. Add database for property caching