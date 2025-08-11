# ReAgent V3 - System Architecture Documentation
## Enterprise-Grade AI Real Estate Intelligence Platform

*Author: Senior Architectural DevOps Engineer*  
*Version: 3.0.0*  
*Last Updated: August 2025*  
*Classification: Production Architecture*

---

## Executive Summary

ReAgent V3 represents a production-ready, AI-powered real estate intelligence platform designed for the Sydney market. This document provides comprehensive architectural guidance for deploying, operating, and scaling the system in production environments.

### Key Architectural Decisions
- **Microservices-Ready Monolith**: Designed for future decomposition
- **Event-Driven Architecture**: SSE-based real-time communication
- **Cloud-Native Design**: Container-ready with horizontal scaling capabilities
- **AI-First Architecture**: Multi-model support with intelligent routing
- **Cache-Heavy Strategy**: Multi-layer caching for sub-second responses

### System Metrics & SLAs
- **Availability Target**: 99.9% (8.76 hours downtime/year)
- **Response Time**: <200ms (p50), <1s (p95), <3s (p99)
- **Throughput**: 1000 req/s sustained, 5000 req/s burst
- **Recovery Time Objective (RTO)**: 1 hour
- **Recovery Point Objective (RPO)**: 15 minutes

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer                            │
│                    (NGINX/ALB with SSL/TLS)                     │
└─────────────────┬───────────────────────────┬───────────────────┘
                  │                           │
         ┌────────▼────────┐         ┌───────▼────────┐
         │   Frontend CDN   │         │  API Gateway   │
         │  (CloudFlare)    │         │   (Kong/AWS)   │
         └────────┬────────┘         └───────┬────────┘
                  │                           │
         ┌────────▼────────┐         ┌───────▼────────┐
         │   Next.js App   │         │  FastAPI App   │
         │    (Port 3000)  │◄────────►│  (Port 8001)  │
         └─────────────────┘         └───────┬────────┘
                                             │
                  ┌──────────────────────────┼──────────────────────────┐
                  │                          │                          │
         ┌────────▼────────┐       ┌────────▼────────┐       ┌────────▼────────┐
         │   AI Services   │       │   Cache Layer   │       │   Data Layer    │
         │ OpenAI/Anthropic│       │     Redis       │       │   PostgreSQL    │
         └─────────────────┘       └─────────────────┘       └─────────────────┘
```

### 1.2 Component Architecture

```yaml
System Components:
  Frontend:
    Technology: Next.js 15 + React 19
    Deployment: Vercel/AWS Amplify/Self-hosted
    Features:
      - Server-side rendering (SSR)
      - Real-time SSE streaming
      - Progressive Web App (PWA) ready
      - Responsive design
  
  Backend:
    Technology: FastAPI + Python 3.11
    Pattern: Service-oriented architecture
    Features:
      - Async/await throughout
      - SSE streaming endpoints
      - Multi-model AI routing
      - Session management
      - Rate limiting
  
  Data Storage:
    Primary: PostgreSQL (future)
    Cache: Redis (optional)
    Session: In-memory (current)
    Files: Local filesystem
  
  AI Services:
    Primary: OpenAI GPT-4
    Secondary: Anthropic Claude
    Fallback: GPT-3.5-turbo
    Embeddings: OpenAI Ada (future)
```

### 1.3 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Next.js | 15.4.6 | React framework with SSR |
| | React | 19.1.1 | UI library |
| | Tailwind CSS | 3.4.1 | Styling framework |
| | Vercel AI SDK | 3.4.33 | AI streaming integration |
| | Framer Motion | 11.15.0 | Animations |
| **Backend** | FastAPI | 0.115.5 | Web framework |
| | Python | 3.11+ | Runtime |
| | Uvicorn | 0.32.1 | ASGI server |
| | Pydantic | 2.10.3 | Data validation |
| **AI/ML** | OpenAI SDK | 1.58.1 | GPT integration |
| | Anthropic SDK | 0.40.0 | Claude integration |
| **Infrastructure** | Docker | 24.0+ | Containerization |
| | NGINX | 1.25+ | Reverse proxy |
| | Redis | 7.0+ | Caching (optional) |
| | PostgreSQL | 16+ | Database (future) |

---

## 2. Infrastructure Design

### 2.1 Deployment Architecture

```yaml
Production Environment:
  Compute:
    Type: Container-based
    Orchestration: Docker Compose → Kubernetes
    Scaling: Horizontal auto-scaling
    
  Network:
    CDN: CloudFlare
    Load Balancer: NGINX/AWS ALB
    SSL/TLS: Let's Encrypt/AWS ACM
    DNS: Route53/CloudFlare
    
  Storage:
    Database: Managed PostgreSQL (RDS/Cloud SQL)
    Cache: Managed Redis (ElastiCache/Redis Cloud)
    Files: Object Storage (S3/GCS)
    
  Monitoring:
    Metrics: Prometheus + Grafana
    Logs: ELK Stack/CloudWatch
    Traces: OpenTelemetry/Jaeger
    APM: DataDog/New Relic
