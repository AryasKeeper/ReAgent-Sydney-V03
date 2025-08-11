'use client'

import { useAIChat } from '@/hooks/useAIChat'
import { Message, MessageContent } from '@/components/ai-elements/message'
import { Response } from '@/components/ai-elements/response'
import { ChatInput } from '@/components/ai-elements/input'
import { ReasoningPanel } from '@/components/ai-elements/reasoning'
import { MessageActions } from '@/components/ai-elements/actions'
import { PropertyCardsFromText } from '@/components/property/property-cards'
import { useState, useRef, useEffect } from 'react'
import { Send, ArrowLeft, Loader2 } from 'lucide-react'

interface ChatInterfaceProps {
  onBack?: () => void
}

export default function ChatInterface({ onBack }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [isInitialized, setIsInitialized] = useState(false)

  const chatProps = useAIChat({
    api: '/api/chat',
    initialMessages: [
      {
        id: 'welcome',
        role: 'assistant',
        content: `I'm ReAgent's intelligence system, analyzing Sydney's real estate market in real-time. 

I can help you with:
• Property valuations and market trends
• Investment opportunity analysis  
• Buyer-seller matching
• Off-market property discovery
• Neighborhood insights and demographics

What aspect of Sydney real estate would you like to explore?`
      }
    ],
    onResponse: (response) => {
      console.log('Response received:', response)
      setIsInitialized(true)
    },
    onError: (error) => {
      console.error('Chat error:', error)
    },
    onFinish: (message) => {
      console.log('Message finished:', message)
    }
  })

  const {
    messages = [],
    input = '',
    handleInputChange,
    handleSubmit,
    isLoading = false,
    error,
    setInput,
    stop,
    reload,
    setMessages
  } = chatProps

  // Debug logging
  useEffect(() => {
    console.log('Chat state:', { 
      messagesCount: messages.length, 
      isLoading, 
      hasError: !!error,
      inputLength: input.length 
    })
  }, [messages, isLoading, error, input])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleFormSubmit = (e: React.FormEvent) => {
    console.log('Form submitted with input:', input)
    handleSubmit(e)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim() && !isLoading) {
        console.log('Enter key pressed, submitting:', input)
        handleSubmit(e as any)
      }
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`
    }
  }, [input])

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-[#0B0C0E]">
      {/* Header */}
      <div className="border-b bg-white/95 dark:bg-black/30 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-4 px-6 py-4">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 hover:bg-surface rounded-lg transition-colors"
              aria-label="Back"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div className="flex-1">
            <h2 className="font-semibold">ReAgent Intelligence</h2>
            <p className="text-xs text-text-muted dark:text-white/60">Sydney Real Estate Analysis</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
          <ReasoningPanel isLoading={isLoading} />
          {messages.map((message) => (
            <Message from={message.role as 'user' | 'assistant'} key={message.id}>
              <MessageContent>
                {message.content.split('\n').map((text, i) => (
                  <Response key={`${message.id}-${i}`}>{text}</Response>
                ))}
                <PropertyCardsFromText text={message.content} />
              </MessageContent>
              {message.role === 'assistant' && (
                <MessageActions
                  contentForCopy={message.content}
                  isLoading={isLoading}
                  onStop={() => stop?.()}
                  onRegenerate={() => {
                    // Remove last assistant message and reload
                    const idx = messages.findIndex((m) => m.id === message.id)
                    if (idx !== -1) {
                      const next = [...messages]
                      next.splice(idx, 1)
                      setMessages?.(next)
                    }
                    reload?.()
                  }}
                />
              )}
            </Message>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-surface rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm text-text-secondary">Analyzing...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="flex justify-center">
              <div className="bg-red-50 text-red-600 rounded-lg px-4 py-2 text-sm">
                Connection error. Please try again.
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <ChatInput
        value={input}
        onChange={(v) => setInput(v)}
        onSubmit={() => handleSubmit(new Event('submit') as any)}
        isLoading={isLoading}
      />
    </div>
  )
}