# ReAgent V3 - DevOps Operational Playbook
## Production Operations Guide for Engineering Teams

*Version: 1.0.0*  
*Last Updated: August 2025*  
*Audience: DevOps Engineers, SREs, Platform Teams*

---

## Quick Reference

### Critical URLs & Endpoints
```yaml
Production:
  Application: https://reagent.com.au
  API: https://api.reagent.com.au
  Health: https://api.reagent.com.au/health
  Metrics: https://metrics.reagent.com.au
  Logs: https://logs.reagent.com.au

Monitoring:
  Grafana: https://grafana.reagent.com.au
  Prometheus: https://prometheus.reagent.com.au
  AlertManager: https://alerts.reagent.com.au
```

### Emergency Contacts
```yaml
On-Call Rotation:
  Primary: +61-XXX-XXX-XXX
  Secondary: +61-XXX-XXX-XXX
  Escalation: engineering-oncall@reagent.com.au

Vendor Support:
  OpenAI: support@openai.com
  AWS: Premium Support Console
  CloudFlare: Enterprise Dashboard
```

---

## 1. Infrastructure as Code

### 1.1 Terraform Configuration

```hcl
# main.tf - AWS Infrastructure
terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket = "reagent-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "ap-southeast-2"
  }
}

provider "aws" {
  region = "ap-southeast-2"
  default_tags {
    tags = {
      Environment = "production"
      Project     = "reagent-v3"
      ManagedBy   = "terraform"
    }
  }
}

# VPC Configuration
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "reagent-prod-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["ap-southeast-2a", "ap-southeast-2b", "ap-southeast-2c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
  enable_dns_hostnames = true
  enable_dns_support = true
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "reagent-prod-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs.name
      }
    }
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "reagent-prod-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = module.vpc.public_subnets
  
  enable_deletion_protection = true
  enable_http2              = true
  enable_cross_zone_load_balancing = true
  
  tags = {
    Name = "reagent-prod-alb"
  }
}

# RDS Database
resource "aws_db_instance" "postgres" {
  identifier = "reagent-prod-db"
  
  engine         = "postgres"
  engine_version = "16.1"
  instance_class = "db.r6g.large"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type         = "gp3"
  storage_encrypted    = true
  
  db_name  = "reagent"
  username = "reagent_admin"
  password = var.db_password  # From AWS Secrets Manager
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  multi_az               = true
  deletion_protection    = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "reagent-prod-db-final-${timestamp()}"
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "reagent-prod-redis"
  replication_group_description = "Redis cache for ReAgent"
  
  engine               = "redis"
  engine_version       = "7.0"
  node_type           = "cache.r6g.large"
  number_cache_clusters = 2
  
  parameter_group_name = "default.redis7"
  port                = 6379
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = var.redis_auth_token
  
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  snapshot_retention_limit = 7
  snapshot_window         = "03:00-05:00"
  
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type        = "slow-log"
  }
}
```

### 1.2 Kubernetes Manifests

```yaml
# deployment.yaml - Backend Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reagent-backend
  namespace: production
  labels:
    app: reagent
    component: backend
    version: v3
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: reagent
      component: backend
  template:
    metadata:
      labels:
        app: reagent
        component: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8001"
        prometheus.io/path: "/metrics"
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - reagent
              - key: component
                operator: In
                values:
                - backend
            topologyKey: kubernetes.io/hostname
      containers:
      - name: backend
        image: reagent/backend:v3.0.0
        ports:
        - containerPort: 8001
          name: http
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: reagent-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: reagent-secrets
              key: redis-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: reagent-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: reagent-config

---
# service.yaml - Backend Service
apiVersion: v1
kind: Service
metadata:
  name: reagent-backend
  namespace: production
  labels:
    app: reagent
    component: backend
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8001
    protocol: TCP
    name: http
  selector:
    app: reagent
    component: backend

---
# hpa.yaml - Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: reagent-backend-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: reagent-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
```

---

## 2. Deployment Procedures

