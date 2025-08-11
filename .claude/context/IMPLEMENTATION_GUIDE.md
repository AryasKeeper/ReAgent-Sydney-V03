# Implementation Guide - ReAgent Sydney V03
*Version: 1.0.0*
*Last Updated: 2025-08-11*

## Quick Start Security Fixes

### 1. Disable DEBUG Mode (5 minutes)
```python
# backend/config.py - Line ~41
class Settings(BaseSettings):
    DEBUG: bool = Field(default=False, env="DEBUG")  # Changed from True
    # OR better: Remove hardcoded default, require env var
    DEBUG: bool = Field(env="DEBUG")  # No default
```

### 2. Enable Mandatory Authentication (30 minutes)
```python
# backend/config.py
class Settings(BaseSettings):
    REQUIRE_API_KEY: bool = Field(default=True, env="REQUIRE_API_KEY")  # Changed from False
    API_KEY: str = Field(env="API_KEY")  # Required, no default
```

### 3. Add Input Validation (1 hour)
```python
# backend/api/agent_whisperer.py
from pydantic import BaseModel, Field, validator

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(..., min_length=1, max_length=100)
    messages: Optional[List[Message]] = Field(default=None, max_items=100)
    
    @validator('message')
    def sanitize_message(cls, v):
        # Remove potential injection patterns
        v = v.replace('\x00', '')  # Null bytes
        v = v.strip()
        if not v:
            raise ValueError('Message cannot be empty')
        return v
    
    @validator('session_id')
    def validate_session_id(cls, v):
        # Only allow alphanumeric and hyphens
        import re
        if not re.match(r'^[a-zA-Z0-9-]+$', v):
            raise ValueError('Invalid session ID format')
        return v
```

## Performance Quick Wins

### 1. Implement Connection Pooling (2 hours)
```python
# backend/services/http_client.py (NEW FILE)
import httpx
from typing import Optional

class HTTPClientManager:
    _client: Optional[httpx.AsyncClient] = None
    
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=100,
                    keepalive_expiry=30
                ),
                timeout=httpx.Timeout(30.0),
                http2=True
            )
        return cls._client
    
    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.aclose()
            cls._client = None

# Use in services:
# backend/services/ai_router_simple.py
from .http_client import HTTPClientManager

class AIRouter:
    async def _get_openai_client(self):
        http_client = await HTTPClientManager.get_client()
        return OpenAI(
            api_key=self.openai_api_key,
            http_client=http_client
        )
```

### 2. Async Redis Operations (3 hours)
```python
# backend/services/session_manager.py
import aioredis
from typing import Optional

class SessionManager:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.sessions = {}  # Fallback in-memory storage
    
    async def connect(self):
        try:
            self.redis = await aioredis.create_redis_pool(
                'redis://localhost:6379',
                minsize=5,
                maxsize=10
            )
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory storage")
    
    async def should_introduce(self, session_id: str) -> bool:
        if self.redis:
            exists = await self.redis.exists(f"session:{session_id}")
            if not exists:
                await self.redis.setex(f"session:{session_id}", 1800, "1")
                return True
            return False
        else:
            # Fallback to in-memory
            if session_id not in self.sessions:
                self.sessions[session_id] = datetime.now()
                return True
            return False
```

## Router Consolidation Strategy