```

### 2.2 Container Architecture

```dockerfile
# Backend Container Structure
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
EXPOSE 8001
CMD ["uvicorn", "app_simple:app", "--host", "0.0.0.0", "--port", "8001"]

# Frontend Container Structure
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
EXPOSE 3000
CMD ["npm", "start"]
```

### 2.3 Resource Requirements

```yaml
Minimum Production Requirements:
  Backend:
    CPU: 2 vCPUs
    Memory: 4GB RAM
    Storage: 20GB SSD
    Instances: 2 (HA)
    
  Frontend:
    CPU: 1 vCPU
    Memory: 2GB RAM
    Storage: 10GB SSD
    Instances: 2 (HA)
    
  Database:
    CPU: 2 vCPUs
    Memory: 8GB RAM
    Storage: 100GB SSD
    IOPS: 3000
    
  Cache:
    Memory: 2GB
    Instances: 1 (2 for HA)

Recommended Production Setup:
  Backend: 4 vCPUs, 8GB RAM × 3 instances
  Frontend: 2 vCPUs, 4GB RAM × 3 instances
  Database: 4 vCPUs, 16GB RAM, 500GB SSD
  Cache: 4GB RAM × 2 instances
```

---

## 3. Component Deep Dive

### 3.1 Frontend Architecture

```typescript
// Component Structure
src/
├── app/                    # Next.js 15 app directory
│   ├── api/               # API routes
│   │   └── chat/         # SSE chat endpoint
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Landing page
├── components/            # React components
│   ├── chat-interface/   # Chat UI components
│   ├── effects/          # Visual effects
│   └── utils/            # Utility functions
└── lib/                  # Shared libraries
    ├── api/             # API client
    └── hooks/           # Custom React hooks

// Key Design Patterns
1. Server Components (RSC) for static content
2. Client Components for interactivity
3. Streaming SSR for optimal performance
4. Suspense boundaries for loading states
```

### 3.2 Backend Architecture

```python
# Service Layer Architecture
backend/
├── api/                   # API endpoints
│   ├── agent_whisperer.py   # Main chat endpoint
│   ├── health.py            # Health checks
│   └── metrics.py           # Metrics endpoint
├── services/              # Business logic
│   ├── ai_router.py        # AI model routing
│   ├── query_analyzer.py   # Query classification
│   ├── session_manager.py  # Session handling
│   └── property_search.py  # Property search logic
├── utils/                 # Utilities
│   ├── streaming.py        # SSE formatting
│   └── logging.py          # Structured logging
└── config.py             # Configuration management

# Key Design Patterns
1. Dependency Injection
2. Repository Pattern (future)
3. Service Layer Pattern
4. Async/Await throughout
5. Circuit Breaker (future)
```

### 3.3 AI Service Integration

```python
# Multi-Model Architecture
class AIRouter:
    """
    Intelligent routing between AI models based on:
    - Query complexity
    - Cost optimization
    - Model availability
    - Response time requirements
    """
    
    routing_strategy = {
        "simple_queries": "gpt-3.5-turbo",
        "complex_queries": "gpt-4-turbo",
        "real_estate_specific": "fine-tuned-model",
        "fallback": "gpt-3.5-turbo"
    }
    
    async def route_request(self, query: Query) -> Model:
        complexity = self.analyze_complexity(query)
        if complexity > 0.8:
            return self.use_advanced_model()
        return self.use_standard_model()
```

---

## 4. Data Flow Architecture

### 4.1 Request Flow

```
User Request → CDN → Load Balancer → Frontend → API Gateway → Backend
    ↓                                                            ↓
Browser Cache                                              AI Services
    ↑                                                            ↓
