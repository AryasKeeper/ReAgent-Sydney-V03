import { NextRequest } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Extract the last user message
    const userMessage = body.messages?.[body.messages.length - 1]?.content || ''
    
    // Forward to backend streaming endpoint
    const response = await fetch(`${BACKEND_URL}/api/v1/agent-whisperer/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: userMessage,
        session_id: body.sessionId || 'default',
        messages: body.messages || []
      }),
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    // Return the streaming response directly
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (error) {
    console.error('Chat API error:', error)
    
    // Return error in SSE format
    const errorMessage = `0:"I'm having trouble connecting to the intelligence system. Please try again in a moment."\n`
    const finishMessage = `d:{"finishReason":"error"}\n`
    
    return new Response(errorMessage + finishMessage, {
      status: 200, // Keep 200 to not break the stream
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    })
  }
}