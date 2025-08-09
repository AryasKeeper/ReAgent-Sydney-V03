'use client'

import { useState } from 'react'
import { Copy, RotateCcw, Square } from 'lucide-react'

interface CopyButtonProps {
  text: string
}

export function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1200)
    } catch {}
  }
  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1 text-xs text-text-secondary dark:text-white/60 hover:text-text-primary dark:hover:text-white transition-colors"
      title={copied ? 'Copied' : 'Copy'}
    >
      <Copy className="w-3.5 h-3.5" /> {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

interface MessageActionsProps {
  onRegenerate?: () => void
  onStop?: () => void
  isLoading?: boolean
  contentForCopy: string
}

export function MessageActions({ onRegenerate, onStop, isLoading, contentForCopy }: MessageActionsProps) {
  return (
    <div className="mt-1 flex items-center gap-3">
      <CopyButton text={contentForCopy} />
      {onRegenerate && (
        <button
          onClick={onRegenerate}
          className="inline-flex items-center gap-1 text-xs text-text-secondary dark:text-white/60 hover:text-text-primary dark:hover:text-white transition-colors"
          title="Regenerate"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Regenerate
        </button>
      )}
      {isLoading && onStop && (
        <button
          onClick={onStop}
          className="inline-flex items-center gap-1 text-xs text-text-secondary dark:text-white/60 hover:text-text-primary dark:hover:text-white transition-colors"
          title="Stop"
        >
          <Square className="w-3.5 h-3.5" /> Stop
        </button>
      )}
    </div>
  )
}


