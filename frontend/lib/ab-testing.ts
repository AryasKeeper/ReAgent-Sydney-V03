/**
 * A/B Testing Framework for AI SDK v5 Migration
 * Enables gradual rollout and performance comparison
 */

import { headers } from 'next/headers'

export interface ABTestConfig {
  experimentId: string
  control: 'v3'
  variant: 'v5'
  trafficAllocation: number // Percentage for variant (0-100)
  enabledEnvironments: string[]
  forceVariantUsers?: string[] // Session IDs to force into variant
  excludeUsers?: string[] // Session IDs to exclude from experiment
}

export interface ABTestResult {
  version: 'v3' | 'v5'
  experimentId: string
  isExperiment: boolean
  reason: string
}

// Migration experiment configuration
const MIGRATION_EXPERIMENT: ABTestConfig = {
  experimentId: 'ai-sdk-v5-migration',
  control: 'v3',
  variant: 'v5',
  trafficAllocation: parseInt(process.env.NEXT_PUBLIC_V5_TRAFFIC_PERCENTAGE || '10'),
  enabledEnvironments: ['development', 'preview', 'production'],
  forceVariantUsers: process.env.NEXT_PUBLIC_V5_FORCE_USERS?.split(',').filter(Boolean),
  excludeUsers: process.env.NEXT_PUBLIC_V5_EXCLUDE_USERS?.split(',').filter(Boolean)
}

/**
 * Determines which SDK version to use for a given session
 */
export function determineSDKVersion(sessionId: string): ABTestResult {
  // Check if explicitly enabled via feature flag
  if (process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED === 'true') {
    return {
      version: 'v5',
      experimentId: MIGRATION_EXPERIMENT.experimentId,
      isExperiment: false,
      reason: 'Feature flag enabled'
    }
  }

  // Check if explicitly disabled
  if (process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED === 'false') {
    return {
      version: 'v3',
      experimentId: MIGRATION_EXPERIMENT.experimentId,
      isExperiment: false,
      reason: 'Feature flag disabled'
    }
  }

  // Check environment eligibility
  const currentEnv = process.env.NODE_ENV || 'development'
  if (!MIGRATION_EXPERIMENT.enabledEnvironments.includes(currentEnv)) {
    return {
      version: 'v3',
      experimentId: MIGRATION_EXPERIMENT.experimentId,
      isExperiment: false,
      reason: `Environment ${currentEnv} not eligible`
    }
  }

  // Check exclusion list
  if (MIGRATION_EXPERIMENT.excludeUsers?.includes(sessionId)) {
    return {
      version: 'v3',
      experimentId: MIGRATION_EXPERIMENT.experimentId,
      isExperiment: false,
      reason: 'User excluded from experiment'
    }
  }

  // Check force variant list
  if (MIGRATION_EXPERIMENT.forceVariantUsers?.includes(sessionId)) {
    return {
      version: 'v5',
      experimentId: MIGRATION_EXPERIMENT.experimentId,
      isExperiment: true,
      reason: 'User forced into variant'
    }
  }

  // Perform consistent hashing for traffic allocation
  const hash = simpleHash(sessionId + MIGRATION_EXPERIMENT.experimentId)
  const bucketValue = (hash % 100) + 1

  if (bucketValue <= MIGRATION_EXPERIMENT.trafficAllocation) {
    return {
      version: 'v5',
      experimentId: MIGRATION_EXPERIMENT.experimentId,
      isExperiment: true,
      reason: `Traffic allocation (${bucketValue}/${MIGRATION_EXPERIMENT.trafficAllocation})`
    }
  }

  return {
    version: 'v3',
    experimentId: MIGRATION_EXPERIMENT.experimentId,
    isExperiment: true,
    reason: `Control group (${bucketValue}/${MIGRATION_EXPERIMENT.trafficAllocation})`
  }
}

/**
 * Simple hash function for consistent bucketing
 */
function simpleHash(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return Math.abs(hash)
}

/**
 * Gets A/B test headers for backend communication
 */
export function getABTestHeaders(result: ABTestResult): Record<string, string> {
  const headers: Record<string, string> = {}
  
  if (result.version === 'v5') {
    headers['x-vercel-ai-ui-message-stream'] = 'v1'
    headers['x-ai-sdk-version'] = '5'
  }
  
  // Add experiment tracking headers
  headers['x-experiment-id'] = result.experimentId
  headers['x-experiment-version'] = result.version
  headers['x-experiment-active'] = result.isExperiment.toString()
  
  return headers
}

/**
 * Logs A/B test assignment for monitoring
 */
export function logABTestAssignment(
  sessionId: string,
  result: ABTestResult,
  metadata?: Record<string, any>
) {
  if (process.env.NODE_ENV === 'development') {
    console.log('[A/B Test Assignment]', {
      sessionId,
      ...result,
      metadata,
      timestamp: new Date().toISOString()
    })
  }

  // In production, this would send to analytics service
  // Example: sendToAnalytics('ab_test_assignment', { ... })
}

/**
 * Reports SDK version for current request (server-side)
 */
export async function getServerSDKVersion(): Promise<'v3' | 'v5'> {
  const headersList = headers()
  const sdkVersion = headersList.get('x-ai-sdk-version')
  
  if (sdkVersion === '5') {
    return 'v5'
  }
  
  // Check UI Message Stream header as fallback
  const uiStream = headersList.get('x-vercel-ai-ui-message-stream')
  if (uiStream === 'v1') {
    return 'v5'
  }
  
  return 'v3'
}