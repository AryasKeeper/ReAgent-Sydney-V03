'use client'

import { useChat as useAIChatV3 } from '@ai-sdk/react'
import { useState, useCallback, useRef, useEffect } from 'react'
import type { Message } from 'ai'
import { performanceCollector } from '@/lib/performance-metrics'

// Dev mode: Just use v5 directly (no A/B testing complexity)
const isV5Enabled = () => {
  return process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED === 'true'
}

// V5 Transport-based implementation with UI Message Stream protocol
function useAIChatV5(options: any) {
  const [messages, setMessages] = useState<Message[]>(options.initialMessages || [])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | undefined>()
  
  // Transport configuration for v5
  const transportRef = useRef<AbortController | null>(null)
  
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement> | string) => {
    const value = typeof e === 'string' ? e : e.target.value
    setInput(value)
  }, [])
  
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault()
    
    if (!input.trim() || isLoading) return
    
    setIsLoading(true)
    setError(undefined)
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput('')
    
    // Start performance tracking
    const requestId = `req_${Date.now()}`
    const sessionId = sessionStorage.getItem('session_id') || 'default'
    performanceCollector.startRequest(requestId, sessionId, 'v5')
    
    try {
      // V5 Transport implementation with UI Message Stream protocol
      transportRef.current = new AbortController()
      
      // Simple dev mode - no A/B testing
      const response = await fetch(options.api || '/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          sessionId: options.sessionId || sessionId
        }),
        signal: transportRef.current.signal
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      // Record first byte
      performanceCollector.recordFirstByte(requestId)
      
      // Handle v5 UI Message Stream format
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      let assistantMessage: Message | null = null
      let currentMessageId: string | null = null
      let firstMessageRecorded = false
      
      if (reader) {
        let buffer = ''
        
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value, { stream: true })
          performanceCollector.recordChunk(requestId, chunk.length)
          buffer += chunk
          const lines = buffer.split('\n')
          
          // Keep the last incomplete line in buffer
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data === '[DONE]') continue
              
              try {
                const message = JSON.parse(data)
                
                switch (message.type) {
                  case 'message-start':
                    // Start of a new assistant message
                    currentMessageId = message.id || Date.now().toString()
                    assistantMessage = {
                      id: currentMessageId,
                      role: 'assistant',
                      content: ''
                    }
                    setMessages(prev => [...prev, assistantMessage!])
                    break
                    
                  case 'text-delta':
                    // Incremental text content
                    if (assistantMessage) {
                      if (!firstMessageRecorded) {
                        performanceCollector.recordFirstMessage(requestId)
                        firstMessageRecorded = true
                      }
                      assistantMessage.content += message.textDelta || ''
                      setMessages(prev => {
                        const newMessages = [...prev]
                        newMessages[newMessages.length - 1] = { ...assistantMessage! }
                        return newMessages
                      })
                    }
                    break
                    
                  case 'tool-result':
                    // Tool results (e.g., web search sources)
                    if (message.toolName === 'web_search' && assistantMessage) {
                      // Could append sources to message metadata if needed
                      console.log('Web search sources:', message.result)
                    }
                    break
                    
                  case 'finish':
                    // Stream completion
                    if (assistantMessage) {
                      options.onFinish?.(assistantMessage)
                    }
                    break
                    
                  case 'error':
                    // Error in stream
                    performanceCollector.recordError(requestId)
                    const streamError = new Error(message.error?.message || 'Stream error')
                    setError(streamError)
                    options.onError?.(streamError)
                    break
                }
              } catch (parseError) {
                console.error('Failed to parse v5 message:', parseError, data)
              }
            } else if (line.startsWith('0:')) {
              // Fallback to v3 format if backend sends it
              try {
                const content = JSON.parse(line.slice(2))
                if (!assistantMessage) {
                  assistantMessage = {
                    id: Date.now().toString(),
                    role: 'assistant',
                    content: ''
                  }
                  setMessages(prev => [...prev, assistantMessage!])
                }
                assistantMessage.content += content
                setMessages(prev => {
                  const newMessages = [...prev]
                  newMessages[newMessages.length - 1] = { ...assistantMessage! }
                  return newMessages
                })
              } catch (parseError) {
                console.error('Failed to parse v3 message:', parseError)
              }
            }
          }
        }
        
        // Process any remaining buffer
        if (buffer.trim()) {
          console.warn('Unprocessed buffer:', buffer)
        }
      }
      
      if (assistantMessage) {
        options.onFinish?.(assistantMessage)
      }
      
      // Complete performance tracking
      const metrics = performanceCollector.completeRequest(requestId)
      if (metrics && process.env.NODE_ENV === 'development') {
        console.log('[V5 Performance]', metrics)
      }
    } catch (err: any) {
      performanceCollector.recordError(requestId)
      performanceCollector.completeRequest(requestId)
      
      if (err.name !== 'AbortError') {
        setError(err)
        options.onError?.(err)
      }
    } finally {
      setIsLoading(false)
      transportRef.current = null
    }
  }, [input, isLoading, messages, options])
  
  const stop = useCallback(() => {
    if (transportRef.current) {
      transportRef.current.abort()
      setIsLoading(false)
    }
  }, [])
  
  const reload = useCallback(async () => {
    if (messages.length < 2) return
    
    // Remove last assistant message and resend
    const newMessages = messages.slice(0, -1)
    setMessages(newMessages)
    
    // Resend last user message
    const lastUserMessage = newMessages[newMessages.length - 1]
    if (lastUserMessage?.role === 'user') {
      setInput(lastUserMessage.content)
      await handleSubmit()
    }
  }, [messages, handleSubmit])
  
  return {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    setInput,
    stop,
    reload,
    setMessages
  }
}

// Unified hook that switches between v3 and v5
export function useAIChat(options: Parameters<typeof useAIChatV3>[0]) {
  const v5Enabled = isV5Enabled()
  
  // Log migration status (development only)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[AI SDK Migration] Using ${v5Enabled ? 'v5 (transport-based)' : 'v3 (stable)'} implementation`)
    }
  }, [v5Enabled])
  
  // Use appropriate version based on feature flag
  if (v5Enabled) {
    return useAIChatV5(options)
  }
  
  return useAIChatV3(options)
}

// Export migration status helper
export function getAISDKVersion() {
  return isV5Enabled() ? '5.0.0-migration' : '3.4.33'
}