SSE Stream ← Frontend ← API Gateway ← Backend ← Response Processing
```

### 4.2 SSE Streaming Architecture

```python
# SSE Format (Critical for Vercel AI SDK compatibility)
def format_sse_chunk(content: str, chunk_type: str = "text") -> str:
    """
    Format: 
    - Text: 0:"content"\n
    - Finish: d:{"finishReason":"stop"}\n
    """
    if chunk_type == "text":
        return f'0:{json.dumps(content)}\n'
    elif chunk_type == "finish":
        return 'd:{"finishReason":"stop"}\n'
```

### 4.3 Caching Strategy

```yaml
Cache Layers:
  L1 - Browser Cache:
    TTL: 5 minutes
    Scope: Static assets, API responses
    
  L2 - CDN Cache:
    TTL: 1 hour
    Scope: Static content, images
    
  L3 - Application Cache:
    TTL: 15 minutes
    Scope: Session data, frequent queries
    
  L4 - Redis Cache:
    TTL: 1 hour
    Scope: AI responses, user sessions
    
  L5 - Database Cache:
    TTL: Permanent
    Scope: Historical data, analytics
```

---

## 5. Security Architecture

### 5.1 Security Layers

```yaml
Security Implementation:
  Network Security:
    - SSL/TLS encryption (TLS 1.3)
    - Web Application Firewall (WAF)
    - DDoS protection (CloudFlare)
    - IP whitelisting for admin endpoints
    
  Application Security:
    - CORS configuration
    - Rate limiting (60 req/min per IP)
    - Input validation (Pydantic)
    - SQL injection prevention
    - XSS protection
    - CSRF tokens
    
  API Security:
    - API key authentication
    - JWT tokens (future)
    - OAuth2 integration (future)
    - Request signing
    
  Data Security:
    - Encryption at rest
    - Encryption in transit
    - PII data masking
    - Audit logging
```

### 5.2 Security Best Practices

```python
# Environment Variable Management
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Never commit secrets
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Input Validation
from pydantic import BaseModel, validator

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(..., regex="^[a-zA-Z0-9-]+$")
    
    @validator('message')
    def sanitize_message(cls, v):
        # Remove potential injection attempts
        return v.strip().replace("<script>", "")
```

---

## 6. Performance Architecture

### 6.1 Performance Optimization

```yaml
Optimization Strategies:
  Backend:
    - Async/await for all I/O operations
    - Connection pooling for databases
    - Batch processing for bulk operations
    - Query optimization with indexes
    - Response compression (gzip)
    
  Frontend:
    - Code splitting
    - Lazy loading
    - Image optimization
    - Bundle size optimization
    - Service Worker caching
    
  API:
    - Response caching
    - Request deduplication
    - Parallel processing
    - Stream processing
    - Circuit breaker pattern
```

### 6.2 Performance Benchmarks

```yaml
Target Metrics:
  API Response Times:
    Health Check: <50ms
    Cached Responses: <100ms
    AI Responses: <3s first token
    Database Queries: <200ms
    
  Frontend Performance:
    First Contentful Paint: <1.5s
    Time to Interactive: <3.5s
    Largest Contentful Paint: <2.5s
    Cumulative Layout Shift: <0.1
    
  System Throughput:
    Concurrent Users: 50+
    Requests/Second: 1000
    WebSocket Connections: 500
    SSE Streams: 100
```

---

## 7. Monitoring & Observability Strategy

### 7.1 Monitoring Stack

```yaml
Monitoring Architecture:
  Metrics:
    Tool: Prometheus + Grafana
    Metrics:
      - Request rate
      - Response time
      - Error rate
      - AI token usage
      - Cache hit ratio
    
  Logging:
    Tool: ELK Stack / Loki
    Levels:
      - ERROR: System errors
      - WARN: Degraded performance
      - INFO: Request/response
      - DEBUG: Detailed tracing
    
  Tracing:
    Tool: OpenTelemetry + Jaeger
    Traces:
      - End-to-end request flow
      - AI model latency
      - Database query time
      - External API calls
    
  Alerting:
    Tool: AlertManager / PagerDuty
    Alerts:
      - Service down
      - High error rate (>1%)
      - Slow response (>5s)
      - Low disk space (<10%)
```

### 7.2 Key Metrics & SLIs

```python
# Application Metrics
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# AI metrics
ai_requests = Counter('ai_requests_total', 'Total AI API requests', ['provider', 'model'])
ai_tokens = Counter('ai_tokens_total', 'Total AI tokens used', ['provider', 'model'])
ai_latency = Histogram('ai_response_latency_seconds', 'AI response latency')

