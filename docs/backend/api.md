# Backend API

Base URL (local): `http://localhost:8000` (or `http://localhost:8001` when running `app_simple.py`).

## Health Check

- Method: `GET`
- Path: `/health`
- Description: Returns service status and available integrations.

Example:
```bash
curl http://localhost:8000/health | jq
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

## Chat Stream (SSE)

- Method: `POST`
- Path: `/api/v1/agent-whisperer/chat/stream`
- Description: Streams assistant responses as SSE-formatted text compatible with `@ai-sdk/react`.
- Headers:
  - `Content-Type: application/json`
- Request Body:
```json
{
  "message": "string",
  "session_id": "string",
  "messages": [
    { "role": "user|assistant|system", "content": "string" }
  ]
}
```

Example:
```bash
curl -N -X POST http://localhost:8000/api/v1/agent-whisperer/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find 3-bed houses under $2m in Marrickville",
    "session_id": "demo",
    "messages": []
  }'
```

### Streaming Format (Critical)

- Text chunk: `0:"<content>"\n`
- Finish signal: `d:{"finishReason":"stop"}\n`

Do not use `data:` or double newlines. See `utils/streaming.py` for formatter.

### Behavior by Query Type

The endpoint routes requests based on intent:
- Greeting: returns introduction/help
- Weather/Time: uses Tavily via `WebSearchService`
- Property Search: uses `PropertySearchService` (Firecrawl → Tavily → Mock)
- Property Analysis / General Chat / Web Search: streams from AI router

See `api/agent_whisperer.py` for full control flow.