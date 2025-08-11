/**
 * Performance Metrics Collection for v3 vs v5 Comparison
 * Tracks key metrics for migration decision making
 */

export interface PerformanceMetrics {
  // Timing metrics
  ttfb: number // Time to first byte
  ttfm: number // Time to first message
  streamingDuration: number // Total streaming time
  totalDuration: number // Total request duration
  
  // Message metrics
  messageCount: number
  totalBytes: number
  chunksReceived: number
  errorsCount: number
  
  // Protocol info
  sdkVersion: 'v3' | 'v5'
  protocol: 'legacy' | 'ui-message-stream'
  sessionId: string
  timestamp: number
}

export interface PerformanceComparison {
  v3: PerformanceStats
  v5: PerformanceStats
  improvement: {
    ttfb: number // Percentage
    ttfm: number
    streamingDuration: number
    throughput: number
  }
}

export interface PerformanceStats {
  sampleSize: number
  averages: {
    ttfb: number
    ttfm: number
    streamingDuration: number
    throughput: number // bytes per second
  }
  percentiles: {
    p50: Record<string, number>
    p95: Record<string, number>
    p99: Record<string, number>
  }
}

class PerformanceCollector {
  private metrics: Map<string, PerformanceMetrics> = new Map()
  private startTimes: Map<string, number> = new Map()
  private firstByteTimes: Map<string, number> = new Map()
  private chunkCounts: Map<string, number> = new Map()
  private byteCounts: Map<string, number> = new Map()

  /**
   * Start tracking a new request
   */
  startRequest(requestId: string, sessionId: string, sdkVersion: 'v3' | 'v5') {
    this.startTimes.set(requestId, performance.now())
    this.chunkCounts.set(requestId, 0)
    this.byteCounts.set(requestId, 0)
    
    this.metrics.set(requestId, {
      ttfb: 0,
      ttfm: 0,
      streamingDuration: 0,
      totalDuration: 0,
      messageCount: 0,
      totalBytes: 0,
      chunksReceived: 0,
      errorsCount: 0,
      sdkVersion,
      protocol: sdkVersion === 'v5' ? 'ui-message-stream' : 'legacy',
      sessionId,
      timestamp: Date.now()
    })
  }

  /**
   * Record first byte received
   */
  recordFirstByte(requestId: string) {
    const startTime = this.startTimes.get(requestId)
    if (!startTime) return

    const ttfb = performance.now() - startTime
    this.firstByteTimes.set(requestId, performance.now())
    
    const metrics = this.metrics.get(requestId)
    if (metrics) {
      metrics.ttfb = ttfb
    }
  }

  /**
   * Record first message received
   */
  recordFirstMessage(requestId: string) {
    const startTime = this.startTimes.get(requestId)
    if (!startTime) return

    const ttfm = performance.now() - startTime
    
    const metrics = this.metrics.get(requestId)
    if (metrics && metrics.ttfm === 0) {
      metrics.ttfm = ttfm
    }
  }

  /**
   * Record chunk received
   */
  recordChunk(requestId: string, bytes: number) {
    const chunks = this.chunkCounts.get(requestId) || 0
    const totalBytes = this.byteCounts.get(requestId) || 0
    
    this.chunkCounts.set(requestId, chunks + 1)
    this.byteCounts.set(requestId, totalBytes + bytes)
    
    const metrics = this.metrics.get(requestId)
    if (metrics) {
      metrics.chunksReceived = chunks + 1
      metrics.totalBytes = totalBytes + bytes
      metrics.messageCount++
    }
  }

  /**
   * Record error
   */
  recordError(requestId: string) {
    const metrics = this.metrics.get(requestId)
    if (metrics) {
      metrics.errorsCount++
    }
  }

  /**
   * Complete request tracking
   */
  completeRequest(requestId: string): PerformanceMetrics | null {
    const startTime = this.startTimes.get(requestId)
    const firstByteTime = this.firstByteTimes.get(requestId)
    const metrics = this.metrics.get(requestId)
    
    if (!startTime || !metrics) return null
    
    const now = performance.now()
    metrics.totalDuration = now - startTime
    
    if (firstByteTime) {
      metrics.streamingDuration = now - firstByteTime
    }
    
    // Clean up
    this.startTimes.delete(requestId)
    this.firstByteTimes.delete(requestId)
    this.chunkCounts.delete(requestId)
    this.byteCounts.delete(requestId)
    
    // Send to analytics in production
    this.reportMetrics(metrics)
    
    return metrics
  }

