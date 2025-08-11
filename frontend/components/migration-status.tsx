'use client'

import { useEffect, useState } from 'react'
import { getAISDKVersion } from '@/hooks/useAIChat'

export function MigrationStatus() {
  const [version, setVersion] = useState<string>('')
  const [features, setFeatures] = useState({
    aiSDKv5: false,
    uiMessageStream: false,
    aiElements: false
  })
  
  useEffect(() => {
    // Only show in development
    if (process.env.NODE_ENV !== 'development') return
    
    setVersion(getAISDKVersion())
    setFeatures({
      aiSDKv5: process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED === 'true',
      uiMessageStream: process.env.NEXT_PUBLIC_UI_MESSAGE_STREAM_ENABLED === 'true',
      aiElements: process.env.NEXT_PUBLIC_AI_ELEMENTS_ENABLED === 'true'
    })
  }, [])
  
  // Don't render in production
  if (process.env.NODE_ENV !== 'development') {
    return null
  }
  
  return (
    <div className="fixed bottom-4 right-4 bg-black/80 text-white p-3 rounded-lg text-xs font-mono z-50 max-w-xs">
      <div className="font-bold mb-2">Migration Status</div>
      <div className="space-y-1">
        <div className="flex justify-between">
          <span>AI SDK:</span>
          <span className={features.aiSDKv5 ? 'text-green-400' : 'text-gray-400'}>
            {version}
          </span>
        </div>
        <div className="flex justify-between">
          <span>UI Stream:</span>
          <span className={features.uiMessageStream ? 'text-green-400' : 'text-gray-400'}>
            {features.uiMessageStream ? 'v1' : 'legacy'}
          </span>
        </div>
        <div className="flex justify-between">
          <span>AI Elements:</span>
          <span className={features.aiElements ? 'text-green-400' : 'text-gray-400'}>
            {features.aiElements ? 'official' : 'custom'}
          </span>
        </div>
      </div>
      <div className="mt-2 pt-2 border-t border-white/20 text-[10px] text-gray-400">
        Sydney Region: syd1
      </div>
    </div>
  )
}