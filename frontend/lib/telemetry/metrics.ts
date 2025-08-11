/**
 * Custom Metrics Collection for Frontend
 * Tracks AI SDK, streaming, and user interaction metrics
 */

import { Counter, Histogram, UpDownCounter, ObservableGauge, Meter } from '@opentelemetry/api'
import telemetryService from './setup'

export interface MetricAttributes {
  [key: string]: string | number | boolean
}

export class ApplicationMetrics {
  private static instance: ApplicationMetrics
  private meter: Meter
  
  // Counters
  private aiRequestCounter!: Counter
  private chatMessageCounter!: Counter
  private errorCounter!: Counter
  private migrationAttemptCounter!: Counter
  private featureFlagChangeCounter!: Counter
  
  // Histograms
  private streamingDurationHistogram!: Histogram
  private ttfbHistogram!: Histogram
  private ttfmHistogram!: Histogram
  private messageLatencyHistogram!: Histogram
  private renderTimeHistogram!: Histogram
  
  // UpDownCounters
  private activeSessionsCounter!: UpDownCounter
  private activeStreamingCounter!: UpDownCounter
  
  // Gauges
  private memoryUsageGauge!: ObservableGauge
  private tokenUsageGauge!: ObservableGauge

  private constructor() {
    this.meter = telemetryService.getMeter('reagent-metrics')
    this.initializeMetrics()
  }

  static getInstance(): ApplicationMetrics {
    if (!ApplicationMetrics.instance) {
      ApplicationMetrics.instance = new ApplicationMetrics()
    }
    return ApplicationMetrics.instance
  }

  private initializeMetrics(): void {
    // Initialize Counters
    this.aiRequestCounter = this.meter.createCounter('ai.requests', {
      description: 'Total number of AI requests',
      unit: 'requests',
    })

    this.chatMessageCounter = this.meter.createCounter('chat.messages', {
      description: 'Total number of chat messages sent',
      unit: 'messages',
    })

    this.errorCounter = this.meter.createCounter('app.errors', {
      description: 'Total number of application errors',
      unit: 'errors',
    })

    this.migrationAttemptCounter = this.meter.createCounter('migration.attempts', {
      description: 'Number of SDK migration attempts',
      unit: 'attempts',
    })

    this.featureFlagChangeCounter = this.meter.createCounter('feature.flag.changes', {
      description: 'Number of feature flag changes',
      unit: 'changes',
    })

    // Initialize Histograms
    this.streamingDurationHistogram = this.meter.createHistogram('streaming.duration', {
      description: 'Duration of SSE streaming sessions',
      unit: 'ms',
    })

    this.ttfbHistogram = this.meter.createHistogram('http.ttfb', {
      description: 'Time to first byte for HTTP requests',
      unit: 'ms',
    })

    this.ttfmHistogram = this.meter.createHistogram('streaming.ttfm', {
      description: 'Time to first message in streaming',
      unit: 'ms',
    })

    this.messageLatencyHistogram = this.meter.createHistogram('message.latency', {
      description: 'End-to-end message processing latency',
      unit: 'ms',
    })

    this.renderTimeHistogram = this.meter.createHistogram('component.render.time', {
      description: 'Component render time',
      unit: 'ms',
    })

    // Initialize UpDownCounters
    this.activeSessionsCounter = this.meter.createUpDownCounter('sessions.active', {
      description: 'Number of active user sessions',
      unit: 'sessions',
    })

    this.activeStreamingCounter = this.meter.createUpDownCounter('streaming.active', {
      description: 'Number of active streaming connections',
      unit: 'connections',
    })

    // Initialize Observable Gauges
    this.memoryUsageGauge = this.meter.createObservableGauge('browser.memory.usage', {
      description: 'Browser memory usage',
      unit: 'bytes',
    })

    this.tokenUsageGauge = this.meter.createObservableGauge('ai.tokens.usage', {
      description: 'AI token usage',
      unit: 'tokens',
    })

    // Set up observable callbacks
    this.setupObservableCallbacks()
  }

  private setupObservableCallbacks(): void {
    // Memory usage callback
    this.memoryUsageGauge.addCallback((observableResult) => {
      if ('memory' in performance) {
        const memory = (performance as any).memory
        observableResult.observe(memory.usedJSHeapSize, {
          type: 'heap',
        })
        observableResult.observe(memory.totalJSHeapSize, {
          type: 'total',
        })
      }
    })

    // Token usage callback (would be updated from actual usage)
    let currentTokenUsage = 0
    this.tokenUsageGauge.addCallback((observableResult) => {
      observableResult.observe(currentTokenUsage, {
        model: 'gpt-4',
      })
    })
  }

