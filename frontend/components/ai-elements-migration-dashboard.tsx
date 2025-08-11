'use client'

import { useState, useEffect } from 'react'
import { getMigrationStatus, validateMigration, COMPONENT_MIGRATION_MAP } from '@/lib/ai-elements-migration'
import { CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'

export function AIElementsMigrationDashboard() {
  const [status, setStatus] = useState(getMigrationStatus())
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  
  useEffect(() => {
    // Only show in development or with debug flag
    const showDashboard = process.env.NODE_ENV === 'development' || 
                         localStorage.getItem('show_ai_elements_dashboard') === 'true'
    setIsVisible(showDashboard)
    
    if (!showDashboard) return
    
    // Update status every 3 seconds
    const interval = setInterval(() => {
      setStatus(getMigrationStatus())
    }, 3000)
    
    return () => clearInterval(interval)
  }, [])
  
  if (!isVisible) return null
  
  const getStatusIcon = (status: 'pending' | 'migrated' | 'in_progress') => {
    switch (status) {
      case 'migrated':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'in_progress':
        return <Clock className="w-4 h-4 text-yellow-400 animate-pulse" />
      case 'pending':
        return <XCircle className="w-4 h-4 text-gray-400" />
    }
  }
  
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-400'
      case 'medium': return 'text-yellow-400'
      case 'high': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }
  
  return (
    <div className="fixed top-4 right-4 bg-black/90 text-white p-4 rounded-lg text-xs font-mono z-50 max-w-sm">
      <div className="flex justify-between items-center mb-3">
        <div className="font-bold text-sm">AI Elements Migration</div>
        <div className="text-green-400">
          {status.percentage}% Complete
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="w-full bg-gray-700 rounded-full h-2 mb-3">
        <div 
          className="bg-gradient-to-r from-blue-400 to-green-400 h-2 rounded-full transition-all duration-500"
          style={{ width: `${status.percentage}%` }}
        />
      </div>
      
      {/* Component list */}
      <div className="space-y-2 mb-3">
        {status.components.map(component => {
          const config = COMPONENT_MIGRATION_MAP.find(c => c.name === component.name)
          return (
            <div 
              key={component.name}
              className="flex items-center justify-between p-2 bg-white/5 rounded hover:bg-white/10 cursor-pointer transition-colors"
              onClick={() => setSelectedComponent(
                selectedComponent === component.name ? null : component.name
              )}
            >
              <div className="flex items-center gap-2">
                {getStatusIcon(component.status)}
                <span className={component.enabled ? 'text-green-400' : ''}>
                  {component.name}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {config && (
                  <span className={`text-[10px] ${getRiskColor(config.riskLevel)}`}>
                    {config.riskLevel} risk
                  </span>
                )}
                {component.enabled && (
                  <span className="text-[10px] text-green-400">Active</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
      
      {/* Selected component details */}
      {selectedComponent && (
        <div className="border-t border-white/20 pt-3">
          <ComponentValidation componentName={selectedComponent} />
        </div>
      )}
      
      {/* Migration stats */}
      <div className="border-t border-white/20 pt-3 mt-3 grid grid-cols-2 gap-2 text-[10px]">
        <div>
          <div className="text-gray-400">Total Components</div>
          <div className="text-lg">{status.total}</div>
        </div>
        <div>
          <div className="text-gray-400">Migrated</div>
          <div className="text-lg text-green-400">{status.migrated}</div>
        </div>
      </div>
      
      {/* Feature flags status */}
      <div className="mt-3 pt-3 border-t border-white/20 text-[10px]">
        <div className="text-gray-400 mb-1">Feature Flags</div>
        <div className="space-y-1">
          <div className="flex justify-between">
            <span>AI SDK v5</span>
            <span className={process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED === 'true' ? 'text-green-400' : 'text-gray-400'}>
              {process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED === 'true' ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>AI Elements Global</span>
            <span className={process.env.NEXT_PUBLIC_AI_ELEMENTS_ENABLED === 'true' ? 'text-green-400' : 'text-gray-400'}>
              {process.env.NEXT_PUBLIC_AI_ELEMENTS_ENABLED === 'true' ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

function ComponentValidation({ componentName }: { componentName: string }) {
  const validation = validateMigration(componentName)
  const config = COMPONENT_MIGRATION_MAP.find(c => c.name === componentName)
  
  if (!config) return null
  
  return (
    <div className="space-y-2 text-[10px]">
      <div className="font-bold text-xs mb-2">{componentName} Details</div>
      
      {/* Feature flag */}
      <div className="flex justify-between">
        <span className="text-gray-400">Feature Flag</span>
        <span className="text-[9px] font-mono">{config.featureFlag}</span>
      </div>
      
      {/* Test coverage */}
      <div className="flex justify-between">
        <span className="text-gray-400">Test Coverage</span>
        <span className={config.testCoverage >= 80 ? 'text-green-400' : 'text-yellow-400'}>
          {config.testCoverage}%
        </span>
      </div>
      
      {/* Dependencies */}
      {config.dependencies.length > 0 && (
        <div>
          <div className="text-gray-400 mb-1">Dependencies</div>
          <div className="pl-2">
            {config.dependencies.map(dep => (
              <div key={dep} className="text-gray-300">{dep}</div>
            ))}
          </div>
        </div>
      )}
      
      {/* Validation status */}
      <div className="mt-2 pt-2 border-t border-white/10">
        <div className="flex items-center gap-1 mb-1">
          {validation.canMigrate ? (
            <>
              <CheckCircle className="w-3 h-3 text-green-400" />
              <span className="text-green-400">Ready to migrate</span>
            </>
          ) : (
            <>
              <XCircle className="w-3 h-3 text-red-400" />
              <span className="text-red-400">Cannot migrate</span>
            </>
          )}
        </div>
        
        {/* Blockers */}
        {validation.blockers.length > 0 && (
          <div className="mt-1">
            <div className="text-red-400 mb-1">Blockers:</div>
            {validation.blockers.map((blocker, i) => (
              <div key={i} className="pl-2 text-red-300">• {blocker}</div>
            ))}
          </div>
        )}
        
        {/* Warnings */}
        {validation.warnings.length > 0 && (
          <div className="mt-1">
            <div className="text-yellow-400 mb-1">Warnings:</div>
            {validation.warnings.map((warning, i) => (
              <div key={i} className="pl-2 text-yellow-300">• {warning}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}