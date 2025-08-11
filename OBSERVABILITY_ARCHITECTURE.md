# Enterprise Observability Architecture

## Overview

Comprehensive observability solution for ReAgent Sydney V03 using OpenTelemetry (OTel) standards for metrics, traces, and logs across frontend and backend systems.

## Architecture Principles

1. **Vendor-Agnostic**: OpenTelemetry standard for portability
2. **Zero-Impact Performance**: Async collection with minimal overhead
3. **Comprehensive Coverage**: Metrics, traces, logs, and custom events
4. **Progressive Enhancement**: Start simple, expand as needed
5. **Cost-Effective**: Smart sampling and data retention policies

## Three Pillars of Observability

### 1. Metrics (Time-Series Data)
- **System Metrics**: CPU, memory, disk, network
- **Application Metrics**: Request rate, error rate, latency
- **Business Metrics**: User engagement, feature adoption, conversion
- **Custom Metrics**: AI SDK performance, streaming metrics, migration progress

### 2. Traces (Request Flow)
- **Distributed Tracing**: Frontend → Backend → AI Services
- **Span Attributes**: User ID, session ID, SDK version, feature flags
- **Performance Profiling**: Identify bottlenecks and slow operations
- **Error Correlation**: Link errors across services

### 3. Logs (Event Data)
- **Structured Logging**: JSON format with consistent schema
- **Context Propagation**: Trace ID in every log entry
- **Log Levels**: ERROR, WARN, INFO, DEBUG with dynamic control
- **Retention Policy**: 7 days hot, 30 days warm, 90 days cold

## Technology Stack

### Core Components
```
┌─────────────────────────────────────────────────────────┐
│                    Applications                          │
├──────────────────┬────────────────┬────────────────────┤
│   Frontend       │    Backend     │   AI Services      │
│   (Next.js)      │   (FastAPI)    │  (OpenAI/Claude)   │
├──────────────────┴────────────────┴────────────────────┤
│              OpenTelemetry SDK & Auto-Instrumentation   │
├─────────────────────────────────────────────────────────┤
│                 OTel Collector (Gateway)                 │
├──────────────────┬────────────────┬────────────────────┤
│    Metrics       │    Traces      │      Logs          │
│  (Prometheus)    │    (Jaeger)    │   (Loki/ELK)       │
├──────────────────┴────────────────┴────────────────────┤
│                 Visualization & Alerting                 │
│                    (Grafana/DataDog)                     │
└─────────────────────────────────────────────────────────┘
```

### Frontend Instrumentation

#### Next.js Integration
```typescript
// lib/telemetry/frontend.ts
import { NodeSDK } from '@opentelemetry/sdk-node'
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics'
import { Resource } from '@opentelemetry/resources'
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions'

export const initTelemetry = () => {
  const resource = Resource.default().merge(
    new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: 'reagent-frontend',
      [SemanticResourceAttributes.SERVICE_VERSION]: process.env.NEXT_PUBLIC_VERSION,
      environment: process.env.NODE_ENV,
      region: process.env.VERCEL_REGION || 'unknown',
    })
  )

  // Metrics
  const metricReader = new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT,
    }),
    intervalMillis: 30000, // 30 seconds
  })

  // Traces
  const traceExporter = new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
  })

  // Initialize SDK
  const sdk = new NodeSDK({
    resource,
    traceExporter,
    metricReader,
    instrumentations: [
      new HttpInstrumentation(),
      new FetchInstrumentation(),
    ],
  })

  sdk.start()
}
```

#### Custom Metrics Collection
```typescript
// lib/telemetry/metrics.ts
export class TelemetryMetrics {
  private meter: Meter
  private counters: Map<string, Counter>
  private histograms: Map<string, Histogram>

  constructor() {
    this.meter = metrics.getMeter('reagent-frontend')
    this.initializeMetrics()
  }

  private initializeMetrics() {
    // AI SDK Metrics
    this.counters.set('ai_sdk_requests', this.meter.createCounter('ai.sdk.requests', {
      description: 'Total AI SDK requests',
    }))

    this.histograms.set('streaming_duration', this.meter.createHistogram('streaming.duration', {
      description: 'SSE streaming duration in milliseconds',
      unit: 'ms',
    }))

    // Migration Metrics
    this.counters.set('v5_migrations', this.meter.createCounter('migration.v5.attempts', {
      description: 'AI SDK v5 migration attempts',
    }))

    // User Interaction Metrics
    this.counters.set('chat_messages', this.meter.createCounter('chat.messages', {
      description: 'Total chat messages sent',
    }))
  }

  recordAIRequest(attributes: { 
    sdkVersion: string, 
    model: string, 
    success: boolean 
  }) {
    this.counters.get('ai_sdk_requests')?.add(1, attributes)
  }

  recordStreamingDuration(duration: number, attributes: {
    sdkVersion: string,
    protocol: string
  }) {
    this.histograms.get('streaming_duration')?.record(duration, attributes)
  }
}
```

### Backend Instrumentation

