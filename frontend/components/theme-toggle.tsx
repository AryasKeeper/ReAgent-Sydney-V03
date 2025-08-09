'use client'

import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'

interface ThemeToggleProps {
  className?: string
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const [isDark, setIsDark] = useState<boolean>(false)
  const [isReady, setIsReady] = useState<boolean>(false)

  useEffect(() => {
    try {
      const stored = localStorage.getItem('reagent-theme')
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      const dark = stored ? stored === 'dark' : prefersDark
      setIsDark(dark)
      document.documentElement.classList.toggle('dark', dark)
    } finally {
      setIsReady(true)
    }
  }, [])

  const handleToggle = () => {
    const next = !isDark
    setIsDark(next)
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('reagent-theme', next ? 'dark' : 'light')
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className={`relative inline-flex items-center justify-center w-9 h-9 rounded-full border border-gray-200/70 dark:border-white/10 bg-white/70 dark:bg-white/5 backdrop-blur-sm shadow-sm hover:bg-white/90 dark:hover:bg-white/10 transition-colors ${className ?? ''}`}
    >
      <span className="absolute inset-0 rounded-full bg-gradient-to-br from-white/50 to-transparent dark:from-white/5 pointer-events-none" />
      {isReady && (
        isDark ? (
          <Moon className="w-4 h-4 text-white" />
        ) : (
          <Sun className="w-4 h-4 text-yellow-500" />
        )
      )}
    </button>
  )
}


