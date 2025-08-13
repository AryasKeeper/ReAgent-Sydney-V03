# ReAgent Sydney V03 - 72-Hour Spike Deployment Guide

## 🎯 Executive Summary

This 72-hour spike delivers a production-ready real estate intelligence platform for Sydney with enterprise-grade architecture:

- **PostgreSQL + pgvector** for semantic search
- **Rolling partitions** for automatic data lifecycle management
- **JWT authentication** with token expiry and reconnection handling
- **Comprehensive security** with CSP, security headers, and environment lockdown
- **ECS Fargate ready** for ap-southeast-2 deployment
- **SSE streaming** preserving exact Vercel AI SDK compatibility (`0:` format)

## 🚀 Quick Start

### 1. Local Development Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Set up development environment
cp env.example .env
# Edit .env with your development settings

# Run database migrations
alembic upgrade head

# Start development server
python app_spike.py
```

### 2. Staging Deployment

```bash
# Copy staging environment
cp env.staging.example .env.staging

# Set REQUIRED staging variables:
export ENVIRONMENT=staging
export API_KEY=your_staging_api_key
export JWT_SECRET_KEY=your_jwt_secret_32_chars_minimum
export DATABASE_URL=postgresql://user:pass@staging-db:5432/reagent

# Start staging server
ENVIRONMENT=staging python app_spike.py
```

### 3. Production ECS Deployment

```bash
# Build and push Docker image
docker build -f Dockerfile.spike -t reagent-sydney-v03:spike .
docker tag reagent-sydney-v03:spike ACCOUNT.dkr.ecr.ap-southeast-2.amazonaws.com/reagent-sydney-v03:spike
docker push ACCOUNT.dkr.ecr.ap-southeast-2.amazonaws.com/reagent-sydney-v03:spike

# Deploy to ECS Fargate
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
aws ecs update-service --cluster reagent-cluster --service reagent-service --task-definition reagent-sydney-v03-spike
```

## 🔒 Security Features

### Hard-Locked Settings

The following settings are **hard-locked** and cannot be overridden in staging/production:

- `DEBUG=False` (enforced in code)
- `REQUIRE_API_KEY=True` (enforced in code)
- `USE_MOCK=False` (enforced in code)

### Security Headers

Automatically applied to all responses:

- `Content-Security-Policy` (environment-specific)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security` (HTTPS only)
- `Permissions-Policy` (restrictive)
- `Referrer-Policy: strict-origin-when-cross-origin`

### Environment Validation

The application **will not start** if critical security requirements are missing:

#### Staging Requirements
- `API_KEY` must be set
- `DATABASE_URL` must be set
- `JWT_SECRET_KEY` must be set

#### Production Requirements
- All staging requirements PLUS:
- `ADMIN_API_KEY` must be set
- `JWT_SECRET_KEY` must be ≥32 characters
- `DATABASE_URL` cannot contain "password" (prevents default passwords)

## 📊 Database Architecture

### Rolling Partitions

Automatic monthly partitions for:
- `agent_interactions` - Chat history and agent responses
- `vector_embeddings` - Semantic search vectors (1536-dim)
- `property_listings` - Property data with geospatial indexing
- `api_usage` - Request tracking and analytics

### Partition Management

- **Auto-creation**: Current and next month partitions
- **Cleanup**: 6-month retention by default
- **Scheduling**: Daily verification, monthly creation, weekly cleanup
- **Health monitoring**: `/api/v1/diagnostics` endpoint

### pgvector Integration

- `text-embedding-3-small` model (1536 dimensions)
- IVFFlat indexing for performance
- Cosine similarity search
- Automatic index creation per partition

## 🧪 Testing

### Connection Cleanup Tests

```bash
# Run backfill and reconnect tests
pytest tests/test_backfill_reconnect.py -v

# Run connection cleanup tests  
pytest tests/test_streaming.py::TestStreamingWithCleanup -v

# Run all tests with connection monitoring
pytest tests/ --connection-cleanup
```

### Security Tests

```bash
# Test security headers
curl -I http://localhost:8001/api/v1/health

# Test CSP
curl http://localhost:8001/api/v1/security/csp-test

# Test environment lockdown
ENVIRONMENT=staging DEBUG=true python app_spike.py  # Should fail
```

## 📡 API Endpoints

### Core Endpoints

- `GET /` - Service information
- `GET /api/v1/health` - Health check
- `POST /api/v1/agent-whisperer/chat/stream` - Chat streaming (SSE)

### Monitoring Endpoints