#### FastAPI Integration
```python
# backend/telemetry/setup.py
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

def init_telemetry(app):
    """Initialize OpenTelemetry for FastAPI application"""
    
    # Create resource
    resource = Resource.create({
        "service.name": "reagent-backend",
        "service.version": os.getenv("VERSION", "unknown"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "region": os.getenv("REGION", "sydney"),
    })
    
    # Setup tracing
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)
    
    # Setup metrics
    metrics.set_meter_provider(MeterProvider(resource=resource))
    meter = metrics.get_meter(__name__)
    
    # Configure exporters
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "false") == "true",
    )
    
    # Auto-instrumentation
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    LoggingInstrumentor().instrument()
    
    # Custom middleware for additional context
    @app.middleware("http")
    async def add_telemetry_context(request: Request, call_next):
        span = trace.get_current_span()
        
        # Add custom attributes
        span.set_attribute("user.session_id", request.headers.get("X-Session-ID", "unknown"))
        span.set_attribute("sdk.version", request.headers.get("X-SDK-Version", "v3"))
        span.set_attribute("feature.flags", json.dumps(get_feature_flags(request)))
        
        # Record metrics
        start_time = time.time()
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        
        request_duration.record(duration, {
            "method": request.method,
            "endpoint": request.url.path,
            "status": response.status_code,
        })
        
        return response
    
    return tracer, meter
```

#### Custom Spans and Metrics
```python
# backend/telemetry/instrumentation.py
from opentelemetry import trace, metrics
from contextlib import contextmanager

tracer = trace.get_tracer("reagent-backend")
meter = metrics.get_meter("reagent-backend")

# Create metrics
chat_counter = meter.create_counter(
    name="chat.messages",
    description="Total chat messages processed",
    unit="messages"
)

streaming_histogram = meter.create_histogram(
    name="streaming.chunk.size",
    description="Size of streaming chunks",
    unit="bytes"
)

ai_latency_histogram = meter.create_histogram(
    name="ai.request.latency",
    description="AI service request latency",
    unit="ms"
)

@contextmanager
def trace_operation(name: str, attributes: dict = None):
    """Context manager for tracing operations"""
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise

async def trace_ai_request(provider: str, model: str):
    """Trace AI service requests"""
    with trace_operation("ai.request", {
        "ai.provider": provider,
        "ai.model": model,
        "ai.streaming": True,
    }) as span:
        start_time = time.time()
        
        try:
            # AI request logic here
            response = await make_ai_request(provider, model)
            
            # Record metrics
            latency = (time.time() - start_time) * 1000
            ai_latency_histogram.record(latency, {
                "provider": provider,
                "model": model,
                "success": True,
            })
            
            span.set_attribute("ai.tokens.used", response.token_count)
            
            return response
            
        except Exception as e:
            ai_latency_histogram.record(
                (time.time() - start_time) * 1000,
                {"provider": provider, "model": model, "success": False}
            )
            raise
```

### Collector Configuration

#### OTel Collector Setup
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
        
  prometheus:
    config:
      scrape_configs:
        - job_name: 'reagent-metrics'
          scrape_interval: 30s
          static_configs:
            - targets: ['localhost:8000', 'localhost:3000']

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
    
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128
    
  resource:
    attributes:
      - key: environment
        value: production
        action: upsert
      - key: region
        value: sydney
        action: upsert
        
  tail_sampling:
    policies:
      - name: errors-policy
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: latency-policy
        type: latency
        latency: {threshold_ms: 1000}
      - name: probabilistic-policy
        type: probabilistic
        probabilistic: {sampling_percentage: 10}

exporters:
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true
      
  prometheus:
    endpoint: 0.0.0.0:8889
    
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    
  datadog:
    api:
      key: ${DD_API_KEY}
      site: datadoghq.com

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource, tail_sampling]
      exporters: [otlp/jaeger, datadog]
      
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, batch, resource]
      exporters: [prometheus, datadog]
      
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [loki, datadog]
```

## Key Metrics to Track

### System Health
- **Golden Signals**: Latency, Traffic, Errors, Saturation
- **Apdex Score**: Application Performance Index
- **SLI/SLO**: Service Level Indicators/Objectives

### AI SDK Migration
```typescript
// Migration-specific metrics
const migrationMetrics = {
  // Traffic distribution
  'migration.traffic.v3': Counter,
  'migration.traffic.v5': Counter,
  
  // Performance comparison
  'migration.ttfb.v3': Histogram,
  'migration.ttfb.v5': Histogram,
  'migration.streaming.duration.v3': Histogram,
  'migration.streaming.duration.v5': Histogram,
  
  // Error rates
  'migration.errors.v3': Counter,
  'migration.errors.v5': Counter,
  
  // Feature flag effectiveness
  'migration.rollback.triggered': Counter,
  'migration.feature.flag.changes': Counter,
}
```

### Business Metrics
```python
# Business KPIs
business_metrics = {
    'user.sessions.active': Gauge,
    'user.messages.sent': Counter,
    'property.searches': Counter,
    'property.views': Counter,
    'ai.tokens.consumed': Counter,
    'ai.cost.estimated': Gauge,
}
```

## Dashboards

### 1. System Overview Dashboard
- Request rate and latency (P50, P95, P99)
- Error rate and types
- Active users and sessions
- Resource utilization

### 2. AI SDK Migration Dashboard
- v3 vs v5 traffic split
- Performance comparison charts
- Error rate comparison
- Rollback triggers and events

### 3. Business Intelligence Dashboard
- User engagement metrics
- Feature adoption rates
- AI usage and costs
- Conversion funnels

### 4. Infrastructure Dashboard
- Vercel function performance
- Database query performance
- External API latencies
- Cache hit rates

## Alerting Rules

### Critical Alerts (Immediate)
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 2m
  annotations:
    summary: "Error rate above 5%"
    
- alert: ServiceDown
  expr: up{service="reagent-backend"} == 0
  for: 1m
  annotations:
    summary: "Backend service is down"
    
- alert: StreamingFailure
  expr: rate(streaming_errors_total[5m]) > 0.1
  for: 2m
  annotations:
    summary: "SSE streaming failures above threshold"
```

