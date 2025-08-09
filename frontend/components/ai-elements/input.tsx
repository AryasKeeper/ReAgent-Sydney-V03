'use client'

import { Loader2, Send } from 'lucide-react'

interface ChatInputProps {
  value: string
  onChange: (v: string) => void
  onSubmit: () => void
  isLoading?: boolean
}

export function ChatInput({ value, onChange, onSubmit, isLoading }: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (value.trim() && !isLoading) onSubmit()
    }
  }

  return (
    <div className="border-t bg-white dark:bg-[#0B0C0E]">
      <div className="max-w-3xl mx-auto px-6 py-4">
        <div className="flex gap-3">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Sydney properties, market trends, investment opportunities..."
            className="flex-1 px-4 py-3 bg-surface dark:bg-white/5 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-accent/20 transition-all min-h-[52px] max-h-32"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={() => !isLoading && value.trim() && onSubmit()}
            disabled={!value.trim() || isLoading}
            className="px-4 py-3 bg-accent text-white rounded-xl hover:bg-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}


