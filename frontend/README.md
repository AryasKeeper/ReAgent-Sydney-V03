# ReAgent Frontend (V3)

Next.js 15 + React 19 app using Vercel AI SDK and AI Elements style components.

## Dev

1. Create `.env.local` (or see `.env.local.example`):

```
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8001
```

2. Install and run:

```
npm install
npm run dev
```

The chat API proxy is at `app/api/chat/route.ts` and forwards to the backend SSE endpoint.


