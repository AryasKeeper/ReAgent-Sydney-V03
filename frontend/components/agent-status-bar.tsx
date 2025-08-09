'use client'

import { useState, useEffect } from 'react'
import { Activity, Eye, Signal, Heart, TrendingUp, Radar } from 'lucide-react'

interface Agent {
  id: string
  name: string
  status: 'active' | 'idle' | 'processing'
  icon: React.ElementType
  description: string
}

const agents: Agent[] = [
  {
    id: 'whisperer',
    name: 'Agent Whisperer',
    status: 'active',
    icon: Activity,
    description: 'Natural language interface'
  },
  {
    id: 'watcher',
    name: 'Market Watcher',
    status: 'idle',
    icon: Eye,
    description: 'Monitoring market trends'
  },
  {
    id: 'signal',
    name: 'Signal',
    status: 'idle',
    icon: Signal,
    description: 'Detecting opportunities'
  },
  {
    id: 'matchmaker',
    name: 'Matchmaker',
    status: 'idle',
    icon: Heart,
    description: 'Buyer-property matching'
  },
  {
    id: 'seller',
    name: 'Seller Consultant',
    status: 'idle',
    icon: TrendingUp,
    description: 'Pricing optimization'
  },
  {
    id: 'radar',
    name: 'Off-Market Radar',
    status: 'idle',
    icon: Radar,
    description: 'Hidden opportunities'
  }
]

interface AgentStatusBarProps {
  position?: 'top' | 'bottom'
}

export default function AgentStatusBar({ position = 'bottom' }: AgentStatusBarProps) {
  const [agentStates, setAgentStates] = useState(agents)

  // Simulate agent activity
  useEffect(() => {
    const interval = setInterval(() => {
      setAgentStates(prev => prev.map(agent => ({
        ...agent,
        status: agent.id === 'whisperer' ? 'active' : 
                Math.random() > 0.9 ? 'processing' : 
                Math.random() > 0.7 ? 'active' : 'idle'
      })))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'processing': return 'bg-blue-500 animate-pulse'
      case 'idle': return 'bg-gray-300'
    }
  }

  const borderClass = position === 'top' ? 'border-b' : 'border-t'
  return (
    <div className={`${borderClass} bg-surface/50 backdrop-blur-sm dark:bg-white/5 overflow-visible`}>
      <div className="px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-6 overflow-x-auto overflow-visible">
            {agentStates.map((agent) => {
              const Icon = agent.icon
              return (
                <div
                  key={agent.id}
                  className="flex items-center gap-2 shrink-0 group"
                  title={agent.description}
                >
                  <div className="relative">
                    <Icon className="w-4 h-4 text-text-secondary dark:text-white/70" />
                    <div
                      className={`absolute -top-0.5 -right-1 w-2 h-2 rounded-full ${getStatusColor(agent.status)}`}
                    />
                  </div>
                  <span className="text-xs font-medium text-text-secondary dark:text-white/70 group-hover:text-text-primary dark:group-hover:text-white transition-colors">
                    {agent.name}
                  </span>
                </div>
              )
            })}
          </div>
          
          <div className="flex items-center gap-2 text-xs text-text-muted dark:text-white/60">
            <div className="w-2 h-2 bg-green-500 rounded-full" />
            <span>All Systems Operational</span>
          </div>
        </div>
      </div>
    </div>
  )
}