# Frontend API Route

## POST /api/chat

- File: `frontend/app/api/chat/route.ts`
- Purpose: Proxies chat requests from the UI to the backend SSE endpoint and returns the streaming response unchanged.

Request Body (from `@ai-sdk/react`):
```json
{
  "messages": [
    { "id": "string", "role": "user|assistant|system", "content": "string" }
  ],
  "sessionId": "string"
}
```

Behavior:
- Extracts the last user message
- Forwards to backend `POST /api/v1/agent-whisperer/chat/stream`
- Returns `Content-Type: text/event-stream` response
- On error, returns SSE-formatted error and finish messages (status 200 to not break stream)

### Configuration

- Env var: `NEXT_PUBLIC_BACKEND_URL` (default `http://localhost:8001`)
  - Example `.env.local` in `frontend/`:
  ```env
  NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
  ```