- `GET /api/v1/diagnostics` - System diagnostics  
- `GET /api/v1/security/health` - Security health check
- `GET /api/v1/security/headers-report` - Security headers config

### SSE Format (CRITICAL)

The exact SSE format is preserved for Vercel AI SDK compatibility:

```
0:"Hello"
0:" world"
d:{"finishReason":"stop"}
```

**Never modify this format** - it's sacred for frontend compatibility.

## 🚀 Deployment Verification

After deployment, verify these endpoints:

1. **Health Check**: `GET /api/v1/health` → 200 OK
2. **Security Status**: `GET /api/v1/security/health` → "secure" status
3. **Partition Health**: `GET /api/v1/diagnostics` → partition status "healthy"
4. **Chat Streaming**: `POST /api/v1/agent-whisperer/chat/stream` → SSE format correct

### Performance Targets

- **API Response Time**: <500ms
- **Database Queries**: <200ms
- **Partition Operations**: <5s
- **Memory Usage**: <1GB (Fargate limit)
- **CPU Usage**: <80% under load

## 🔧 Configuration

### Required Environment Variables

#### All Environments
```bash
ENVIRONMENT=development|staging|production
DATABASE_URL=postgresql://...
```

#### Staging + Production
```bash
API_KEY=your_api_key
JWT_SECRET_KEY=your_secret_key_32_chars_min
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

#### Production Only
```bash
ADMIN_API_KEY=your_admin_key
```

### Optional Configuration
```bash
TAVILY_API_KEY=tvly-...
FIRECRAWL_API_KEY=fc-...
REDIS_URL=redis://...
BACKEND_URL=https://api.reagent.properties
```

## 🎬 Architecture Decisions

### 1. PostgreSQL + pgvector (vs Qdrant)
- **Reason**: Simpler deployment, fewer moving parts
- **Trade-off**: Single-node vs distributed vector DB
- **Migration Path**: Can migrate to Qdrant later if needed

### 2. Rolling Partitions
- **Reason**: Automatic data lifecycle, performance at scale
- **Benefit**: 6-month retention, automatic cleanup
- **Operations**: Zero-maintenance partition management

### 3. Hard-Locked Security
- **Reason**: Prevent configuration drift in production
- **Method**: Code-level enforcement, not just env vars
- **Validation**: Startup-time validation with failure

### 4. ECS Fargate (ap-southeast-2)
- **Reason**: Regional optimization for Sydney users
- **Benefit**: <50ms latency to Sydney-based clients
- **Scaling**: Auto-scaling based on CPU/memory

## 🔍 Troubleshooting

### Common Issues

1. **Startup fails with security error**
   ```
   Critical security configuration issues prevent startup
   ```
   → Check required environment variables are set

2. **Database connection fails**
   ```
   Database connection unsuccessful
   ```
   → Verify DATABASE_URL and network connectivity

3. **Partition worker fails**
   ```
   Partition worker startup failed
   ```
   → Check database permissions for CREATE TABLE

4. **SSE format incorrect**
   ```
   Frontend not receiving expected format
   ```
   → Verify `utils/streaming.py` not modified

### Monitoring

- **Logs**: CloudWatch logs at `/ecs/reagent-sydney-v03`
- **Metrics**: ECS service metrics + custom application metrics
- **Health**: Built-in health checks with 30s interval
- **Alerts**: Configure CloudWatch alarms for failure scenarios

## 🎯 Success Criteria

This spike is considered successful when:

- ✅ Application starts in all environments (dev/staging/prod)
- ✅ Security validation prevents insecure configurations
- ✅ Database partitions create and clean up automatically
- ✅ JWT tokens expire and reconnect properly
- ✅ Connection cleanup prevents resource leaks
- ✅ Security headers applied to all responses
- ✅ SSE streaming maintains exact format compatibility
- ✅ ECS deployment completes successfully
- ✅ Performance targets met (<500ms API, <200ms DB)

## 📋 Next Steps (Post-Spike)

1. **Performance Optimization**
   - Redis session storage
   - CDN for static assets
   - Database query optimization

2. **Observability**
   - OpenTelemetry instrumentation
   - Distributed tracing
   - Custom metrics dashboard

3. **Advanced Features**
   - Vector similarity search UI
   - Agent orchestration with LangGraph
   - Real-time property notifications

4. **Scaling**
   - Multi-AZ deployment
   - Auto-scaling policies
   - Database read replicas

---

**Deployment Target**: ECS Fargate, ap-southeast-2  
**Go-Live Ready**: Yes, with production environment variables  
**72-Hour Spike Status**: ✅ COMPLETE