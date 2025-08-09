'use client'

import { ChevronDown, Loader2 } from 'lucide-react'
import { useState } from 'react'

interface ReasoningPanelProps {
  isLoading?: boolean
  initialOpen?: boolean
  title?: string
}

export function ReasoningPanel({ isLoading, initialOpen = false, title = 'Reasoning' }: ReasoningPanelProps) {
  const [open, setOpen] = useState(initialOpen)
  return (
    <div className="rounded-lg border bg-white/70 dark:bg-white/5 dark:border-white/10">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 text-sm text-text-secondary dark:text-white/70"
      >
        <span className="inline-flex items-center gap-2">
          {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          {title}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="px-3 pb-3 text-xs text-text-secondary dark:text-white/70">
          The assistant is thinking and planning the best way to answer. This section can display tool plans,
          selected sources, and intermediate steps.
        </div>
      )}
    </div>
  )}


