/**
 * AI Elements Migration Strategy
 * Maps custom components to official AI Elements with progressive rollout
 */

export interface ComponentMigrationConfig {
  name: string
  customPath: string
  officialComponent: string
  featureFlag: string
  migrationStatus: 'pending' | 'in_progress' | 'completed'
  dependencies: string[]
  riskLevel: 'low' | 'medium' | 'high'
  testCoverage: number
}

export const COMPONENT_MIGRATION_MAP: ComponentMigrationConfig[] = [
  {
    name: 'Message',
    customPath: '@/components/ai-elements/message',
    officialComponent: '@ai-sdk/ui/message',
    featureFlag: 'NEXT_PUBLIC_AI_ELEMENTS_MESSAGE',
    migrationStatus: 'pending',
    dependencies: ['MessageContent'],
    riskLevel: 'low',
    testCoverage: 0
  },
  {
    name: 'MessageContent',
    customPath: '@/components/ai-elements/message',
    officialComponent: '@ai-sdk/ui/message-content',
    featureFlag: 'NEXT_PUBLIC_AI_ELEMENTS_MESSAGE_CONTENT',
    migrationStatus: 'pending',
    dependencies: [],
    riskLevel: 'low',
    testCoverage: 0
  },
  {
    name: 'Response',
    customPath: '@/components/ai-elements/response',
    officialComponent: '@ai-sdk/ui/response',
    featureFlag: 'NEXT_PUBLIC_AI_ELEMENTS_RESPONSE',
    migrationStatus: 'pending',
    dependencies: [],
    riskLevel: 'low',
    testCoverage: 0
  },
  {
    name: 'MessageActions',
    customPath: '@/components/ai-elements/actions',
    officialComponent: '@ai-sdk/ui/message-actions',
    featureFlag: 'NEXT_PUBLIC_AI_ELEMENTS_ACTIONS',
    migrationStatus: 'pending',
    dependencies: ['CopyButton'],
    riskLevel: 'medium',
    testCoverage: 0
  },
  {
    name: 'ChatInput',
    customPath: '@/components/ai-elements/input',
    officialComponent: '@ai-sdk/ui/chat-input',
    featureFlag: 'NEXT_PUBLIC_AI_ELEMENTS_INPUT',
    migrationStatus: 'pending',
    dependencies: [],
    riskLevel: 'medium',
    testCoverage: 0
  },
  {
    name: 'ReasoningPanel',
    customPath: '@/components/ai-elements/reasoning',
    officialComponent: '@ai-sdk/ui/reasoning-panel',
    featureFlag: 'NEXT_PUBLIC_AI_ELEMENTS_REASONING',
    migrationStatus: 'pending',
    dependencies: [],
    riskLevel: 'low',
    testCoverage: 0
  }
]

/**
 * Migration risk assessment
 */
export interface MigrationRisk {
  component: string
  risks: string[]
  mitigations: string[]
  rollbackPlan: string
}

export const MIGRATION_RISKS: MigrationRisk[] = [
  {
    component: 'Message',
    risks: [
      'Style differences between custom and official components',
      'Prop interface changes'
    ],
    mitigations: [
      'Create adapter layer for prop mapping',
      'Add CSS overrides for style consistency'
    ],
    rollbackPlan: 'Feature flag disable + cache clear'
  },
  {
    component: 'MessageActions',
    risks: [
      'Custom copy functionality may differ',
      'Button interactions and states'
    ],
    mitigations: [
      'Test copy functionality across browsers',
      'Verify all action handlers work correctly'
    ],
    rollbackPlan: 'Immediate feature flag disable'
  },
  {
    component: 'ChatInput',
    risks: [
      'Form submission behavior differences',
      'Keyboard shortcut handling',
      'Auto-resize functionality'
    ],
    mitigations: [
      'Extensive E2E testing of input scenarios',
      'Monitor user input metrics'
    ],
    rollbackPlan: 'Revert to custom component via flag'
  }
]

/**
 * Component feature flag checker
 */
export function isComponentMigrated(componentName: string): boolean {
  if (typeof window === 'undefined') return false
  
  const config = COMPONENT_MIGRATION_MAP.find(c => c.name === componentName)
  if (!config) return false
  
  // Check specific component flag
  const specificFlag = process.env[config.featureFlag]
  if (specificFlag !== undefined) {
    return specificFlag === 'true'
  }
  
  // Fall back to global AI Elements flag
  return process.env.NEXT_PUBLIC_AI_ELEMENTS_ENABLED === 'true'
}

/**
 * Get migration status for dashboard
 */
export function getMigrationStatus(): {
  total: number
  migrated: number
  percentage: number
  components: Array<{
    name: string
    status: 'pending' | 'migrated' | 'in_progress'
    enabled: boolean
  }>
} {
  const components = COMPONENT_MIGRATION_MAP.map(config => ({
    name: config.name,
    status: isComponentMigrated(config.name) ? 'migrated' as const : config.migrationStatus,
    enabled: isComponentMigrated(config.name)
  }))
  
  const migrated = components.filter(c => c.enabled).length
  
  return {
    total: components.length,
    migrated,
    percentage: Math.round((migrated / components.length) * 100),
    components
  }
}

/**
 * Migration validation
 */
export function validateMigration(componentName: string): {
  canMigrate: boolean
  blockers: string[]
  warnings: string[]
} {
  const config = COMPONENT_MIGRATION_MAP.find(c => c.name === componentName)
  if (!config) {
    return {
      canMigrate: false,
      blockers: ['Component not found in migration map'],
      warnings: []
    }
  }
  
  const blockers: string[] = []
  const warnings: string[] = []
  
  // Check dependencies
  for (const dep of config.dependencies) {
    const depConfig = COMPONENT_MIGRATION_MAP.find(c => c.name === dep)
    if (depConfig && !isComponentMigrated(dep)) {
      warnings.push(`Dependency ${dep} not yet migrated`)
    }
  }
  
  // Check test coverage
  if (config.testCoverage < 80) {
    warnings.push(`Low test coverage: ${config.testCoverage}%`)
  }
  
  // Check risk level
  if (config.riskLevel === 'high') {
    warnings.push('High risk component - extra validation required')
  }
  
  // Check AI SDK v5 is enabled for official components
  if (process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED !== 'true') {
    blockers.push('AI SDK v5 must be enabled for official AI Elements')
  }
  
  return {
    canMigrate: blockers.length === 0,
    blockers,
    warnings
  }
}