# Business metrics
active_sessions = Gauge('active_sessions', 'Number of active user sessions')
queries_processed = Counter('queries_processed_total', 'Total queries processed', ['type'])
```

### 7.3 Logging Strategy

```python
# Structured Logging Configuration
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Usage
logger = structlog.get_logger()
logger.info("api_request", 
    method="POST",
    endpoint="/chat",
    session_id=session_id,
    latency_ms=latency)
```

---

## 8. Deployment Strategy

### 8.1 Deployment Pipeline

```yaml
CI/CD Pipeline:
  Source Control:
    Platform: GitHub
    Branching: GitFlow
    Protected Branches: main, production
    
  Build Pipeline:
    1. Code Checkout
    2. Install Dependencies
    3. Run Linting (ESLint, Black)
    4. Run Tests (Jest, Pytest)
    5. Security Scan (Snyk, Dependabot)
    6. Build Docker Images
    7. Push to Registry
    
  Deployment Pipeline:
    1. Pull Docker Images
    2. Database Migrations
    3. Blue-Green Deployment
    4. Health Checks
    5. Smoke Tests
    6. Traffic Switch
    7. Rollback on Failure
```

### 8.2 Environment Configuration

```yaml
Environments:
  Development:
    URL: http://localhost:3000
    Database: SQLite/Local PostgreSQL
    AI Models: GPT-3.5 (cost optimization)
    Logging: DEBUG level
    
  Staging:
    URL: https://staging.reagent.com.au
    Database: Shared PostgreSQL
    AI Models: Production models
    Logging: INFO level
    
  Production:
    URL: https://reagent.com.au
    Database: Dedicated PostgreSQL cluster
    AI Models: GPT-4, Claude
    Logging: WARN level
    
Environment Variables:
  - NODE_ENV={development|staging|production}
  - API_BASE_URL
  - DATABASE_URL
  - REDIS_URL
  - OPENAI_API_KEY
  - SENTRY_DSN
  - LOG_LEVEL
```

### 8.3 Rollout Strategy

```yaml
Deployment Strategy:
  Type: Blue-Green with Canary
  
  Steps:
    1. Deploy to Green environment
    2. Run health checks
    3. Route 5% traffic (canary)
    4. Monitor for 15 minutes
    5. Route 25% traffic
    6. Monitor for 30 minutes
    7. Route 100% traffic
    8. Keep Blue for instant rollback
    
  Rollback Triggers:
    - Error rate >5%
    - Response time >5s (p95)
    - Health check failures
    - Memory usage >90%
```

---

## 9. Operational Runbooks

### 9.1 Service Startup

```bash
#!/bin/bash
# Service Startup Procedure

# 1. Check dependencies
check_dependencies() {
    echo "Checking PostgreSQL..."
    pg_isready -h localhost -p 5432
    
    echo "Checking Redis..."
    redis-cli ping
    
    echo "Checking API keys..."
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "ERROR: OPENAI_API_KEY not set"
        exit 1
    fi
}

# 2. Start services
start_services() {
    echo "Starting backend..."
    cd backend && uvicorn app_simple:app --host 0.0.0.0 --port 8001 &
    
    echo "Starting frontend..."
    cd frontend && npm start &
    
    echo "Waiting for services..."
    sleep 10
    
    # Health checks
    curl -f http://localhost:8001/health || exit 1
    curl -f http://localhost:3000 || exit 1
}

# 3. Run startup
check_dependencies
start_services
echo "ReAgent V3 started successfully"
```

### 9.2 Incident Response

```yaml
Incident Response Playbook:
  Severity Levels:
    P1 - Critical: Complete outage
    P2 - High: Major feature broken
    P3 - Medium: Minor feature issue
    P4 - Low: Cosmetic issue
    
  Response Times:
    P1: 15 minutes
    P2: 1 hour
    P3: 4 hours
    P4: Next business day
    
  Escalation Path:
    1. On-call engineer
    2. Team lead
    3. Engineering manager
    4. CTO
    
  Response Steps:
    1. Acknowledge incident
    2. Assess impact
    3. Communicate status
    4. Implement fix
    5. Verify resolution
    6. Post-mortem
