/**
 * AI Elements Abstraction Layer
 * Provides unified interface that switches between custom and official components
 * based on feature flags for progressive migration
 */

'use client'

import { lazy, Suspense, ComponentType } from 'react'
import { isComponentMigrated } from '@/lib/ai-elements-migration'

// Import custom components
import { 
  Message as CustomMessage, 
  MessageContent as CustomMessageContent,
  type MessageProps 
} from './message'
import { Response as CustomResponse } from './response'
import { MessageActions as CustomMessageActions, CopyButton as CustomCopyButton } from './actions'
import { ChatInput as CustomChatInput } from './input'
import { ReasoningPanel as CustomReasoningPanel } from './reasoning'

// Loading fallback
const LoadingFallback = () => <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded h-4 w-full" />

/**
 * Dynamic component loader with migration support
 */
function createMigratedComponent<T extends {}>(
  componentName: string,
  CustomComponent: ComponentType<T>,
  officialPath?: string
): ComponentType<T> {
  // Check if we should use the official component
  const shouldUseOfficial = isComponentMigrated(componentName)
  
  if (shouldUseOfficial && officialPath) {
    // Dynamically import official component (when available)
    // For now, we'll return the custom component with a migration indicator
    console.log(`[AI Elements] Component ${componentName} is flagged for migration but official component not yet available`)
    
    // This is where we would import the official component:
    // const OfficialComponent = lazy(() => import(officialPath))
    // return (props: T) => (
    //   <Suspense fallback={<LoadingFallback />}>
    //     <OfficialComponent {...props} />
    //   </Suspense>
    // )
  }
  
  // Return custom component
  return CustomComponent
}

/**
 * Exported components with migration support
 */
export const Message = createMigratedComponent(
  'Message',
  CustomMessage,
  '@ai-sdk/ui/message'
)

export const MessageContent = createMigratedComponent(
  'MessageContent',
  CustomMessageContent,
  '@ai-sdk/ui/message-content'
)

export const Response = createMigratedComponent(
  'Response',
  CustomResponse,
  '@ai-sdk/ui/response'
)

export const MessageActions = createMigratedComponent(
  'MessageActions',
  CustomMessageActions,
  '@ai-sdk/ui/message-actions'
)

export const CopyButton = createMigratedComponent(
  'CopyButton',
  CustomCopyButton,
  '@ai-sdk/ui/copy-button'
)

export const ChatInput = createMigratedComponent(
  'ChatInput',
  CustomChatInput,
  '@ai-sdk/ui/chat-input'
)

export const ReasoningPanel = createMigratedComponent(
  'ReasoningPanel',
  CustomReasoningPanel,
  '@ai-sdk/ui/reasoning-panel'
)

// Re-export types
export type { MessageProps }

/**
 * Component compatibility adapter
 * Ensures props work with both custom and official components
 */
export function adaptMessageProps(props: any): MessageProps {
  // Map official AI Elements props to our custom props if needed
  if ('role' in props && !('from' in props)) {
    return {
      ...props,
      from: props.role === 'user' ? 'user' : 'assistant'
    }
  }
  return props
}

/**
 * Migration status indicator for development
 */
export function MigrationIndicator({ componentName }: { componentName: string }) {
  if (process.env.NODE_ENV !== 'development') return null
  
  const isMigrated = isComponentMigrated(componentName)
  
  return (
    <div className="absolute top-0 right-0 text-[8px] px-1 py-0.5 rounded-bl bg-black/50 text-white">
      {isMigrated ? '✓ Official' : 'Custom'}
    </div>
  )
}