### Consolidate 4 Routers into 1 (4 hours)
```python
# backend/services/ai_router_unified.py
from enum import Enum
from typing import Optional, Dict, Any

class RouterMode(Enum):
    SIMPLE = "simple"
    TOOLS = "tools"
    RESPONSES = "responses"
    STANDARD = "standard"

class UnifiedAIRouter:
    def __init__(self, mode: RouterMode = RouterMode.SIMPLE):
        self.mode = mode
        self.openai_client = None
        self.anthropic_client = None
        
    async def process_message(
        self,
        message: str,
        session_id: str,
        history: List[Dict] = None,
        reasoning_effort: str = "medium",
        verbosity: str = "medium",
        allowed_tools: Optional[List] = None,
        tool_choice: Optional[Dict] = None,
        **kwargs
    ):
        """Unified interface for all routing modes"""
        
        if self.mode == RouterMode.RESPONSES and allowed_tools:
            async for chunk in self._process_with_responses(
                message, session_id, history, 
                reasoning_effort, allowed_tools, tool_choice
            ):
                yield chunk
                
        elif self.mode == RouterMode.TOOLS and allowed_tools:
            async for chunk in self._process_with_tools(
                message, session_id, history, allowed_tools
            ):
                yield chunk
                
        else:  # SIMPLE or STANDARD
            async for chunk in self._process_simple(
                message, session_id, history
            ):
                yield chunk
    
    async def _process_simple(self, message, session_id, history):
        """Simple streaming without tools"""
        # Implementation from ai_router_simple.py
        pass
    
    async def _process_with_tools(self, message, session_id, history, tools):
        """Process with function calling"""
        # Implementation from ai_router_tools.py
        pass
    
    async def _process_with_responses(self, message, session_id, history, effort, tools, choice):
        """Process with Responses API"""
        # Implementation from ai_router_responses.py
        pass

# Update imports in agent_whisperer.py:
from services.ai_router_unified import UnifiedAIRouter, RouterMode
ai_router = UnifiedAIRouter(mode=RouterMode.RESPONSES if settings.OPENAI_USE_RESPONSES else RouterMode.SIMPLE)
```

## Testing Infrastructure Setup

### 1. Frontend Testing Setup (2 hours)
```bash
# Install testing dependencies
cd frontend
npm install --save-dev @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

```javascript
// frontend/jest.config.js
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'app/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  coverageThresholds: {
    global: {
      branches: 70,
      functions: 70,
      lines: 80,
      statements: 80,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
```

```javascript
// frontend/jest.setup.js
import '@testing-library/jest-dom'
```

### 2. Example Component Test
```typescript
// frontend/__tests__/components/ChatInterface.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChatInterface } from '@/components/chat-interface'

describe('ChatInterface', () => {
  it('renders input and send button', () => {
    render(<ChatInterface />)
    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })
  
  it('sends message on form submit', async () => {
    const mockFetch = jest.fn(() => 
      Promise.resolve({
        ok: true,
        body: {
          getReader: () => ({
            read: jest.fn()
              .mockResolvedValueOnce({ value: new TextEncoder().encode('0:"Hello"\n'), done: false })
              .mockResolvedValueOnce({ done: true })
          })
        }
      })
    )
    global.fetch = mockFetch
    
    render(<ChatInterface />)
    const input = screen.getByPlaceholderText(/type your message/i)
    const button = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Test message')
        })
      )
    })
  })
})
```

### 3. Backend Unit Test Example
```python
# backend/tests/unit/test_query_analyzer.py
import pytest
from services.query_analyzer import QueryAnalyzer, QueryType

class TestQueryAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return QueryAnalyzer()
    
    def test_greeting_detection(self, analyzer):
        query_type, params = analyzer.analyze_query("Hello there!")
        assert query_type == QueryType.GREETING
        assert params == {}
    
    def test_property_search_detection(self, analyzer):
        query_type, params = analyzer.analyze_query(
            "Find me a 3 bedroom house in Bondi under 2 million"
        )
        assert query_type == QueryType.PROPERTY_SEARCH
        assert params["bedrooms"] == 3
        assert params["suburb"] == "Bondi"
        assert params["max_price"] == 2000000
        assert params["property_type"] == "house"
    
    def test_web_search_explicit(self, analyzer):
        query_type, params = analyzer.analyze_query("use live sources for latest news")
        assert query_type == QueryType.WEB_SEARCH
        assert "query" in params
    
    def test_negation_handling(self, analyzer):
        query_type, params = analyzer.analyze_query("don't use live sources, just tell me")
        assert query_type != QueryType.WEB_SEARCH
    
    @pytest.mark.parametrize("query,expected_type", [
        ("What's the weather?", QueryType.WEATHER),
        ("What time is it?", QueryType.TIME),
        ("Latest property news", QueryType.NEWS),
        ("Calculate 5 + 3", QueryType.CALCULATION),
        ("How are you?", QueryType.GENERAL_CHAT),
    ])
    def test_query_classification(self, analyzer, query, expected_type):
        query_type, _ = analyzer.analyze_query(query)
        assert query_type == expected_type