```

### 9.3 Common Issues & Solutions

```yaml
Troubleshooting Guide:
  High Memory Usage:
    Symptoms: OOM errors, slow response
    Diagnosis: Check memory metrics
    Solution:
      - Increase memory limits
      - Optimize query patterns
      - Implement pagination
      - Clear session cache
    
  Slow API Response:
    Symptoms: >5s response time
    Diagnosis: Check AI latency, database queries
    Solution:
      - Enable response caching
      - Optimize AI prompts
      - Add database indexes
      - Scale horizontally
    
  SSE Connection Drops:
    Symptoms: Chat stops updating
    Diagnosis: Check network logs
    Solution:
      - Implement reconnection logic
      - Increase timeout values
      - Check proxy configuration
      - Enable keep-alive
    
  AI Rate Limits:
    Symptoms: 429 errors from OpenAI
    Diagnosis: Check token usage
    Solution:
      - Implement backoff strategy
      - Use multiple API keys
      - Cache AI responses
      - Optimize prompt length
```

---

## 10. Disaster Recovery Plan

### 10.1 Backup Strategy

```yaml
Backup Configuration:
  Database:
    Type: Automated snapshots
    Frequency: Every 6 hours
    Retention: 30 days
    Location: Cross-region S3
    
  Application State:
    Type: Redis persistence
    Frequency: Every hour
    Retention: 7 days
    
  Configuration:
    Type: Git repository
    Frequency: On change
    Retention: Forever
    
  Logs:
    Type: Log aggregation
    Frequency: Real-time
    Retention: 90 days
```

### 10.2 Recovery Procedures

```bash
#!/bin/bash
# Disaster Recovery Procedure

# 1. Database Recovery
restore_database() {
    echo "Restoring database from snapshot..."
    pg_restore -h localhost -d reagent_restore backup_latest.sql
    
    echo "Verifying data integrity..."
    psql -h localhost -d reagent_restore -c "SELECT COUNT(*) FROM sessions;"
}

# 2. Application Recovery
restore_application() {
    echo "Pulling latest stable images..."
    docker pull reagent/backend:stable
    docker pull reagent/frontend:stable
    
    echo "Starting services..."
    docker-compose -f docker-compose.recovery.yml up -d
}

# 3. Verification
verify_recovery() {
    echo "Running health checks..."
    ./health_check.sh
    
    echo "Running smoke tests..."
    pytest tests/smoke/
}

# Execute recovery
restore_database
restore_application
verify_recovery
```

---

## 11. Scaling Strategy

### 11.1 Horizontal Scaling

```yaml
Scaling Triggers:
  CPU-based:
    Scale Up: >70% for 5 minutes
    Scale Down: <30% for 10 minutes
    
  Memory-based:
    Scale Up: >80% for 5 minutes
    Scale Down: <40% for 10 minutes
    
  Request-based:
    Scale Up: >1000 req/min
    Scale Down: <200 req/min
    
  Custom Metrics:
    AI Queue Length: >10 pending
    SSE Connections: >80% capacity
    Database Connections: >80% pool
