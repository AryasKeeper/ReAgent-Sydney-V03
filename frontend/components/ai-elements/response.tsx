'use client'

import type { PropsWithChildren } from 'react'

export function Response({ children }: PropsWithChildren) {
  return <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
}


