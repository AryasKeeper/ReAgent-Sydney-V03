/**
 * Gradual Rollout Strategy for AI SDK v5 Migration
 * Progressive deployment with safety gates and automatic rollback
 */

export interface RolloutStage {
  name: string
  description: string
  trafficPercentage: number
  minDuration: number // Hours
  successCriteria: SuccessCriteria
  rollbackTriggers: RollbackTrigger[]
  targetDate: string
}

export interface SuccessCriteria {
  minSampleSize: number
  maxErrorRate: number // Percentage
  maxP95Latency: number // Milliseconds
  minThroughputImprovement: number // Percentage
}

export interface RollbackTrigger {
  metric: 'error_rate' | 'p95_latency' | 'p99_latency' | 'throughput'
  threshold: number
  duration: number // Minutes
}

export interface RolloutStatus {
  currentStage: string
  startTime: number
  elapsedHours: number
  metrics: {
    sampleSize: number
    errorRate: number
    p95Latency: number
    throughputImprovement: number
  }
  healthStatus: 'healthy' | 'warning' | 'critical'
  canProgress: boolean
  shouldRollback: boolean
}

// Define rollout stages
export const ROLLOUT_STAGES: RolloutStage[] = [
  {
    name: 'canary',
    description: 'Initial canary deployment to 1% of traffic',
    trafficPercentage: 1,
    minDuration: 24,
    successCriteria: {
      minSampleSize: 100,
      maxErrorRate: 2,
      maxP95Latency: 500,
      minThroughputImprovement: -10 // Allow 10% degradation initially
    },
    rollbackTriggers: [
      { metric: 'error_rate', threshold: 5, duration: 5 },
      { metric: 'p95_latency', threshold: 1000, duration: 10 }
    ],
    targetDate: '2025-01-12'
  },
  {
    name: 'early_adopters',
    description: 'Expand to early adopters (5% of traffic)',
    trafficPercentage: 5,
    minDuration: 48,
    successCriteria: {
      minSampleSize: 500,
      maxErrorRate: 1.5,
      maxP95Latency: 400,
      minThroughputImprovement: 0
    },
    rollbackTriggers: [
      { metric: 'error_rate', threshold: 3, duration: 10 },
      { metric: 'p95_latency', threshold: 800, duration: 15 }
    ],
    targetDate: '2025-01-14'
  },
  {
    name: 'beta',
    description: 'Beta rollout to 20% of traffic',
    trafficPercentage: 20,
    minDuration: 72,
    successCriteria: {
      minSampleSize: 2000,
      maxErrorRate: 1,
      maxP95Latency: 350,
      minThroughputImprovement: 5
    },
    rollbackTriggers: [
      { metric: 'error_rate', threshold: 2, duration: 15 },
      { metric: 'p95_latency', threshold: 600, duration: 20 }
    ],
    targetDate: '2025-01-17'
  },
  {
    name: 'wide_release',
    description: 'Wide release to 50% of traffic',
    trafficPercentage: 50,
    minDuration: 96,
    successCriteria: {
      minSampleSize: 5000,
      maxErrorRate: 0.5,
      maxP95Latency: 300,
      minThroughputImprovement: 10
    },
    rollbackTriggers: [
      { metric: 'error_rate', threshold: 1.5, duration: 20 },
      { metric: 'p95_latency', threshold: 500, duration: 30 }
    ],
    targetDate: '2025-01-21'
  },
  {
    name: 'general_availability',
    description: 'General availability to all users',
    trafficPercentage: 100,
    minDuration: 168, // 1 week
    successCriteria: {
      minSampleSize: 10000,
      maxErrorRate: 0.5,
      maxP95Latency: 250,
      minThroughputImprovement: 15
    },
    rollbackTriggers: [
      { metric: 'error_rate', threshold: 1, duration: 30 },
      { metric: 'p95_latency', threshold: 400, duration: 60 }
    ],
    targetDate: '2025-01-25'
  }
]

class RolloutManager {
  private currentStageIndex: number = 0
  private stageStartTime: number = 0
  
  constructor() {
    this.loadState()
  }
  
  /**
   * Load rollout state from storage
   */
  private loadState() {
    try {
      const saved = localStorage.getItem('v5_rollout_state')
      if (saved) {
        const state = JSON.parse(saved)
        this.currentStageIndex = state.stageIndex
        this.stageStartTime = state.startTime
      } else {
        this.stageStartTime = Date.now()
        this.saveState()
      }
    } catch (e) {
      this.currentStageIndex = 0
      this.stageStartTime = Date.now()
    }
  }
  
  /**
   * Save rollout state to storage
   */
  private saveState() {
    try {
      localStorage.setItem('v5_rollout_state', JSON.stringify({
        stageIndex: this.currentStageIndex,
        startTime: this.stageStartTime
      }))
    } catch (e) {
      // Ignore storage errors
    }
  }
  
  /**
   * Get current rollout stage
   */
  getCurrentStage(): RolloutStage {
    return ROLLOUT_STAGES[this.currentStageIndex] || ROLLOUT_STAGES[0]
  }
  
  /**
   * Get rollout status
   */
  getStatus(): RolloutStatus {
    const stage = this.getCurrentStage()
    const elapsedHours = (Date.now() - this.stageStartTime) / (1000 * 60 * 60)
    
    // Get metrics from performance collector
    const metrics = this.collectMetrics()
    
    // Evaluate health status
    const healthStatus = this.evaluateHealth(stage, metrics)
    
    // Check if can progress to next stage
    const canProgress = this.canProgressToNextStage(stage, metrics, elapsedHours)
    
    // Check if should rollback
    const shouldRollback = this.shouldRollback(stage, metrics)
    
    return {
      currentStage: stage.name,
      startTime: this.stageStartTime,
      elapsedHours,
      metrics,
      healthStatus,
      canProgress,
      shouldRollback
    }
  }
  
