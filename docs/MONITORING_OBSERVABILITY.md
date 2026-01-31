# Monitoring & Observability Strategy for Micro-CFO

## Overview
Comprehensive monitoring strategy to ensure reliability, performance, and security of the Micro-CFO platform.

## 1. Monitoring Stack

### Core Components
```
Application Metrics → Prometheus
Logs → ELK Stack (Elasticsearch, Logstash, Kibana)
Traces → Jaeger / OpenTelemetry
Uptime → UptimeRobot / Pingdom
Alerts → PagerDuty + Slack
Dashboards → Grafana
```

## 2. Key Metrics to Monitor

### Application Metrics

#### API Performance
```python
# metrics.py - Add to integration_server.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

# Business metrics
INVOICE_SCANS = Counter(
    'invoice_scans_total',
    'Total invoice scans',
    ['status']
)

SUBSIDY_MATCHES = Counter(
    'subsidy_matches_total',
    'Total subsidy matches found'
)

LEGAL_ALERTS = Counter(
    'legal_alerts_total',
    'Total legal compliance alerts',
    ['severity']
)

# Example middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

#### Database Metrics
- Connection pool usage
- Query execution time
- Slow queries (>1s)
- Deadlocks
- Table sizes
- Index usage

```sql
-- Slow query monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;
```

#### System Metrics
- CPU usage (target: <70%)
- Memory usage (target: <80%)
- Disk I/O
- Network throughput
- Open file descriptors

### 3. Alerting Rules

#### Critical Alerts (Immediate Response)

```yaml
# prometheus/alerts.yml
groups:
  - name: critical
    rules:
      - alert: ServiceDown
        expr: up{job="microcfo-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Micro-CFO API is down"
          description: "API has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% over last 5 minutes"

      - alert: DatabaseDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL database is down"

      - alert: HighDatabaseConnections
        expr: pg_stat_database_numbackends > 80
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"

      - alert: DiskSpacelow
        expr: node_filesystem_free_bytes{mountpoint="/"} / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Less than 10% disk space remaining"
```

#### Warning Alerts (Monitor Closely)

```yaml
  - name: warnings
    rules:
      - alert: HighLatency
        expr: http_request_duration_seconds{quantile="0.95"} > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API latency is high"
          description: "P95 latency is {{ $value }}s"

      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total[5m]) > 0.7
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU usage above 70%"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / node_memory_MemTotal_bytes > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage above 80%"

      - alert: SlowQueries
        expr: rate(pg_stat_statements_mean_exec_time[5m]) > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow database queries detected"
```

## 4. Logging Strategy

### Structured Logging

```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_object = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_object['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_object['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_object['duration_ms'] = record.duration
            
        return json.dumps(log_object)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('/var/log/microcfo/app.log'),
        logging.StreamHandler()
    ]
)

# Set JSON formatter
for handler in logging.getLogger().handlers:
    handler.setFormatter(JSONFormatter())
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Something unexpected but not critical
- **ERROR**: Error that caused function to fail
- **CRITICAL**: System-wide failure

### Log Retention
- **Application logs**: 30 days hot, 90 days cold (S3)
- **Audit logs**: 7 years (compliance)
- **Security logs**: 1 year
- **Debug logs**: 7 days

## 5. Distributed Tracing

### OpenTelemetry Integration

```python
# tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure tracing
resource = Resource(attributes={
    SERVICE_NAME: "microcfo-api"
})

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(jaeger_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Custom tracing
tracer = trace.get_tracer(__name__)

@app.post("/api/v1/agents/visual-auditor/scan-invoice")
async def scan_invoice(file: UploadFile):
    with tracer.start_as_current_span("scan_invoice") as span:
        span.set_attribute("file.name", file.filename)
        span.set_attribute("file.size", file.size)
        
        # Processing logic
        result = await process_invoice(file)
        
        span.set_attribute("result.status", result.status)
        return result
```

## 6. Health Checks

### Comprehensive Health Endpoint