### Warning Alerts (Business Hours)
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
  for: 5m
  annotations:
    summary: "P95 latency above 1 second"
    
- alert: LowCacheHitRate
  expr: cache_hit_rate < 0.8
  for: 10m
  annotations:
    summary: "Cache hit rate below 80%"
```

### Info Alerts (Daily Report)
```yaml
- alert: HighAITokenUsage
  expr: increase(ai_tokens_total[24h]) > 1000000
  annotations:
    summary: "Daily AI token usage exceeds 1M"
    
- alert: MigrationProgress
  expr: migration_v5_traffic_percentage < 0.5
  annotations:
    summary: "v5 migration below 50% after deadline"
```

## Data Retention Policy

### Metrics
- **Raw**: 7 days (1-minute resolution)
- **5-minute**: 30 days
- **1-hour**: 90 days
- **1-day**: 365 days

### Traces
- **Full traces**: 24 hours
- **Sampled traces**: 7 days
- **Error traces**: 30 days

### Logs
- **ERROR**: 90 days
- **WARN**: 30 days
- **INFO**: 7 days
- **DEBUG**: 24 hours

## Cost Optimization

### Sampling Strategies
```yaml
sampling:
  # Sample 100% of errors
  errors: 1.0
  
  # Sample 10% of successful requests
  success: 0.1
  
  # Sample 50% of slow requests (>1s)
  slow: 0.5
  
  # Sample 1% of health checks
  health_checks: 0.01
```

### Data Compression
- Use protobuf for wire protocol
- Enable gzip compression
- Batch exports every 30 seconds
- Aggregate metrics at source

### Smart Routing
- Route different data types to appropriate backends
- Use cheaper storage for archived data
- Implement tiered storage strategy

## Implementation Phases

### Phase 1: Foundation (Week 7)
- [ ] Install OpenTelemetry SDKs
- [ ] Basic auto-instrumentation
- [ ] Local collector setup
- [ ] Basic metrics and traces

### Phase 2: Enhancement (Week 7)
- [ ] Custom instrumentation
- [ ] Migration-specific metrics
- [ ] Business metrics
- [ ] Basic dashboards

### Phase 3: Production (Week 8)
- [ ] Cloud collector deployment
- [ ] Full dashboard suite
- [ ] Alerting rules
- [ ] Runbook documentation

### Phase 4: Optimization (Week 8)
- [ ] Sampling strategies
- [ ] Cost optimization
- [ ] Performance tuning
- [ ] Team training

## Security Considerations

### Data Privacy
- No PII in metrics or traces
- Sanitize URLs and headers
- Encrypt data in transit
- Implement data masking

### Access Control
- Role-based dashboard access
- API key rotation
- Audit logging
- Secure collector endpoints

## Troubleshooting Guide

### Common Issues

#### High Memory Usage
```bash
# Check collector memory
curl http://localhost:8888/metrics | grep memory

# Adjust batch processor
# Reduce batch size or timeout
```

#### Missing Traces
```bash
# Verify exporter endpoint
curl -X POST http://localhost:4318/v1/traces

# Check sampling configuration
# Ensure trace propagation headers
```

#### Metric Gaps
```bash
# Check scrape targets
curl http://localhost:8889/targets

# Verify metric names and labels
```

## Team Runbook

### On-Call Procedures
1. Check system overview dashboard
2. Review recent alerts
3. Examine error traces
4. Check deployment timeline
5. Escalate if needed

### Investigation Tools
```bash
# Query traces by ID
curl "http://jaeger:16686/api/traces/{traceId}"

# Export metrics for analysis
curl "http://prometheus:9090/api/v1/query?query=up"

# Search logs by trace ID
curl "http://loki:3100/loki/api/v1/query?query={traceId=\"xyz\"}"
```

## Next Steps

1. Review and approve architecture
2. Set up development environment
3. Implement Phase 1 instrumentation
4. Deploy collector to staging
5. Create initial dashboards
6. Train team on observability tools