  /**
   * Collect current metrics
   */
  private collectMetrics(): RolloutStatus['metrics'] {
    try {
      const v5Metrics = JSON.parse(localStorage.getItem('perf_metrics_v5') || '[]')
      const v3Metrics = JSON.parse(localStorage.getItem('perf_metrics_v3') || '[]')
      
      // Calculate error rate
      const v5Errors = v5Metrics.filter((m: any) => m.errorsCount > 0).length
      const errorRate = v5Metrics.length > 0 ? (v5Errors / v5Metrics.length) * 100 : 0
      
      // Calculate P95 latency
      const latencies = v5Metrics.map((m: any) => m.ttfm).sort((a: number, b: number) => a - b)
      const p95Index = Math.floor(latencies.length * 0.95)
      const p95Latency = latencies[p95Index] || 0
      
      // Calculate throughput improvement
      const v5Throughput = v5Metrics.reduce((sum: number, m: any) => 
        sum + (m.totalBytes / (m.streamingDuration / 1000)), 0) / Math.max(v5Metrics.length, 1)
      const v3Throughput = v3Metrics.reduce((sum: number, m: any) => 
        sum + (m.totalBytes / (m.streamingDuration / 1000)), 0) / Math.max(v3Metrics.length, 1)
      const throughputImprovement = v3Throughput > 0 ? 
        ((v5Throughput - v3Throughput) / v3Throughput) * 100 : 0
      
      return {
        sampleSize: v5Metrics.length,
        errorRate,
        p95Latency,
        throughputImprovement
      }
    } catch (e) {
      return {
        sampleSize: 0,
        errorRate: 0,
        p95Latency: 0,
        throughputImprovement: 0
      }
    }
  }
  
  /**
   * Evaluate health status
   */
  private evaluateHealth(
    stage: RolloutStage,
    metrics: RolloutStatus['metrics']
  ): 'healthy' | 'warning' | 'critical' {
    const { successCriteria, rollbackTriggers } = stage
    
    // Check critical conditions
    for (const trigger of rollbackTriggers) {
      if (trigger.metric === 'error_rate' && metrics.errorRate > trigger.threshold) {
        return 'critical'
      }
      if (trigger.metric === 'p95_latency' && metrics.p95Latency > trigger.threshold) {
        return 'critical'
      }
    }
    
    // Check warning conditions
    if (metrics.errorRate > successCriteria.maxErrorRate * 0.8) {
      return 'warning'
    }
    if (metrics.p95Latency > successCriteria.maxP95Latency * 0.8) {
      return 'warning'
    }
    
    return 'healthy'
  }
  
  /**
   * Check if can progress to next stage
   */
  private canProgressToNextStage(
    stage: RolloutStage,
    metrics: RolloutStatus['metrics'],
    elapsedHours: number
  ): boolean {
    const { successCriteria, minDuration } = stage
    
    // Check minimum duration
    if (elapsedHours < minDuration) {
      return false
    }
    
    // Check sample size
    if (metrics.sampleSize < successCriteria.minSampleSize) {
      return false
    }
    
    // Check error rate
    if (metrics.errorRate > successCriteria.maxErrorRate) {
      return false
    }
    
    // Check latency
    if (metrics.p95Latency > successCriteria.maxP95Latency) {
      return false
    }
    
    // Check throughput improvement
    if (metrics.throughputImprovement < successCriteria.minThroughputImprovement) {
      return false
    }
    
    return true
  }
  
  /**
   * Check if should rollback
   */
  private shouldRollback(
    stage: RolloutStage,
    metrics: RolloutStatus['metrics']
  ): boolean {
    // Check error rate trigger
    if (metrics.errorRate > stage.rollbackTriggers[0].threshold) {
      return true
    }
    
    // Check latency trigger
    if (metrics.p95Latency > stage.rollbackTriggers[1].threshold) {
      return true
    }
    
    return false
  }
  
  /**
   * Progress to next stage
   */
  progressToNextStage(): boolean {
    const status = this.getStatus()
    
    if (!status.canProgress) {
      return false
    }
    
    if (this.currentStageIndex < ROLLOUT_STAGES.length - 1) {
      this.currentStageIndex++
      this.stageStartTime = Date.now()
      this.saveState()
      
      // Update environment variable
      const newStage = this.getCurrentStage()
      this.updateTrafficAllocation(newStage.trafficPercentage)
      
      return true
    }
    
    return false
  }
  
  /**
   * Rollback to previous stage
   */
  rollback(): boolean {
    if (this.currentStageIndex > 0) {
      this.currentStageIndex--
      this.stageStartTime = Date.now()
      this.saveState()
      
      // Update environment variable
      const newStage = this.getCurrentStage()
      this.updateTrafficAllocation(newStage.trafficPercentage)
      
      return true
    }
    
    // Emergency rollback to 0%
    this.updateTrafficAllocation(0)
    return false
  }
  
  /**
   * Update traffic allocation
   */
  private updateTrafficAllocation(percentage: number) {
    // In production, this would update the environment variable
    // through Vercel API or configuration management
    console.log(`[Rollout] Updating traffic allocation to ${percentage}%`)
    
    // For development, update localStorage
    localStorage.setItem('v5_traffic_percentage', percentage.toString())
  }
}

// Export singleton instance
export const rolloutManager = new RolloutManager()

// Export helper functions
export const getCurrentRolloutStage = () => rolloutManager.getCurrentStage()
export const getRolloutStatus = () => rolloutManager.getStatus()
export const progressRollout = () => rolloutManager.progressToNextStage()
export const rollbackDeployment = () => rolloutManager.rollback()