### 2.1 Blue-Green Deployment

```bash
#!/bin/bash
# blue-green-deploy.sh - Zero-downtime deployment

set -euo pipefail

# Configuration
BLUE_ENV="reagent-blue"
GREEN_ENV="reagent-green"
HEALTH_CHECK_URL="https://api.reagent.com.au/health"
ROLLBACK_TIMEOUT=300

# Functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

check_health() {
    local env=$1
    local url="${2:-$HEALTH_CHECK_URL}"
    
    for i in {1..30}; do
        if curl -f -s "$url" > /dev/null; then
            log "Health check passed for $env"
            return 0
        fi
        log "Health check attempt $i/30 failed for $env"
        sleep 10
    done
    
    log "Health check failed for $env"
    return 1
}

get_active_env() {
    kubectl get service reagent-active -o jsonpath='{.spec.selector.deployment}'
}

# Main deployment flow
main() {
    local VERSION=${1:-latest}
    local ACTIVE_ENV=$(get_active_env)
    local INACTIVE_ENV
    
    if [ "$ACTIVE_ENV" == "$BLUE_ENV" ]; then
        INACTIVE_ENV=$GREEN_ENV
    else
        INACTIVE_ENV=$BLUE_ENV
    fi
    
    log "Starting deployment of version $VERSION"
    log "Active environment: $ACTIVE_ENV"
    log "Deploying to: $INACTIVE_ENV"
    
    # Step 1: Deploy to inactive environment
    log "Deploying to $INACTIVE_ENV..."
    kubectl set image deployment/$INACTIVE_ENV \
        backend=reagent/backend:$VERSION \
        frontend=reagent/frontend:$VERSION \
        -n production
    
    # Step 2: Wait for rollout
    log "Waiting for rollout to complete..."
    kubectl rollout status deployment/$INACTIVE_ENV -n production
    
    # Step 3: Run health checks
    log "Running health checks..."
    if ! check_health "$INACTIVE_ENV"; then
        log "ERROR: Health check failed. Aborting deployment."
        exit 1
    fi
    
    # Step 4: Run smoke tests
    log "Running smoke tests..."
    pytest tests/smoke/ --env=$INACTIVE_ENV
    
    # Step 5: Switch traffic (canary first)
    log "Starting canary deployment (10% traffic)..."
    kubectl patch service reagent-active \
        -p '{"spec":{"selector":{"deployment":"'$INACTIVE_ENV'","canary":"true"}}}' \
        -n production
    
    sleep 60
    
    # Check metrics
    ERROR_RATE=$(prometheus_query 'rate(http_requests_total{status=~"5.."}[1m])')
    if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
        log "ERROR: High error rate detected. Rolling back..."
        kubectl patch service reagent-active \
            -p '{"spec":{"selector":{"deployment":"'$ACTIVE_ENV'"}}}' \
            -n production
        exit 1
    fi
    
    # Step 6: Full traffic switch
    log "Switching all traffic to $INACTIVE_ENV..."
    kubectl patch service reagent-active \
        -p '{"spec":{"selector":{"deployment":"'$INACTIVE_ENV'"}}}' \
        -n production
    
    log "Deployment successful! New active environment: $INACTIVE_ENV"
    
    # Step 7: Keep old environment for rollback
    log "Keeping $ACTIVE_ENV available for quick rollback"
}

# Execute deployment
main "$@"
```

### 2.2 Rollback Procedure

