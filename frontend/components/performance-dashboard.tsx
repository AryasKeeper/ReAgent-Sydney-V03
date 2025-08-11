'use client'

import { useState, useEffect } from 'react'
import { getPerformanceComparison, type PerformanceComparison } from '@/lib/performance-metrics'
import { determineSDKVersion } from '@/lib/ab-testing'

export function PerformanceDashboard() {
  const [comparison, setComparison] = useState<PerformanceComparison | null>(null)
  const [currentVersion, setCurrentVersion] = useState<'v3' | 'v5'>('v3')
  const [isVisible, setIsVisible] = useState(false)
  
  useEffect(() => {
    // Only show in development or with debug flag
    const showDashboard = process.env.NODE_ENV === 'development' || 
                         localStorage.getItem('show_performance_dashboard') === 'true'
    setIsVisible(showDashboard)
    
    if (!showDashboard) return
    
    // Get current version
    const sessionId = sessionStorage.getItem('session_id') || 'default'
    const result = determineSDKVersion(sessionId)
    setCurrentVersion(result.version)
    
    // Update comparison data every 5 seconds
    const updateComparison = () => {
      const data = getPerformanceComparison()
      setComparison(data)
    }
    
    updateComparison()
    const interval = setInterval(updateComparison, 5000)
    
    return () => clearInterval(interval)
  }, [])
  
  if (!isVisible || !comparison) {
    return null
  }
  
  const formatMs = (ms: number) => `${ms.toFixed(1)}ms`
  const formatPercentage = (value: number) => {
    const formatted = value.toFixed(1)
    const prefix = value > 0 ? '+' : ''
    const color = value > 0 ? 'text-green-400' : value < 0 ? 'text-red-400' : 'text-gray-400'
    return <span className={color}>{prefix}{formatted}%</span>
  }
  
  return (
    <div className="fixed bottom-4 left-4 bg-black/90 text-white p-4 rounded-lg text-xs font-mono z-50 max-w-md">
      <div className="flex justify-between items-center mb-3">
        <div className="font-bold text-sm">Performance Comparison</div>
        <div className="flex items-center gap-2">
          <span className="text-gray-400">Current:</span>
          <span className={currentVersion === 'v5' ? 'text-green-400' : 'text-blue-400'}>
            {currentVersion.toUpperCase()}
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-4 gap-2 text-[10px]">
        <div className="text-gray-400">Metric</div>
        <div className="text-blue-400 text-center">v3</div>
        <div className="text-green-400 text-center">v5</div>
        <div className="text-gray-400 text-center">Δ</div>
        
        {/* TTFB */}
        <div>TTFB</div>
        <div className="text-center">{formatMs(comparison.v3.averages.ttfb)}</div>
        <div className="text-center">{formatMs(comparison.v5.averages.ttfb)}</div>
        <div className="text-center">{formatPercentage(comparison.improvement.ttfb)}</div>
        
        {/* TTFM */}
        <div>TTFM</div>
        <div className="text-center">{formatMs(comparison.v3.averages.ttfm)}</div>
        <div className="text-center">{formatMs(comparison.v5.averages.ttfm)}</div>
        <div className="text-center">{formatPercentage(comparison.improvement.ttfm)}</div>
        
        {/* Streaming */}
        <div>Stream</div>
        <div className="text-center">{formatMs(comparison.v3.averages.streamingDuration)}</div>
        <div className="text-center">{formatMs(comparison.v5.averages.streamingDuration)}</div>
        <div className="text-center">{formatPercentage(comparison.improvement.streamingDuration)}</div>
        
        {/* Throughput */}
        <div>T/put</div>
        <div className="text-center">{(comparison.v3.averages.throughput / 1024).toFixed(1)}KB/s</div>
        <div className="text-center">{(comparison.v5.averages.throughput / 1024).toFixed(1)}KB/s</div>
        <div className="text-center">{formatPercentage(comparison.improvement.throughput)}</div>
      </div>
      
      <div className="mt-3 pt-3 border-t border-white/20 grid grid-cols-2 gap-4 text-[10px]">
        <div>
          <div className="text-gray-400 mb-1">v3 Samples</div>
          <div className="text-blue-400">{comparison.v3.sampleSize}</div>
        </div>
        <div>
          <div className="text-gray-400 mb-1">v5 Samples</div>
          <div className="text-green-400">{comparison.v5.sampleSize}</div>
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t border-white/20 text-[10px]">
        <div className="text-gray-400 mb-1">P95 Latencies</div>
        <div className="grid grid-cols-3 gap-2">
          <div></div>
          <div className="text-blue-400 text-center">v3</div>
          <div className="text-green-400 text-center">v5</div>
          
          <div className="text-gray-400">TTFB</div>
          <div className="text-center">{formatMs(comparison.v3.percentiles.p95.ttfb)}</div>
          <div className="text-center">{formatMs(comparison.v5.percentiles.p95.ttfb)}</div>
          
          <div className="text-gray-400">TTFM</div>
          <div className="text-center">{formatMs(comparison.v3.percentiles.p95.ttfm)}</div>
          <div className="text-center">{formatMs(comparison.v5.percentiles.p95.ttfm)}</div>
        </div>
      </div>
      
      <div className="mt-3 text-[9px] text-gray-500">
        TTFB: Time to First Byte | TTFM: Time to First Message
        <br />
        Stream: Total streaming duration | T/put: Throughput
      </div>
    </div>
  )
}