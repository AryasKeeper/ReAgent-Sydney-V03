'use client'

import { memo, useMemo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { cn } from '@/components/utils/cn'

interface GridBackgroundProps {
  className?: string
  gridSize?: number // px
  gridOpacity?: number // 0..1
  beamsCount?: number
  beamsSpeed?: number // seconds across
  beamsOpacity?: number // 0..1
  colors?: {
    background?: string
    grid?: string
    beams?: string[]
  }
}

function rgba(hex: string, alpha: number): string {
  // accepts tailwind-like hex e.g. #0B0C0E or shorthand
  const h = hex.replace('#', '')
  const bigint = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16)
  const r = (bigint >> 16) & 255
  const g = (bigint >> 8) & 255
  const b = bigint & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

export const GridBackground = memo(function GridBackground(props: GridBackgroundProps) {
  const {
    className,
    gridSize = 48,
    gridOpacity = 0.08,
    beamsCount = 4,
    beamsSpeed = 18,
    beamsOpacity = 0.06,
    colors = {
      background: '#0B0C0E',
      grid: '#FFFFFF',
      beams: ['#60A5FA', '#22D3EE', '#818CF8'], // blue-400, cyan-400, indigo-400
    },
  } = props

  const reduceMotion = useReducedMotion()

  const backgroundStyle = useMemo(() => {
    const gridColor = rgba(colors.grid ?? '#FFFFFF', gridOpacity)
    return {
      backgroundColor: colors.background ?? '#0B0C0E',
      backgroundImage: `
        linear-gradient(to right, ${gridColor} 1px, transparent 1px),
        linear-gradient(to bottom, ${gridColor} 1px, transparent 1px)
      `,
      backgroundSize: `${gridSize}px ${gridSize}px`,
    } as React.CSSProperties
  }, [colors.background, colors.grid, gridOpacity, gridSize])

  const beams = useMemo(() => {
    const count = Math.max(0, beamsCount)
    return Array.from({ length: count }).map((_, i) => {
      const color = colors.beams?.[i % (colors.beams?.length || 1)] || '#60A5FA'
      const delay = (i * (beamsSpeed / count)) % beamsSpeed
      const translate = 120 // percentage over diagonal
      return { color, delay, translate }
    })
  }, [beamsCount, beamsSpeed, colors.beams])

  return (
    <div
      className={cn('pointer-events-none absolute inset-0 -z-10', className)}
      aria-hidden
    >
      <div className="absolute inset-0" style={backgroundStyle} />

      {/* Beams layer */}
      {!reduceMotion && (
        <div className="absolute inset-0 overflow-hidden">
          {beams.map((b, idx) => (
            <motion.div
              key={idx}
              className="absolute h-[220%] w-32 -left-16 top-[-60%] rotate-45 blur-2xl"
              style={{ backgroundColor: rgba(b.color, beamsOpacity) }}
              initial={{ x: '-20%' }}
              animate={{ x: `${b.translate}%` }}
              transition={{ duration: beamsSpeed, delay: b.delay, repeat: Infinity, ease: 'linear' }}
            />
          ))}
        </div>
      )}
    </div>
  )
})

export default GridBackground


