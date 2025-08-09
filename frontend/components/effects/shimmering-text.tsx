'use client'

import { memo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { cn } from '@/components/utils/cn'

interface ShimmeringTextProps {
  text: string | React.ReactNode
  className?: string
  duration?: number
  delay?: number
  repeatDelay?: number
  shimmerColor?: string // CSS color
  spread?: number // px width of shimmer band
}

export const ShimmeringText = memo(function ShimmeringText({
  text,
  className,
  duration = 2.5,
  delay = 0,
  repeatDelay = 0.6,
  shimmerColor = 'rgba(96,165,250,0.35)', // blue-400 @ 35%
  spread = 120,
}: ShimmeringTextProps) {
  const reduceMotion = useReducedMotion()

  return (
    <span className={cn('relative inline-block overflow-hidden', className)}>
      {/* Content */}
      <span className="relative z-10">{text}</span>

      {/* Shimmer overlay */}
      {!reduceMotion && (
        <motion.span
          aria-hidden
          className="pointer-events-none absolute inset-y-0 -left-1/3 z-0"
          style={{
            width: `${spread}px`,
            background:
              `linear-gradient(90deg, transparent 0%, ${shimmerColor} 50%, transparent 100%)`,
            filter: 'blur(8px)',
            mixBlendMode: 'screen',
          }}
          initial={{ x: '-40%' }}
          animate={{ x: '140%' }}
          transition={{ duration, delay, repeat: Infinity, repeatDelay, ease: 'linear' }}
        />)
      }
    </span>
  )
})

export default ShimmeringText


