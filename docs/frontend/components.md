# Frontend Components

## AgentStatusBar

- Path: `frontend/components/agent-status-bar.tsx`
- Props: none
- Description: Displays a minimal status bar of background agents and overall system state.

Usage:
```tsx
import AgentStatusBar from '@/components/agent-status-bar'

export default function Page() {
  return (
    <div>
      <AgentStatusBar />
    </div>
  )
}
```

## ChatInterface

- Path: `frontend/components/chat-interface.tsx`
- Props:
  - `onBack?: () => void`
- Description: Chat UI powered by `@ai-sdk/react` `useChat`, wired to `/api/chat`.

Usage:
```tsx
'use client'
import ChatInterface from '@/components/chat-interface'

export default function ChatPage() {
  return <ChatInterface onBack={() => history.back()} />
}
```

Behavior:
- Submits messages to `/api/chat`
- Auto-scrolls, shows loading and error states
- Enter to send, Shift+Enter for newline