#!/usr/bin/env python3
"""
Comprehensive Health Check and Monitoring Service for MicroCFO
Implements health checks for all dependencies and Prometheus-style metrics

Based on Backend PRD:
- Health checks for database, Redis, S3, AI APIs
- Prometheus metrics export
- Business metrics tracking
- APM integration
"""

import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.now)


class MetricsCounter:
    """Thread-safe counter for metrics"""
    
    def __init__(self):
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = Lock()
    
    def inc(self, name: str, value: float = 1.0, labels: Optional[Dict] = None):
        key = self._make_key(name, labels)
        with self._lock:
            self._values[key] += value
    
    def get(self, name: str, labels: Optional[Dict] = None) -> float:
        key = self._make_key(name, labels)
        with self._lock:
            return self._values.get(key, 0.0)
    
    def _make_key(self, name: str, labels: Optional[Dict]) -> str:
        if labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name
    
    def all(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._values)


class MetricsHistogram:
    """Simple histogram for latency tracking"""
    
    BUCKETS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    
    def __init__(self):
        self._counts: Dict[str, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self._sums: Dict[str, float] = defaultdict(float)
        self._totals: Dict[str, int] = defaultdict(int)
        self._lock = Lock()
    
    def observe(self, name: str, value: float, labels: Optional[Dict] = None):
        key = self._make_key(name, labels)
        
        with self._lock:
            self._sums[key] += value
            self._totals[key] += 1
            
            for bucket in self.BUCKETS:
                if value <= bucket:
                    self._counts[key][bucket] += 1
    
    def _make_key(self, name: str, labels: Optional[Dict]) -> str:
        if labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name
    
    def summary(self, name: str, labels: Optional[Dict] = None) -> Dict:
        key = self._make_key(name, labels)
        with self._lock:
            total = self._totals.get(key, 0)
            return {
                "count": total,
                "sum": self._sums.get(key, 0),
                "avg": self._sums.get(key, 0) / total if total > 0 else 0,
                "buckets": dict(self._counts.get(key, {}))
            }


class Metrics:
    """
    Prometheus-style metrics collection
    
    Usage:
        metrics.counter("requests_total").inc(labels={"endpoint": "/api/v1/audit"})
        metrics.histogram("request_duration").observe(0.125, labels={"endpoint": "/api/v1/audit"})
    """
    
    def __init__(self):
        self._counters: Dict[str, MetricsCounter] = {}
        self._histograms: Dict[str, MetricsHistogram] = {}
        
        # Pre-define common metrics
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """Initialize default application metrics"""
        
        # Request metrics
        self.counter("http_requests_total", "Total HTTP requests")
        self.counter("http_request_errors_total", "Total HTTP request errors")
        self.histogram("http_request_duration_seconds", "HTTP request duration")
        
        # Document processing
        self.counter("documents_processed_total", "Total documents processed")
        self.counter("document_processing_errors_total", "Document processing errors")
        self.histogram("document_processing_duration_seconds", "Document processing time")
        
        # AI/LLM metrics
        self.counter("llm_requests_total", "Total LLM API requests")
        self.counter("llm_tokens_total", "Total LLM tokens used")
        self.counter("llm_errors_total", "LLM API errors")
        self.histogram("llm_request_duration_seconds", "LLM request duration")
        
        # Business metrics
        self.counter("compliance_issues_detected", "Compliance issues detected")
        self.counter("subsidies_matched", "Subsidy matches found")
        self.counter("emails_sent_total", "Emails sent by Agent D")
        
        # Cache metrics
        self.counter("cache_hits_total", "Cache hits")
        self.counter("cache_misses_total", "Cache misses")
    
    def counter(self, name: str, description: str = "") -> MetricsCounter:
        if name not in self._counters:
            self._counters[name] = MetricsCounter()
        return self._counters[name]
    
    def histogram(self, name: str, description: str = "") -> MetricsHistogram:
        if name not in self._histograms:
            self._histograms[name] = MetricsHistogram()
        return self._histograms[name]
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        for name, counter in self._counters.items():
            for key, value in counter.all().items():
                lines.append(f"{key} {value}")
        
        for name, histogram in self._histograms.items():
            # Export histogram buckets
            for key in histogram._totals.keys():
                summary = histogram.summary(name)
                lines.append(f"{key}_count {summary['count']}")
                lines.append(f"{key}_sum {summary['sum']}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary"""
        return {
            "counters": {name: counter.all() for name, counter in self._counters.items()},
            "histograms": {
                name: {
                    key: hist.summary(name) 
                    for key in hist._totals.keys()
                } if hist._totals else {}
                for name, hist in self._histograms.items()
            }
        }


class HealthCheckService:
    """
    Comprehensive health check service
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - S3/Storage access
    - AI API availability (Gemini, Groq, OpenAI)
    - External services (SendGrid, Twilio)
    """
    
    def __init__(self):
        self._last_results: Dict[str, HealthCheckResult] = {}
        self._check_interval = 60  # seconds
        self._last_check_time: Optional[datetime] = None
    
    async def check_database(self) -> HealthCheckResult:
        """Check PostgreSQL database connectivity"""
        start = time.time()
        
        try:
            from src.database import engine
            
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
            
            latency = (time.time() - start) * 1000
            
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="PostgreSQL connected",
                details={"type": "postgresql"}
            )
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )
    
    async def check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity"""
        start = time.time()
        
        try:
            import redis
            
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            client = redis.from_url(redis_url, socket_timeout=5)
            client.ping()
            
            info = client.info('memory')
            
            latency = (time.time() - start) * 1000
            
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Redis connected",
                details={
                    "used_memory": info.get('used_memory_human', 'N/A'),
                    "connected_clients": client.info('clients').get('connected_clients', 0)
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.DEGRADED,  # Redis is optional
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )
    
    async def check_s3(self) -> HealthCheckResult:
        """Check S3/Storage access"""
        start = time.time()
        
        try:
            import boto3
            
            s3_bucket = os.getenv('S3_BUCKET_NAME')
            
            if not s3_bucket:
                return HealthCheckResult(
                    name="s3",
                    status=HealthStatus.DEGRADED,
                    message="S3 not configured (using local storage)"
                )
            
            s3 = boto3.client('s3')
            s3.head_bucket(Bucket=s3_bucket)
            
            latency = (time.time() - start) * 1000
            
            return HealthCheckResult(
                name="s3",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="S3 connected",
                details={"bucket": s3_bucket}
            )
        except Exception as e:
            return HealthCheckResult(
                name="s3",
                status=HealthStatus.DEGRADED,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )
    
    async def check_gemini_api(self) -> HealthCheckResult:
        """Check Google Gemini API"""
        start = time.time()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return HealthCheckResult(
                name="gemini_api",
                status=HealthStatus.DEGRADED,
                message="GEMINI_API_KEY not configured"
            )
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content("Say OK", generation_config={"max_output_tokens": 5})
            
            latency = (time.time() - start) * 1000
            
            return HealthCheckResult(
                name="gemini_api",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Gemini API operational",
                details={"model": "gemini-2.0-flash"}
            )
        except Exception as e:
            return HealthCheckResult(
                name="gemini_api",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )
    
    async def check_groq_api(self) -> HealthCheckResult:
        """Check Groq API"""
        start = time.time()
        
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            return HealthCheckResult(
                name="groq_api",
                status=HealthStatus.DEGRADED,
                message="GROQ_API_KEY not configured"
            )
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": "Say OK"}],
                        "max_tokens": 5
                    },
                    timeout=10
                )
                response.raise_for_status()
            
            latency = (time.time() - start) * 1000
            
            return HealthCheckResult(
                name="groq_api",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Groq API operational",
                details={"model": "llama-3.3-70b-versatile"}
            )
        except Exception as e:
            return HealthCheckResult(
                name="groq_api",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )
    
    async def check_openai_api(self) -> HealthCheckResult:
        """Check OpenAI API"""
        start = time.time()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return HealthCheckResult(
                name="openai_api",
                status=HealthStatus.DEGRADED,
                message="OPENAI_API_KEY not configured"
            )
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": "Say OK"}],
                        "max_tokens": 5
                    },
                    timeout=10
                )
                response.raise_for_status()
            
            latency = (time.time() - start) * 1000
            
            return HealthCheckResult(
                name="openai_api",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="OpenAI API operational",
                details={"model": "gpt-4o-mini"}
            )
        except Exception as e:
            return HealthCheckResult(
                name="openai_api",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )
    
    async def check_chromadb(self) -> HealthCheckResult:
        """Check ChromaDB (vector database)"""
        start = time.time()
        
        try:
            import chromadb
            
            # Try to connect to the legal DB
            from src.vector_database import legal_db
            
            count = legal_db.collection.count()
            
            latency = (time.time() - start) * 1000
            
            return HealthCheckResult(
                name="chromadb",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="ChromaDB operational",
                details={"document_count": count}
            )
        except Exception as e:
            return HealthCheckResult(
                name="chromadb",
                status=HealthStatus.DEGRADED,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        
        checks = [
            self.check_database(),
            self.check_redis(),
            self.check_s3(),
            self.check_gemini_api(),
            self.check_groq_api(),
            self.check_openai_api(),
            self.check_chromadb(),
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        check_results = {}
        overall_status = HealthStatus.HEALTHY
        
        for result in results:
            if isinstance(result, Exception):
                result = HealthCheckResult(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=str(result)
                )
            
            check_results[result.name] = {
                "status": result.status.value,
                "latency_ms": result.latency_ms,
                "message": result.message,
                "details": result.details,
                "checked_at": result.checked_at.isoformat()
            }
            
            self._last_results[result.name] = result
            
            # Determine overall status
            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        self._last_check_time = datetime.now()
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "checks": check_results
        }
    
    async def quick_check(self) -> Dict[str, Any]:
        """Quick health check (database + Redis only)"""
        
        db_result = await self.check_database()
        redis_result = await self.check_redis()
        
        overall = HealthStatus.HEALTHY
        if db_result.status == HealthStatus.UNHEALTHY:
            overall = HealthStatus.UNHEALTHY
        elif redis_result.status == HealthStatus.UNHEALTHY:
            overall = HealthStatus.DEGRADED
        
        return {
            "status": overall.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": db_result.status.value,
                "redis": redis_result.status.value
            }
        }
    
    def get_last_results(self) -> Dict[str, HealthCheckResult]:
        """Get cached health check results"""
        return self._last_results


class BusinessMetrics:
    """
    Business-specific metrics for MicroCFO
    
    Tracks:
    - Documents processed per day
    - Compliance issues detected
    - Subsidies matched
    - User engagement (DAU/MAU)
    - AI API costs
    """
    
    def __init__(self):
        self._daily_documents = defaultdict(int)
        self._daily_compliance_issues = defaultdict(int)
        self._daily_subsidies_matched = defaultdict(int)
        self._daily_emails_sent = defaultdict(int)
        self._daily_api_costs = defaultdict(float)
        self._active_users = set()
        self._lock = Lock()
    
    def _today(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")
    
    def track_document_processed(self, user_id: str):
        with self._lock:
            self._daily_documents[self._today()] += 1
            self._active_users.add(user_id)
    
    def track_compliance_issue(self, count: int = 1):
        with self._lock:
            self._daily_compliance_issues[self._today()] += count
    
    def track_subsidy_match(self, count: int = 1):
        with self._lock:
            self._daily_subsidies_matched[self._today()] += count
    
    def track_email_sent(self, count: int = 1):
        with self._lock:
            self._daily_emails_sent[self._today()] += count
    
    def track_api_cost(self, cost_usd: float, provider: str):
        with self._lock:
            self._daily_api_costs[f"{self._today()}:{provider}"] += cost_usd
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict:
        date = date or self._today()
        
        with self._lock:
            api_costs = {
                k.split(":")[1]: v 
                for k, v in self._daily_api_costs.items() 
                if k.startswith(date)
            }
            
            return {
                "date": date,
                "documents_processed": self._daily_documents.get(date, 0),
                "compliance_issues_detected": self._daily_compliance_issues.get(date, 0),
                "subsidies_matched": self._daily_subsidies_matched.get(date, 0),
                "emails_sent": self._daily_emails_sent.get(date, 0),
                "api_costs_usd": api_costs,
                "total_api_cost_usd": sum(api_costs.values()),
                "active_users": len(self._active_users)
            }


# Global instances
metrics = Metrics()
health_service = HealthCheckService()
business_metrics = BusinessMetrics()