```bash
#!/bin/bash
# rollback.sh - Emergency rollback procedure

set -euo pipefail

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ROLLBACK: $1"
}

# Get current and previous environments
CURRENT_ENV=$(kubectl get service reagent-active -o jsonpath='{.spec.selector.deployment}')
if [ "$CURRENT_ENV" == "reagent-blue" ]; then
    PREVIOUS_ENV="reagent-green"
else
    PREVIOUS_ENV="reagent-blue"
fi

log "Rolling back from $CURRENT_ENV to $PREVIOUS_ENV"

# Step 1: Immediate traffic switch
log "Switching traffic to previous environment..."
kubectl patch service reagent-active \
    -p '{"spec":{"selector":{"deployment":"'$PREVIOUS_ENV'"}}}' \
    -n production

# Step 2: Verify health
log "Verifying health of rollback environment..."
for i in {1..10}; do
    if curl -f -s https://api.reagent.com.au/health > /dev/null; then
        log "Health check passed"
        break
    fi
    sleep 5
done

# Step 3: Alert team
log "Sending rollback notification..."
curl -X POST https://hooks.slack.com/services/XXX/YYY/ZZZ \
    -H 'Content-Type: application/json' \
    -d '{
        "text": "⚠️ PRODUCTION ROLLBACK EXECUTED",
        "attachments": [{
            "color": "danger",
            "fields": [
                {"title": "From", "value": "'$CURRENT_ENV'", "short": true},
                {"title": "To", "value": "'$PREVIOUS_ENV'", "short": true},
                {"title": "Time", "value": "'$(date)'", "short": false}
            ]
        }]
    }'

log "Rollback completed successfully"
```

---

## 3. Monitoring Setup

### 3.1 Prometheus Configuration

```yaml
# prometheus.yml - Prometheus configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: 'production'
    region: 'ap-southeast-2'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Load rules
rule_files:
  - "alerts/*.yml"

# Scrape configurations
scrape_configs:
  # Backend metrics
  - job_name: 'reagent-backend'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - production
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

  # Node exporter
  - job_name: 'node-exporter'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

  # PostgreSQL exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'pg_.*'
        action: keep

  # Redis exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 3.2 Alert Rules

```yaml
# alerts/reagent-alerts.yml - Critical alerts
groups:
  - name: reagent_critical
    interval: 30s
    rules:
      # Service availability
      - alert: ServiceDown
        expr: up{job="reagent-backend"} == 0
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "ReAgent backend is down"
          description: "{{ $labels.instance }} has been down for more than 2 minutes"
          runbook: https://wiki.reagent.com.au/runbooks/service-down

      # High error rate
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"
          runbook: https://wiki.reagent.com.au/runbooks/high-error-rate

      # API latency
      - alert: HighAPILatency
        expr: |
          histogram_quantile(0.95, 
            rate(http_request_duration_seconds_bucket[5m])
          ) > 3
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High API latency detected"
          description: "95th percentile latency is {{ $value }}s"

      # Database connection pool
      - alert: DatabaseConnectionPoolExhausted
        expr: |
          postgresql_connections_active / postgresql_connections_max > 0.9
        for: 5m
        labels:
          severity: critical
          team: database
        annotations:
          summary: "Database connection pool near exhaustion"
          description: "{{ $value | humanizePercentage }} of connections in use"

      # AI token usage
      - alert: HighAITokenUsage
        expr: |
          rate(ai_tokens_total[1h]) > 100000
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High AI token consumption"
          description: "Using {{ $value }} tokens per hour"

      # Memory usage
      - alert: HighMemoryUsage
        expr: |
          container_memory_usage_bytes{pod=~"reagent-.*"} 
          / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High memory usage in {{ $labels.pod }}"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # Disk space
      - alert: LowDiskSpace
        expr: |
          node_filesystem_avail_bytes{mountpoint="/"} 
          / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Only {{ $value | humanizePercentage }} disk space remaining"
