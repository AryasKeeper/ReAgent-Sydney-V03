'use client'

import type { PropsWithChildren, ReactNode } from 'react'
import { cn } from '../utils/cn'

export interface MessageProps extends PropsWithChildren {
  from: 'user' | 'assistant' | 'system'
  className?: string
}

export function Message({ from, className, children }: MessageProps) {
  const isUser = from === 'user'
  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start', className)}>
      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-4 py-3 shadow-sm',
          isUser
            ? 'bg-accent text-white'
            : 'bg-surface dark:bg-white/5 text-text-primary dark:text-white'
        )}
      >
        {children}
      </div>
    </div>
  )
}

export function MessageContent({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('prose prose-sm max-w-none dark:prose-invert', className)}>
      {children}
    </div>
  )
}