```

### 11.2 Database Scaling

```sql
-- Partitioning Strategy
CREATE TABLE chat_messages (
    id SERIAL,
    session_id VARCHAR(50),
    message TEXT,
    created_at TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE chat_messages_2025_08 
    PARTITION OF chat_messages
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');

-- Indexes for performance
CREATE INDEX idx_session_created 
    ON chat_messages(session_id, created_at);
CREATE INDEX idx_created_at 
    ON chat_messages(created_at);
```

---

## 12. Cost Optimization

### 12.1 Resource Optimization

```yaml
Cost Optimization Strategies:
  Compute:
    - Use spot instances for non-critical workloads
    - Implement auto-scaling with conservative thresholds
    - Right-size instances based on actual usage
    - Use ARM-based instances (Graviton)
    
  Storage:
    - Implement data lifecycle policies
    - Use object storage for cold data
    - Compress logs and backups
    - Clean up unused snapshots
    
  Network:
    - Use CDN for static assets
    - Implement aggressive caching
    - Minimize cross-region traffic
    - Use private endpoints
    
  AI/ML:
    - Cache AI responses aggressively
    - Use smaller models for simple queries
    - Implement prompt optimization
    - Batch API requests when possible
```

### 12.2 Cost Monitoring

```python
# Cost Tracking Implementation
class CostTracker:
    def __init__(self):
        self.metrics = {
            'ai_tokens': Counter('ai_tokens_used', 'AI tokens consumed'),
            'api_calls': Counter('external_api_calls', 'External API calls'),
            'compute_hours': Counter('compute_hours', 'Compute hours used'),
        }
    
    def track_ai_usage(self, tokens: int, model: str, cost_per_1k: float):
        cost = (tokens / 1000) * cost_per_1k
        self.metrics['ai_tokens'].inc(tokens)
        logger.info("ai_cost", tokens=tokens, model=model, cost=cost)
        
        # Alert if daily budget exceeded
        if self.get_daily_cost() > DAILY_BUDGET:
            self.trigger_cost_alert()
```

---

## 13. Compliance & Governance

### 13.1 Data Governance

```yaml
Data Classification:
  Public:
    - Property listings
    - Suburb statistics
    - Market trends
    
  Internal:
    - User sessions
    - Search queries
    - Analytics data
    
  Confidential:
    - User credentials
    - API keys
    - Personal information
    
  Restricted:
    - Payment information
    - Government IDs
    - Financial records
```

### 13.2 Compliance Requirements

```yaml
Regulatory Compliance:
  Privacy:
    - GDPR compliance (EU users)
    - Privacy Act 1988 (Australian users)
    - Cookie consent implementation
    - Data retention policies
    
  Security:
    - ISO 27001 alignment
    - OWASP Top 10 mitigation
    - Regular security audits
    - Penetration testing
    
  Industry:
    - Real estate regulations
    - Fair trading requirements
    - Anti-discrimination laws
    - Consumer protection
```

---

## 14. Future Architecture Roadmap

### 14.1 Evolution Path

```yaml
Phase 1 - Current (Q3 2025):
  - Monolithic deployment
  - Basic AI integration
  - Manual scaling
  - Single region
  
Phase 2 - Microservices (Q4 2025):
  - Service decomposition
  - Container orchestration (K8s)
  - Advanced caching
  - Multi-region support
  
Phase 3 - ML Platform (Q1 2026):
  - Custom ML models
  - Vector database integration
  - Real-time analytics
  - Predictive features
  
Phase 4 - Enterprise (Q2 2026):
  - Multi-tenant architecture
  - White-label support
  - Advanced integrations
  - Global deployment
```

### 14.2 Technology Upgrades

```yaml
Planned Upgrades:
  Infrastructure:
    - Kubernetes orchestration
    - Service mesh (Istio)
    - GitOps deployment
    - Multi-cloud support
    
  Data Platform:
    - Data lake implementation
    - Stream processing (Kafka)
    - Real-time analytics
    - ML feature store
    
  AI/ML:
    - Fine-tuned models
    - RAG implementation
    - Agent orchestration
    - AutoML pipeline
```

---

## Appendix A: Configuration Templates

### Docker Compose Production

```yaml
version: '3.8'

services:
  backend:
    image: reagent/backend:${VERSION:-latest}
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  frontend:
    image: reagent/frontend:${VERSION:-latest}
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_BACKEND_URL=http://backend:8001
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 2G
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
```

### NGINX Configuration

```nginx
upstream backend {
    least_conn;
    server backend:8001 max_fails=3 fail_timeout=30s;
}

upstream frontend {
    least_conn;
    server frontend:3000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    listen [::]:80;
    server_name reagent.com.au;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name reagent.com.au;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # API routes
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE specific
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }
    
    # Frontend routes
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## Appendix B: Performance Tuning

### Database Optimization

```sql
-- Connection pool settings
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET work_mem = '16MB';

-- Query optimization
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET default_statistics_target = 100;

-- Write performance
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET max_wal_size = '4GB';
```

### Application Optimization

```python
# Connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)

# Async optimization
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

async def optimized_handler(request):
    # Parallel I/O operations
    results = await asyncio.gather(
        fetch_from_cache(request.session_id),
        fetch_user_data(request.user_id),
        prepare_ai_context(request.message)
    )
    
    # Process results
    return process_results(results)
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 3.0.0 | Aug 2025 | Sr. DevOps Engineer | Initial comprehensive architecture |
| 3.0.1 | Aug 2025 | - | Added cost optimization section |
| 3.0.2 | Aug 2025 | - | Enhanced security architecture |

---

*This document represents the complete architectural blueprint for ReAgent V3. It should be reviewed quarterly and updated based on operational learnings and technological advances.*