```

### 3.3 Grafana Dashboards

```json
{
  "dashboard": {
    "title": "ReAgent V3 - Operations Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[5m])",
          "legendFormat": "{{ method }} {{ endpoint }}"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "title": "Response Time (p50, p95, p99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p99"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
          "legendFormat": "5xx Errors"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "title": "AI Token Usage",
        "targets": [{
          "expr": "rate(ai_tokens_total[1h])",
          "legendFormat": "{{ provider }} - {{ model }}"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      },
      {
        "title": "Active Sessions",
        "targets": [{
          "expr": "active_sessions",
          "legendFormat": "Sessions"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
      },
      {
        "title": "Database Connections",
        "targets": [{
          "expr": "postgresql_connections_active",
          "legendFormat": "Active Connections"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
      }
    ]
  }
}
```

---

## 4. Troubleshooting Guide

### 4.1 Common Issues

#### High Memory Usage

```bash
#!/bin/bash
# diagnose-memory.sh - Memory diagnostics

# Check container memory
kubectl top pods -n production | grep reagent

# Get memory dump
POD=$(kubectl get pods -n production -l app=reagent,component=backend -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n production $POD -- python -c "
import tracemalloc
import gc
tracemalloc.start()
# ... application code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
"

# Check for memory leaks
kubectl exec -n production $POD -- pip install memory_profiler
kubectl exec -n production $POD -- python -m memory_profiler app_simple.py

# Force garbage collection
kubectl exec -n production $POD -- python -c "
import gc
gc.collect()
print(f'Collected {gc.collect()} objects')
"

# Restart if necessary
kubectl rollout restart deployment/reagent-backend -n production
```

#### Slow API Response

```bash
#!/bin/bash
# diagnose-performance.sh - Performance diagnostics

# Check current latency
curl -w "@curl-format.txt" -o /dev/null -s https://api.reagent.com.au/health

# Profile specific endpoint
python -m cProfile -o profile.stats test_endpoint.py
python -m pstats profile.stats

# Check database slow queries
psql -h $DB_HOST -U $DB_USER -d reagent -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC
LIMIT 10;
"

# Check Redis latency
redis-cli --latency-history
redis-cli --latency-doctor

# Check AI service latency
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }' \
  -w "\nTime: %{time_total}s\n"
```

#### SSE Connection Issues

```bash
#!/bin/bash
# diagnose-sse.sh - SSE diagnostics

# Test SSE endpoint
curl -N -H "Accept: text/event-stream" \
  https://api.reagent.com.au/api/v1/agent-whisperer/chat/stream \
  -d '{"message":"test","session_id":"test-session"}'

# Check nginx configuration
nginx -t
grep -E "proxy_buffering|proxy_cache" /etc/nginx/nginx.conf

# Check timeout settings
echo "Checking proxy timeouts..."
grep -E "proxy_read_timeout|proxy_connect_timeout" /etc/nginx/nginx.conf

# Monitor active connections
watch -n 1 'netstat -an | grep :8001 | grep ESTABLISHED | wc -l'

# Check for connection drops
tcpdump -i any -n port 8001 -c 1000 | grep -E "RST|FIN"
```

### 4.2 Emergency Procedures

#### Complete System Recovery

```bash
#!/bin/bash
# emergency-recovery.sh - Full system recovery

set -euo pipefail

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] EMERGENCY: $1"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] EMERGENCY: $1" >> /var/log/emergency-recovery.log
}

# Step 1: Assess current state
log "Assessing system state..."
BACKEND_STATUS=$(kubectl get pods -n production -l component=backend --no-headers | grep -c Running || echo 0)
FRONTEND_STATUS=$(kubectl get pods -n production -l component=frontend --no-headers | grep -c Running || echo 0)
DB_STATUS=$(pg_isready -h $DB_HOST || echo "DOWN")

log "Backend pods running: $BACKEND_STATUS"
log "Frontend pods running: $FRONTEND_STATUS"
log "Database status: $DB_STATUS"

# Step 2: Restore database if needed
if [ "$DB_STATUS" == "DOWN" ]; then
    log "Restoring database from backup..."
    aws s3 cp s3://reagent-backups/latest/database.sql.gz /tmp/
    gunzip /tmp/database.sql.gz
    psql -h $DB_BACKUP_HOST -U $DB_USER -d postgres -c "CREATE DATABASE reagent_recovery;"
    psql -h $DB_BACKUP_HOST -U $DB_USER -d reagent_recovery < /tmp/database.sql
    log "Database restored to $DB_BACKUP_HOST"
fi

# Step 3: Restore application
log "Deploying emergency configuration..."
kubectl apply -f emergency-config.yaml -n production

# Step 4: Scale up minimal services
log "Starting minimal services..."
kubectl scale deployment/reagent-backend --replicas=1 -n production
kubectl scale deployment/reagent-frontend --replicas=1 -n production

# Step 5: Wait for services
log "Waiting for services to start..."
kubectl wait --for=condition=ready pod -l component=backend -n production --timeout=300s
kubectl wait --for=condition=ready pod -l component=frontend -n production --timeout=300s

# Step 6: Verify basic functionality
log "Verifying basic functionality..."
if curl -f https://api.reagent.com.au/health; then
    log "Health check passed"
else
    log "Health check failed - manual intervention required"
    exit 1
fi

# Step 7: Gradually scale up
log "Scaling up to normal capacity..."
kubectl scale deployment/reagent-backend --replicas=3 -n production
kubectl scale deployment/reagent-frontend --replicas=2 -n production

log "Emergency recovery completed"
log "System is running in degraded mode - full restoration required"
```

---

## 5. Performance Tuning

### 5.1 Application Tuning

```python
# performance_config.py - Optimized settings

import uvloop
import asyncio

# Use uvloop for better async performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# FastAPI optimization
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(
    title="ReAgent API",
    docs_url=None,  # Disable in production
    redoc_url=None,  # Disable in production
    openapi_url=None,  # Disable in production
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*.reagent.com.au"])

# Connection pool optimization
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,  # Disable SQL logging in production
    future=True,
    query_cache_size=1200,
    connect_args={
        "server_settings": {
            "application_name": "reagent_backend",
            "jit": "off"
        },
        "command_timeout": 60,
        "prepared_statement_cache_size": 0,  # Disable if using PgBouncer
    }
)

# Redis optimization
import redis.asyncio as redis

redis_pool = redis.ConnectionPool(
    host="redis.reagent.internal",
    port=6379,
    db=0,
    max_connections=50,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
    connection_class=redis.Connection,
    connection_kwargs={
        "socket_keepalive": True,
        "socket_keepalive_options": {
            1: 1,  # TCP_KEEPIDLE
            2: 3,  # TCP_KEEPINTVL
            3: 5,  # TCP_KEEPCNT
        }
    }
)
```

### 5.2 Database Tuning

```sql
-- performance_tuning.sql - PostgreSQL optimization

-- Connection pooling with PgBouncer
-- /etc/pgbouncer/pgbouncer.ini
[databases]
reagent = host=localhost port=5432 dbname=reagent

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
server_lifetime = 3600
server_idle_timeout = 600
server_connect_timeout = 15
server_login_retry = 15
query_wait_timeout = 120
client_login_timeout = 60

-- Query optimization
-- Create appropriate indexes
CREATE INDEX CONCURRENTLY idx_chat_messages_session_created 
    ON chat_messages(session_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_chat_messages_created 
    ON chat_messages(created_at DESC) 
    WHERE created_at > NOW() - INTERVAL '7 days';

-- Partial indexes for common queries
CREATE INDEX CONCURRENTLY idx_active_sessions 
    ON sessions(id) 
    WHERE ended_at IS NULL;

-- Analyze tables regularly
ANALYZE chat_messages;
ANALYZE sessions;

-- Vacuum settings
ALTER TABLE chat_messages SET (autovacuum_vacuum_scale_factor = 0.01);
ALTER TABLE sessions SET (autovacuum_analyze_scale_factor = 0.05);

-- Query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time,
    rows
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 20;
```

### 5.3 Cache Optimization

```python
# cache_strategy.py - Multi-layer caching

from functools import lru_cache, wraps
import hashlib
import json
import asyncio
from typing import Any, Optional
import redis.asyncio as redis

class CacheManager:
    def __init__(self, redis_pool):
        self.redis = redis.Redis(connection_pool=redis_pool)
        self.local_cache = {}
        
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (L1 local, L2 Redis)"""
        # L1: Local memory cache
        if key in self.local_cache:
            return self.local_cache[key]
        
        # L2: Redis cache
        value = await self.redis.get(key)
        if value:
            self.local_cache[key] = json.loads(value)
            return self.local_cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set in both cache layers"""
        # L1: Local cache
        self.local_cache[key] = value
        
        # L2: Redis cache
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )
    
    def cached(self, prefix: str, ttl: int = 3600):
        """Decorator for caching async functions"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = self.cache_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

# Usage example
cache = CacheManager(redis_pool)

@cache.cached("chat_response", ttl=1800)
async def get_ai_response(message: str, model: str = "gpt-3.5-turbo"):
    # Expensive AI call
    response = await openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content
```

---

## 6. Security Hardening

### 6.1 Security Checklist

```yaml
# security-checklist.yaml

Application Security:
  ✓ Input validation on all endpoints
  ✓ SQL injection prevention (parameterized queries)
  ✓ XSS protection (content escaping)
  ✓ CSRF tokens for state-changing operations
  ✓ Rate limiting implemented
  ✓ Authentication required for admin endpoints
  ✓ Authorization checks on all resources
  ✓ Secure session management
  ✓ Security headers configured

Infrastructure Security:
  ✓ SSL/TLS certificates valid and auto-renewed
  ✓ Firewall rules configured (least privilege)
  ✓ SSH key-based authentication only
  ✓ Fail2ban configured for brute force protection
  ✓ SELinux/AppArmor enabled
  ✓ Regular security updates applied
  ✓ Intrusion detection system active
  ✓ Log aggregation and monitoring

Data Security:
  ✓ Encryption at rest (database, backups)
  ✓ Encryption in transit (TLS 1.3)
  ✓ PII data masking in logs
  ✓ Secure backup storage (encrypted, access controlled)
  ✓ Data retention policies implemented
  ✓ GDPR compliance measures
  ✓ Regular data audits

Secrets Management:
  ✓ No hardcoded secrets in code
  ✓ Environment variables for configuration
  ✓ Secrets rotated regularly
  ✓ AWS Secrets Manager / HashiCorp Vault integration
  ✓ Principle of least privilege for service accounts
  ✓ Audit trail for secret access
```

### 6.2 Security Configuration

```nginx
# nginx-security.conf - Security headers and configuration

server {
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.reagent.com.au wss://api.reagent.com.au; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;
    add_header Permissions-Policy "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
    limit_conn_zone $binary_remote_addr zone=addr:10m;
    
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        limit_conn addr 10;
        # ... proxy configuration
    }
    
    location /api/auth/ {
        limit_req zone=auth burst=5 nodelay;
        limit_conn addr 2;
        # ... proxy configuration
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        return 404;
    }
    
    location ~ \.(env|git|yml|yaml|toml|ini|conf|config)$ {
        deny all;
        return 404;
    }
}
```

---

## 7. Disaster Recovery

### 7.1 Backup Procedures

```bash
#!/bin/bash
# backup.sh - Automated backup script

set -euo pipefail

# Configuration
BACKUP_DIR="/backup/reagent"
S3_BUCKET="s3://reagent-backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] BACKUP: $1"
}

# Database backup
backup_database() {
    log "Starting database backup..."
    
    pg_dump \
        -h $DB_HOST \
        -U $DB_USER \
        -d reagent \
        --no-owner \
        --no-acl \
        --clean \
        --if-exists \
        --compress=9 \
        -f "$BACKUP_DIR/database_$TIMESTAMP.sql.gz"
    
    log "Database backup completed: database_$TIMESTAMP.sql.gz"
}

# Redis backup
backup_redis() {
    log "Starting Redis backup..."
    
    redis-cli --rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"
    gzip "$BACKUP_DIR/redis_$TIMESTAMP.rdb"
    
    log "Redis backup completed: redis_$TIMESTAMP.rdb.gz"
}

# Application files backup
backup_application() {
    log "Starting application backup..."
    
    tar -czf "$BACKUP_DIR/application_$TIMESTAMP.tar.gz" \
        --exclude=node_modules \
        --exclude=__pycache__ \
        --exclude=.git \
        /app
    
    log "Application backup completed: application_$TIMESTAMP.tar.gz"
}

# Upload to S3
upload_to_s3() {
    log "Uploading backups to S3..."
    
    aws s3 cp "$BACKUP_DIR/" "$S3_BUCKET/$(date +%Y/%m/%d)/" \
        --recursive \
        --exclude "*" \
        --include "*_$TIMESTAMP*"
    
    log "Upload to S3 completed"
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Local cleanup
    find "$BACKUP_DIR" -type f -mtime +7 -delete
    
    # S3 cleanup
    aws s3 ls "$S3_BUCKET" --recursive | \
        awk -v date="$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)" '$1 < date {print $4}' | \
        xargs -I {} aws s3 rm "$S3_BUCKET/{}"
    
    log "Cleanup completed"
}

# Main execution
main() {
    log "Starting backup process..."
    
    backup_database
    backup_redis
    backup_application
    upload_to_s3
    cleanup_old_backups
    
    log "Backup process completed successfully"
}

main
```

### 7.2 Restore Procedures

```bash
#!/bin/bash
# restore.sh - Restore from backup

set -euo pipefail

RESTORE_DATE=${1:-$(date +%Y%m%d)}
S3_BUCKET="s3://reagent-backups"
RESTORE_DIR="/tmp/restore"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] RESTORE: $1"
}

# Download backups from S3
download_backups() {
    log "Downloading backups for date: $RESTORE_DATE"
    
    mkdir -p "$RESTORE_DIR"
    aws s3 sync "$S3_BUCKET" "$RESTORE_DIR" \
        --exclude "*" \
        --include "*${RESTORE_DATE}*"
    
    log "Download completed"
}

# Restore database
restore_database() {
    log "Restoring database..."
    
    # Find latest database backup
    DB_BACKUP=$(find "$RESTORE_DIR" -name "database_${RESTORE_DATE}*.sql.gz" | sort -r | head -1)
    
    if [ -z "$DB_BACKUP" ]; then
        log "ERROR: No database backup found for $RESTORE_DATE"
        exit 1
    fi
    
    # Create restore database
    psql -h $DB_HOST -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS reagent_restore;"
    psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE reagent_restore;"
    
    # Restore data
    gunzip -c "$DB_BACKUP" | psql -h $DB_HOST -U $DB_USER -d reagent_restore
    
    log "Database restored to reagent_restore"
}

# Restore Redis
restore_redis() {
    log "Restoring Redis..."
    
    REDIS_BACKUP=$(find "$RESTORE_DIR" -name "redis_${RESTORE_DATE}*.rdb.gz" | sort -r | head -1)
    
    if [ -z "$REDIS_BACKUP" ]; then
        log "WARNING: No Redis backup found for $RESTORE_DATE"
        return
    fi
    
    # Stop Redis
    redis-cli SHUTDOWN SAVE
    
    # Restore backup
    gunzip -c "$REDIS_BACKUP" > /var/lib/redis/dump.rdb
    chown redis:redis /var/lib/redis/dump.rdb
    
    # Start Redis
    systemctl start redis
    
    log "Redis restored"
}

# Verify restoration
verify_restore() {
    log "Verifying restoration..."
    
    # Check database
    DB_COUNT=$(psql -h $DB_HOST -U $DB_USER -d reagent_restore -t -c "SELECT COUNT(*) FROM sessions;")
    log "Database sessions count: $DB_COUNT"
    
    # Check Redis
    REDIS_KEYS=$(redis-cli DBSIZE | awk '{print $1}')
    log "Redis keys count: $REDIS_KEYS"
    
    log "Verification completed"
}

# Main execution
main() {
    log "Starting restore process for date: $RESTORE_DATE"
    
    download_backups
    restore_database
    restore_redis
    verify_restore
    
    log "Restore process completed"
    log "Database restored to: reagent_restore"
    log "Please verify data before switching to production"
}

main
```

---

## 8. Automation Scripts

### 8.1 Health Check Automation

```python
#!/usr/bin/env python3
# health_monitor.py - Continuous health monitoring

import asyncio
import aiohttp
import time
from datetime import datetime
import json
import sys

class HealthMonitor:
    def __init__(self, endpoints):
        self.endpoints = endpoints
        self.metrics = {}
        
    async def check_endpoint(self, session, name, url):
        """Check single endpoint health"""
        start_time = time.time()
        try:
            async with session.get(url, timeout=10) as response:
                latency = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy",
                        "latency_ms": round(latency, 2),
                        "data": data
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "latency_ms": round(latency, 2),
                        "http_status": response.status
                    }
        except asyncio.TimeoutError:
            return {"status": "timeout", "latency_ms": 10000}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_all(self):
        """Check all endpoints"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, url in self.endpoints.items():
                tasks.append(self.check_endpoint(session, name, url))
            
            results = await asyncio.gather(*tasks)
            
            for i, (name, url) in enumerate(self.endpoints.items()):
                self.metrics[name] = results[i]
        
        return self.metrics
    
    def evaluate_health(self):
        """Evaluate overall system health"""
        unhealthy = []
        warnings = []
        
        for name, metrics in self.metrics.items():
            if metrics["status"] != "healthy":
                unhealthy.append(name)
            elif metrics.get("latency_ms", 0) > 1000:
                warnings.append(f"{name} (slow: {metrics['latency_ms']}ms)")
        
        if unhealthy:
            return "CRITICAL", f"Unhealthy services: {', '.join(unhealthy)}"
        elif warnings:
            return "WARNING", f"Performance issues: {', '.join(warnings)}"
        else:
            return "HEALTHY", "All systems operational"
    
    async def monitor_loop(self, interval=30):
        """Continuous monitoring loop"""
        while True:
            try:
                await self.check_all()
                status, message = self.evaluate_health()
                
                print(f"[{datetime.now().isoformat()}] {status}: {message}")
                
                # Send to monitoring system
                if status == "CRITICAL":
                    await self.send_alert(status, message)
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(interval)
    
    async def send_alert(self, status, message):
        """Send alert to notification system"""
        # Implement your alerting logic here
        pass

# Configuration
endpoints = {
    "backend": "https://api.reagent.com.au/health",
    "frontend": "https://reagent.com.au",
    "database": "https://api.reagent.com.au/health/db",
    "redis": "https://api.reagent.com.au/health/redis",
}

# Run monitor
if __name__ == "__main__":
    monitor = HealthMonitor(endpoints)
    asyncio.run(monitor.monitor_loop())
```

### 8.2 Deployment Automation

```yaml
# .github/workflows/deploy.yml - GitHub Actions deployment

name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy'
        required: true
        default: 'latest'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        run: |
          pytest backend/tests/ --cov=backend --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Backend
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:${{ github.sha }}
      
      - name: Build and push Frontend
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-southeast-2
      
      - name: Deploy to ECS
        run: |
          # Update task definition
          aws ecs register-task-definition \
            --cli-input-json file://ecs-task-definition.json
          
          # Update service
          aws ecs update-service \
            --cluster reagent-prod-cluster \
            --service reagent-backend \
            --task-definition reagent-backend:latest \
            --force-new-deployment
          
          # Wait for deployment
          aws ecs wait services-stable \
            --cluster reagent-prod-cluster \
            --services reagent-backend
      
      - name: Verify deployment
        run: |
          curl -f https://api.reagent.com.au/health || exit 1
      
      - name: Notify success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          text: 'Production deployment successful!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
      
      - name: Notify failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          text: 'Production deployment failed!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Aug 2025 | DevOps Team | Initial playbook creation |

---

*This playbook is maintained by the DevOps team. For updates or corrections, please submit a pull request or contact devops@reagent.com.au*