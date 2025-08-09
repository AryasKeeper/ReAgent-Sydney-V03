'use client'

import { useState } from 'react'
import { ChevronRight } from 'lucide-react'
import AgentStatusBar from '@/components/agent-status-bar'
import ChatInterface from '@/components/chat-interface'

export default function HomePage() {
  const [showChat, setShowChat] = useState(false)

  return (
    <div className="min-h-screen">
      {!showChat ? (
        // Hero Section - Apple-inspired minimalism
        <div className="flex flex-col min-h-screen">
          <div className="flex-1 flex items-center justify-center px-6">
            <div className="max-w-4xl mx-auto text-center space-y-8">
              {/* Subtle badge */}
              <div className="inline-block">
                <span className="text-xs font-medium tracking-wider uppercase text-gray-500 dark:text-white/60">
                  Sydney Real Estate Intelligence
                </span>
              </div>
              
              {/* Strong headline */}
              <h1 className="text-5xl md:text-7xl font-semibold tracking-tight">
                Intelligence that sees
                <span className="block text-gray-400 dark:text-white/40">
                  tomorrow's market today
                </span>
              </h1>
              
              {/* Clear value prop */}
              <p className="text-xl text-gray-600 dark:text-white/70 max-w-2xl mx-auto">
                ReAgent analyzes millions of data points to give professionals 
                an unfair advantage in real estate.
              </p>
              
              {/* Single CTA */}
              <div className="pt-8">
                <button
                  onClick={() => setShowChat(true)}
                  className="group inline-flex items-center gap-2 px-8 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors"
                >
                  Start Conversation
                  <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>
              
              {/* Trust metrics */}
              <div className="flex justify-center gap-12 pt-16 text-sm text-gray-500 dark:text-white/60">
                <div>
                  <div className="text-2xl font-semibold">2.3s</div>
                  <div>Response Time</div>
                </div>
                <div>
                  <div className="text-2xl font-semibold">94%</div>
                  <div>Match Accuracy</div>
                </div>
                <div>
                  <div className="text-2xl font-semibold">24/7</div>
                  <div>Monitoring</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Agent Status Bar - Minimal */}
          <AgentStatusBar />
        </div>
      ) : (
        // Chat Interface
        <div className="h-screen flex flex-col">
          <AgentStatusBar />
          <ChatInterface onBack={() => setShowChat(false)} />
        </div>
      )}
    </div>
  )
}