  /**
   * Report metrics to analytics service
   */
  private reportMetrics(metrics: PerformanceMetrics) {
    if (process.env.NODE_ENV === 'development') {
      console.log('[Performance Metrics]', {
        sdkVersion: metrics.sdkVersion,
        ttfb: `${metrics.ttfb.toFixed(2)}ms`,
        ttfm: `${metrics.ttfm.toFixed(2)}ms`,
        streaming: `${metrics.streamingDuration.toFixed(2)}ms`,
        total: `${metrics.totalDuration.toFixed(2)}ms`,
        throughput: `${(metrics.totalBytes / (metrics.streamingDuration / 1000)).toFixed(0)} B/s`,
        chunks: metrics.chunksReceived,
        errors: metrics.errorsCount
      })
    }

    // In production, send to analytics
    // Example: sendToAnalytics('streaming_performance', metrics)
    
    // Store in localStorage for local analysis
    this.storeLocally(metrics)
  }

  /**
   * Store metrics locally for analysis
   */
  private storeLocally(metrics: PerformanceMetrics) {
    try {
      const key = `perf_metrics_${metrics.sdkVersion}`
      const stored = localStorage.getItem(key)
      const existing = stored ? JSON.parse(stored) : []
      
      // Keep last 100 metrics
      const updated = [...existing, metrics].slice(-100)
      localStorage.setItem(key, JSON.stringify(updated))
    } catch (e) {
      // Ignore localStorage errors
    }
  }

  /**
   * Get comparison statistics
   */
  static getComparison(): PerformanceComparison | null {
    try {
      const v3Metrics = JSON.parse(localStorage.getItem('perf_metrics_v3') || '[]')
      const v5Metrics = JSON.parse(localStorage.getItem('perf_metrics_v5') || '[]')
      
      if (v3Metrics.length === 0 || v5Metrics.length === 0) {
        return null
      }
      
      const v3Stats = this.calculateStats(v3Metrics)
      const v5Stats = this.calculateStats(v5Metrics)
      
      return {
        v3: v3Stats,
        v5: v5Stats,
        improvement: {
          ttfb: ((v3Stats.averages.ttfb - v5Stats.averages.ttfb) / v3Stats.averages.ttfb) * 100,
          ttfm: ((v3Stats.averages.ttfm - v5Stats.averages.ttfm) / v3Stats.averages.ttfm) * 100,
          streamingDuration: ((v3Stats.averages.streamingDuration - v5Stats.averages.streamingDuration) / v3Stats.averages.streamingDuration) * 100,
          throughput: ((v5Stats.averages.throughput - v3Stats.averages.throughput) / v3Stats.averages.throughput) * 100
        }
      }
    } catch (e) {
      return null
    }
  }

  /**
   * Calculate statistics from metrics
   */
  private static calculateStats(metrics: PerformanceMetrics[]): PerformanceStats {
    const ttfbValues = metrics.map(m => m.ttfb).sort((a, b) => a - b)
    const ttfmValues = metrics.map(m => m.ttfm).sort((a, b) => a - b)
    const streamingValues = metrics.map(m => m.streamingDuration).sort((a, b) => a - b)
    const throughputValues = metrics.map(m => m.totalBytes / (m.streamingDuration / 1000)).sort((a, b) => a - b)
    
    const average = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length
    const percentile = (arr: number[], p: number) => arr[Math.floor(arr.length * p)]
    
    return {
      sampleSize: metrics.length,
      averages: {
        ttfb: average(ttfbValues),
        ttfm: average(ttfmValues),
        streamingDuration: average(streamingValues),
        throughput: average(throughputValues)
      },
      percentiles: {
        p50: {
          ttfb: percentile(ttfbValues, 0.5),
          ttfm: percentile(ttfmValues, 0.5),
          streamingDuration: percentile(streamingValues, 0.5),
          throughput: percentile(throughputValues, 0.5)
        },
        p95: {
          ttfb: percentile(ttfbValues, 0.95),
          ttfm: percentile(ttfmValues, 0.95),
          streamingDuration: percentile(streamingValues, 0.95),
          throughput: percentile(throughputValues, 0.95)
        },
        p99: {
          ttfb: percentile(ttfbValues, 0.99),
          ttfm: percentile(ttfmValues, 0.99),
          streamingDuration: percentile(streamingValues, 0.99),
          throughput: percentile(throughputValues, 0.99)
        }
      }
    }
  }
}

// Export singleton instance
export const performanceCollector = new PerformanceCollector()

// Export static comparison method
export const getPerformanceComparison = PerformanceCollector.getComparison