```python
# health.py
from fastapi import APIRouter
from datetime import datetime
import psutil

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check with dependencies"""
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        from src.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        health["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["status"] = "unhealthy"
        health["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
    finally:
        db.close()
    
    # Redis check
    try:
        from redis import Redis
        r = Redis()
        r.ping()
        health["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
    
    # ChromaDB check
    try:
        from chromadb import Client
        client = Client()
        health["checks"]["chromadb"] = {"status": "healthy"}
    except Exception as e:
        health["checks"]["chromadb"] = {"status": "unhealthy", "error": str(e)}
    
    # System resources
    health["checks"]["system"] = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    return health

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest
    return Response(generate_latest(), media_type="text/plain")
```

## 7. Dashboard Setup

### Grafana Dashboards

#### Main Application Dashboard
- Request rate (req/sec)
- Error rate (%)
- P50/P95/P99 latency
- Active users
- Database connections
- System resources

#### Business Metrics Dashboard
- Daily active users
- Invoice scans per day
- Subsidy matches per day
- Legal alerts by severity
- Revenue metrics

#### Infrastructure Dashboard
- Server health
- Database performance
- Cache hit rates
- Queue depths
- Network traffic

## 8. SLA Monitoring

### Target SLAs
- **Availability**: 99.9% (43.2 minutes downtime/month)
- **API Latency (P95)**: < 500ms
- **API Latency (P99)**: < 2s
- **Error Rate**: < 0.1%

### SLA Tracking
```python
# Calculate SLA
def calculate_sla(uptime_minutes, total_minutes):
    """Calculate availability SLA percentage"""
    return (uptime_minutes / total_minutes) * 100

# Monthly SLA report
def generate_sla_report(month, year):
    total_minutes = get_minutes_in_month(month, year)
    downtime = get_downtime_minutes(month, year)
    uptime = total_minutes - downtime
    
    sla = calculate_sla(uptime, total_minutes)
    
    report = {
        "month": month,
        "year": year,
        "target_sla": 99.9,
        "actual_sla": sla,
        "total_downtime_minutes": downtime,
        "met_target": sla >= 99.9
    }
    
    return report
```

## 9. Security Monitoring

### Security Events to Monitor
- Failed login attempts (>5 in 10 min)
- Unusual API access patterns
- Privilege escalation attempts
- Data export activities
- Configuration changes
- Suspicious file uploads

```python
# security_monitoring.py
FAILED_LOGINS = Counter('failed_logins_total', 'Failed login attempts', ['user'])
SUSPICIOUS_ACTIVITY = Counter('suspicious_activity_total', 'Suspicious activities', ['type'])

async def track_security_event(event_type: str, user_id: str = None, details: dict = None):
    """Track security events"""
    logger.warning(
        "Security event detected",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    SUSPICIOUS_ACTIVITY.labels(type=event_type).inc()
    
    # Alert if critical
    if event_type in ['privilege_escalation', 'data_breach_attempt']:
        send_alert(f"CRITICAL: {event_type} detected for user {user_id}")
```

## 10. Implementation Checklist

### Phase 1: Foundation (Week 1-2)
- [ ] Set up Prometheus
- [ ] Configure basic metrics
- [ ] Implement health endpoints
- [ ] Set up basic alerts

### Phase 2: Logging (Week 3-4)
- [ ] Deploy ELK stack
- [ ] Implement structured logging
- [ ] Configure log rotation
- [ ] Set up log dashboards

### Phase 3: Tracing (Week 5-6)
- [ ] Deploy Jaeger
- [ ] Instrument critical paths
- [ ] Create trace dashboards
- [ ] Document trace analysis

### Phase 4: Dashboards (Week 7-8)
- [ ] Create Grafana dashboards
- [ ] Set up business metrics
- [ ] Configure SLA tracking
- [ ] Train team on usage

### Phase 5: Security (Week 9-10)
- [ ] Implement security monitoring
- [ ] Set up SIEM alerts
- [ ] Configure audit logging
- [ ] Create incident playbooks

---

**Document Version**: 1.0  
**Last Updated**: January 31, 2026  
**Owner**: DevOps Team  
**Status**: Implementation Roadmap
