/**
 * AI Elements Migration Tests
 * Validates that custom and official components maintain compatibility
 */

import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { 
  Message, 
  MessageContent, 
  Response, 
  ChatInput, 
  ReasoningPanel, 
  MessageActions,
  adaptMessageProps 
} from '../index'

describe('AI Elements Migration', () => {
  
  describe('Message Component', () => {
    it('renders user message correctly', () => {
      render(
        <Message from="user">
          <MessageContent>Test user message</MessageContent>
        </Message>
      )
      
      expect(screen.getByText('Test user message')).toBeInTheDocument()
    })
    
    it('renders assistant message correctly', () => {
      render(
        <Message from="assistant">
          <MessageContent>Test assistant message</MessageContent>
        </Message>
      )
      
      expect(screen.getByText('Test assistant message')).toBeInTheDocument()
    })
    
    it('adapts props correctly', () => {
      const officialProps = { role: 'user', children: 'Test' }
      const adapted = adaptMessageProps(officialProps)
      
      expect(adapted.from).toBe('user')
      expect(adapted.children).toBe('Test')
    })
  })
  
  describe('ChatInput Component', () => {
    it('renders input field', () => {
      const onChange = jest.fn()
      const onSubmit = jest.fn()
      
      render(
        <ChatInput 
          value="Test input"
          onChange={onChange}
          onSubmit={onSubmit}
        />
      )
      
      const input = screen.getByPlaceholderText(/Ask about Sydney properties/i)
      expect(input).toHaveValue('Test input')
    })
    
    it('handles submit on Enter key', () => {
      const onChange = jest.fn()
      const onSubmit = jest.fn()
      
      render(
        <ChatInput 
          value="Test input"
          onChange={onChange}
          onSubmit={onSubmit}
        />
      )
      
      const input = screen.getByPlaceholderText(/Ask about Sydney properties/i)
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
      
      expect(onSubmit).toHaveBeenCalled()
    })
    
    it('does not submit on Shift+Enter', () => {
      const onChange = jest.fn()
      const onSubmit = jest.fn()
      
      render(
        <ChatInput 
          value="Test input"
          onChange={onChange}
          onSubmit={onSubmit}
        />
      )
      
      const input = screen.getByPlaceholderText(/Ask about Sydney properties/i)
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: true })
      
      expect(onSubmit).not.toHaveBeenCalled()
    })
  })
  
  describe('MessageActions Component', () => {
    it('renders copy button', () => {
      render(
        <MessageActions 
          contentForCopy="Test content"
        />
      )
      
      expect(screen.getByText('Copy')).toBeInTheDocument()
    })
    
    it('shows regenerate button when handler provided', () => {
      const onRegenerate = jest.fn()
      
      render(
        <MessageActions 
          contentForCopy="Test content"
          onRegenerate={onRegenerate}
        />
      )
      
      expect(screen.getByText('Regenerate')).toBeInTheDocument()
    })
    
    it('shows stop button when loading', () => {
      const onStop = jest.fn()
      
      render(
        <MessageActions 
          contentForCopy="Test content"
          isLoading={true}
          onStop={onStop}
        />
      )
      
      expect(screen.getByText('Stop')).toBeInTheDocument()
    })
  })
  
  describe('ReasoningPanel Component', () => {
    it('renders collapsed by default', () => {
      render(
        <ReasoningPanel title="Test Reasoning" />
      )
      
      expect(screen.getByText('Test Reasoning')).toBeInTheDocument()
      expect(screen.queryByText(/The assistant is thinking/i)).not.toBeInTheDocument()
    })
    
    it('expands when clicked', () => {
      render(
        <ReasoningPanel title="Test Reasoning" />
      )
      
      const button = screen.getByRole('button')
      fireEvent.click(button)
      
      expect(screen.getByText(/The assistant is thinking/i)).toBeInTheDocument()
    })
    
    it('shows loading indicator when isLoading', () => {
      render(
        <ReasoningPanel title="Test Reasoning" isLoading={true} />
      )
      
      // Check for loading spinner (animate-spin class)
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })
  })
  
  describe('Response Component', () => {
    it('renders text content', () => {
      render(
        <Response>Test response content</Response>
      )
      
      expect(screen.getByText('Test response content')).toBeInTheDocument()
    })
  })
})

describe('Migration Feature Flags', () => {
  const originalEnv = process.env
  
  beforeEach(() => {
    jest.resetModules()
    process.env = { ...originalEnv }
  })
  
  afterAll(() => {
    process.env = originalEnv
  })
  
  it('uses custom components when flags are disabled', () => {
    process.env.NEXT_PUBLIC_AI_ELEMENTS_ENABLED = 'false'
    
    const { isComponentMigrated } = require('@/lib/ai-elements-migration')
    
    expect(isComponentMigrated('Message')).toBe(false)
    expect(isComponentMigrated('ChatInput')).toBe(false)
  })
  
  it('detects migration when global flag is enabled', () => {
    process.env.NEXT_PUBLIC_AI_ELEMENTS_ENABLED = 'true'
    
    const { isComponentMigrated } = require('@/lib/ai-elements-migration')
    
    expect(isComponentMigrated('Message')).toBe(true)
    expect(isComponentMigrated('ChatInput')).toBe(true)
  })
  
  it('respects individual component flags over global', () => {
    process.env.NEXT_PUBLIC_AI_ELEMENTS_ENABLED = 'false'
    process.env.NEXT_PUBLIC_AI_ELEMENTS_MESSAGE = 'true'
    
    const { isComponentMigrated } = require('@/lib/ai-elements-migration')
    
    expect(isComponentMigrated('Message')).toBe(true)
    expect(isComponentMigrated('ChatInput')).toBe(false)
  })
})

describe('Migration Validation', () => {
  const originalEnv = process.env
  
  beforeEach(() => {
    jest.resetModules()
    process.env = { ...originalEnv }
  })
  
  afterAll(() => {
    process.env = originalEnv
  })
  
  it('blocks migration when AI SDK v5 is disabled', () => {
    process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED = 'false'
    
    const { validateMigration } = require('@/lib/ai-elements-migration')
    const validation = validateMigration('Message')
    
    expect(validation.canMigrate).toBe(false)
    expect(validation.blockers).toContain('AI SDK v5 must be enabled for official AI Elements')
  })
  
  it('warns about low test coverage', () => {
    process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED = 'true'
    
    const { validateMigration } = require('@/lib/ai-elements-migration')
    const validation = validateMigration('Message')
    
    expect(validation.warnings).toContain('Low test coverage: 0%')
  })
  
  it('warns about unmigrated dependencies', () => {
    process.env.NEXT_PUBLIC_AI_SDK_V5_ENABLED = 'true'
    process.env.NEXT_PUBLIC_AI_ELEMENTS_MESSAGE = 'false'
    
    const { validateMigration } = require('@/lib/ai-elements-migration')
    const validation = validateMigration('MessageActions')
    
    // MessageActions depends on CopyButton
    expect(validation.warnings.some(w => w.includes('CopyButton'))).toBe(true)
  })
})