```

## Dependency Injection Pattern

### Implement DI Container (4 hours)
```python
# backend/core/container.py
from typing import Dict, Any, Type
from functools import lru_cache

class ServiceContainer:
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
    
    def register_singleton(self, service_type: Type, instance: Any):
        """Register a singleton service"""
        self._services[service_type] = instance
    
    def register_factory(self, service_type: Type, factory: callable):
        """Register a factory function for creating services"""
        self._factories[service_type] = factory
    
    def get(self, service_type: Type) -> Any:
        """Get a service instance"""
        if service_type in self._services:
            return self._services[service_type]
        
        if service_type in self._factories:
            instance = self._factories[service_type]()
            self._services[service_type] = instance
            return instance
        
        raise ValueError(f"Service {service_type} not registered")

# backend/core/dependencies.py
from .container import ServiceContainer
from services.ai_router_unified import UnifiedAIRouter
from services.session_manager import SessionManager
from services.query_analyzer import QueryAnalyzer

@lru_cache()
def get_container() -> ServiceContainer:
    container = ServiceContainer()
    
    # Register factories
    container.register_factory(
        UnifiedAIRouter,
        lambda: UnifiedAIRouter(mode=RouterMode.RESPONSES if settings.OPENAI_USE_RESPONSES else RouterMode.SIMPLE)
    )
    
    container.register_factory(SessionManager, SessionManager)
    container.register_factory(QueryAnalyzer, QueryAnalyzer)
    
    return container

# Usage in API endpoints:
from fastapi import Depends
from core.dependencies import get_container
from core.container import ServiceContainer

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    container: ServiceContainer = Depends(get_container)
):
    ai_router = container.get(UnifiedAIRouter)
    query_analyzer = container.get(QueryAnalyzer)
    session_manager = container.get(SessionManager)
    
    # Use services...
```

## CI/CD Pipeline Setup

### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
      
      - name: Build
        run: |
          cd frontend
          npm run build

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Bandit security scan
        run: |
          pip install bandit
          bandit -r backend/ -f json -o bandit-report.json
      
      - name: Check for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
```

## Monitoring & Observability

### Add Application Performance Monitoring
```python
# backend/core/monitoring.py
import time
import logging
from contextlib import asynccontextmanager
from typing import Optional

class MetricsCollector:
    def __init__(self):
        self.metrics = {}
    
    @asynccontextmanager
    async def timer(self, operation: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.record_metric(f"{operation}_duration_ms", duration * 1000)
    
    def record_metric(self, name: str, value: float):
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)
        
        # Log for now, integrate with APM later
        logging.info(f"Metric: {name}={value:.2f}")

# Usage:
metrics = MetricsCollector()

async with metrics.timer("chat_request"):
    response = await process_chat(message)
```

## Common Pitfalls to Avoid

1. **Don't change SSE format** - Must remain `0:"content"\n` for Vercel AI SDK
2. **Don't break streaming** - Test with browser Network tab after changes
3. **Don't skip validation** - Always validate user input
4. **Don't ignore async** - Keep all I/O operations async
5. **Don't hardcode secrets** - Use environment variables
6. **Don't skip tests** - Write tests for critical paths
7. **Don't optimize prematurely** - Measure first, optimize second

## Rollback Procedures

### If Breaking Changes Occur:
1. **Streaming breaks**: Revert `utils/streaming.py` changes
2. **Auth breaks**: Temporarily set `REQUIRE_API_KEY=False`
3. **Performance degrades**: Disable new features via feature flags
4. **Frontend breaks**: Revert to previous Next.js build

### Feature Flags for Safe Deployment:
```python
# backend/config.py
class Settings(BaseSettings):
    # Feature flags
    USE_CONNECTION_POOLING: bool = Field(default=False, env="USE_CONNECTION_POOLING")
    USE_ASYNC_REDIS: bool = Field(default=False, env="USE_ASYNC_REDIS")
    USE_UNIFIED_ROUTER: bool = Field(default=False, env="USE_UNIFIED_ROUTER")
    ENABLE_MONITORING: bool = Field(default=False, env="ENABLE_MONITORING")
```

---
*Follow this guide for systematic improvements to the codebase*