  // AI Request Metrics
  recordAIRequest(attributes: {
    provider: string
    model: string
    sdkVersion: string
    success: boolean
    streaming: boolean
  }): void {
    this.aiRequestCounter.add(1, attributes)
  }

  // Chat Message Metrics
  recordChatMessage(attributes: {
    role: 'user' | 'assistant'
    sessionId: string
    sdkVersion: string
  }): void {
    this.chatMessageCounter.add(1, attributes)
  }

  // Error Metrics
  recordError(attributes: {
    type: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    component: string
    sdkVersion?: string
  }): void {
    this.errorCounter.add(1, attributes)
  }

  // Migration Metrics
  recordMigrationAttempt(attributes: {
    fromVersion: string
    toVersion: string
    component: string
    success: boolean
  }): void {
    this.migrationAttemptCounter.add(1, attributes)
  }

  // Feature Flag Metrics
  recordFeatureFlagChange(attributes: {
    flag: string
    oldValue: string | boolean
    newValue: string | boolean
  }): void {
    this.featureFlagChangeCounter.add(1, attributes)
  }

  // Streaming Metrics
  recordStreamingDuration(duration: number, attributes: {
    sdkVersion: string
    protocol: string
    success: boolean
  }): void {
    this.streamingDurationHistogram.record(duration, attributes)
  }

  recordTTFB(duration: number, attributes: {
    endpoint: string
    method: string
    status: number
  }): void {
    this.ttfbHistogram.record(duration, attributes)
  }

  recordTTFM(duration: number, attributes: {
    sdkVersion: string
    protocol: string
  }): void {
    this.ttfmHistogram.record(duration, attributes)
  }

  recordMessageLatency(duration: number, attributes: {
    messageType: string
    sdkVersion: string
  }): void {
    this.messageLatencyHistogram.record(duration, attributes)
  }

  recordComponentRenderTime(duration: number, attributes: {
    component: string
    variant?: string
  }): void {
    this.renderTimeHistogram.record(duration, attributes)
  }

  // Session Metrics
  incrementActiveSessions(attributes: {
    userId?: string
    region?: string
  }): void {
    this.activeSessionsCounter.add(1, attributes)
  }

  decrementActiveSessions(attributes: {
    userId?: string
    region?: string
  }): void {
    this.activeSessionsCounter.add(-1, attributes)
  }

  // Streaming Connection Metrics
  incrementActiveStreaming(attributes: {
    sdkVersion: string
    protocol: string
  }): void {
    this.activeStreamingCounter.add(1, attributes)
  }

  decrementActiveStreaming(attributes: {
    sdkVersion: string
    protocol: string
  }): void {
    this.activeStreamingCounter.add(-1, attributes)
  }

  // Utility method to measure async operations
  async measureAsyncOperation<T>(
    operation: () => Promise<T>,
    metricName: 'ttfb' | 'ttfm' | 'streaming' | 'message' | 'render',
    attributes: MetricAttributes
  ): Promise<T> {
    const startTime = performance.now()
    
    try {
      const result = await operation()
      const duration = performance.now() - startTime
      
      // Record the appropriate metric
      switch (metricName) {
        case 'ttfb':
          this.recordTTFB(duration, attributes as any)
          break
        case 'ttfm':
          this.recordTTFM(duration, attributes as any)
          break
        case 'streaming':
          this.recordStreamingDuration(duration, attributes as any)
          break
        case 'message':
          this.recordMessageLatency(duration, attributes as any)
          break
        case 'render':
          this.recordComponentRenderTime(duration, attributes as any)
          break
      }
      
      return result
    } catch (error) {
      const duration = performance.now() - startTime
      
      // Record error and duration
      this.recordError({
        type: error instanceof Error ? error.name : 'unknown',
        severity: 'high',
        component: metricName,
        ...attributes,
      })
      
      throw error
    }
  }
}

// Export singleton instance
export const metrics = ApplicationMetrics.getInstance()

// React hook for component render time measurement
export function useRenderMetrics(componentName: string, variant?: string) {
  if (typeof window !== 'undefined') {\n    const startTime = performance.now()
    
    // Use useEffect to measure after render
    if ('useEffect' in require('react')) {\n      const { useEffect } = require('react')
      useEffect(() => {
        const renderTime = performance.now() - startTime
        metrics.recordComponentRenderTime(renderTime, {
          component: componentName,
          variant,
        })
      })
    }
  }
}

// Utility function to track feature flag changes
export function trackFeatureFlagChange(
  flagName: string,
  oldValue: string | boolean,
  newValue: string | boolean
): void {
  metrics.recordFeatureFlagChange({
    flag: flagName,
    oldValue,
    newValue,
  })
}

// Export types for external use
export type { Meter, Counter, Histogram, UpDownCounter, ObservableGauge } from '@opentelemetry/api'