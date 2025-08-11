"""
Custom Instrumentation for Backend Services
Provides decorators and utilities for detailed telemetry
"""

import time
import asyncio
import functools
import logging
from typing import Any, Callable, Optional, Dict, TypeVar, Union
from contextlib import asynccontextmanager

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.metrics import Counter, Histogram, UpDownCounter

from .setup import telemetry

logger = logging.getLogger(__name__)

# Type variables for generic decorators
F = TypeVar('F', bound=Callable[..., Any])


class Instrumentation:
    """Custom instrumentation utilities"""
    
    def __init__(self):
        self.tracer = telemetry.get_tracer()
        self.meter = telemetry.get_meter()
        
        # Initialize custom metrics
        self._init_metrics()
        
    def _init_metrics(self):
        """Initialize custom metrics"""
        
        if not self.meter:
            return
            
        # Query metrics
        self.query_counter = self.meter.create_counter(
            name="query.analyzer.requests",
            description="Query analyzer requests",
            unit="requests",
        )
        
        self.query_duration = self.meter.create_histogram(
            name="query.analyzer.duration",
            description="Query analysis duration",
            unit="ms",
        )
        
        # Property search metrics
        self.property_search_counter = self.meter.create_counter(
            name="property.searches",
            description="Property search requests",
            unit="searches",
        )
        
        self.property_results = self.meter.create_histogram(
            name="property.search.results",
            description="Number of property search results",
            unit="properties",
        )
        
        # Session metrics
        self.session_counter = self.meter.create_counter(
            name="sessions.created",
            description="User sessions created",
            unit="sessions",
        )
        
        self.session_duration = self.meter.create_histogram(
            name="sessions.duration",
            description="Session duration",
            unit="seconds",
        )
        
        # Cache metrics
        self.cache_hits = self.meter.create_counter(
            name="cache.hits",
            description="Cache hit count",
            unit="hits",
        )
        
        self.cache_misses = self.meter.create_counter(
            name="cache.misses",
            description="Cache miss count",
            unit="misses",
        )
        
        # External API metrics
        self.external_api_counter = self.meter.create_counter(
            name="external.api.requests",
            description="External API requests",
            unit="requests",
        )
        
        self.external_api_latency = self.meter.create_histogram(
            name="external.api.latency",
            description="External API latency",
            unit="ms",
        )
    
    def trace_method(
        self,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        record_exception: bool = True,
    ):
        """Decorator to trace method execution"""
        
        def decorator(func: F) -> F:
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.tracer:
                    return await func(*args, **kwargs)
                    
                with self.tracer.start_as_current_span(span_name) as span:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                            
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                        
                    except Exception as e:
                        if record_exception:
                            span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
                        
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.tracer:
                    return func(*args, **kwargs)
                    
                with self.tracer.start_as_current_span(span_name) as span:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                            
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                        
                    except Exception as e:
                        if record_exception:
                            span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
                        
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
                
        return decorator
    
    def measure_time(
        self,
        metric_name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Decorator to measure execution time"""
        
        def decorator(func: F) -> F:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    
                    # Record metric based on name
                    if metric_name == "query_duration":
                        self.query_duration.record(duration, attributes or {})
                    elif metric_name == "session_duration":
                        self.session_duration.record(duration / 1000, attributes or {})
                    elif metric_name == "external_api_latency":
                        self.external_api_latency.record(duration, attributes or {})
                        
                    return result
                    
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    # Still record duration even on error
                    if hasattr(self, metric_name):
                        metric = getattr(self, metric_name)
                        if isinstance(metric, Histogram):
                            error_attrs = {**(attributes or {}), "error": True}
                            metric.record(duration, error_attrs)
                    raise
                    
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    
                    # Record metric based on name
                    if metric_name == "query_duration":
                        self.query_duration.record(duration, attributes or {})
                    elif metric_name == "session_duration":
                        self.session_duration.record(duration / 1000, attributes or {})
                    elif metric_name == "external_api_latency":
                        self.external_api_latency.record(duration, attributes or {})
                        
                    return result
                    
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    # Still record duration even on error
                    if hasattr(self, metric_name):
                        metric = getattr(self, metric_name)
                        if isinstance(metric, Histogram):
                            error_attrs = {**(attributes or {}), "error": True}
                            metric.record(duration, error_attrs)
                    raise
                    
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
                
        return decorator
    
    # Query analysis instrumentation
    def record_query_analysis(
        self,
        query_type: str,
        confidence: float,
        duration: float,
    ):
        """Record query analysis metrics"""
        
        attributes = {
            "query_type": query_type,
            "confidence_level": "high" if confidence > 0.8 else "low",
        }
        
        self.query_counter.add(1, attributes)
        self.query_duration.record(duration * 1000, attributes)
    
    # Property search instrumentation
    def record_property_search(
        self,
        search_type: str,
        result_count: int,
        filters: Dict[str, Any],
    ):
        """Record property search metrics"""
        
        attributes = {
            "search_type": search_type,
            "has_filters": bool(filters),
            "filter_count": len(filters),
        }
        
        self.property_search_counter.add(1, attributes)
        self.property_results.record(result_count, attributes)
    
    # Session instrumentation
    def record_session_created(self, user_id: Optional[str] = None):
        """Record session creation"""
        
        attributes = {
            "authenticated": bool(user_id),
        }
        
        self.session_counter.add(1, attributes)
    
    def record_session_duration(self, duration: float, user_id: Optional[str] = None):
        """Record session duration"""
        
        attributes = {
            "authenticated": bool(user_id),
        }
        
        self.session_duration.record(duration, attributes)
    
    # Cache instrumentation
    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        
        self.cache_hits.add(1, {"cache_type": cache_type})
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        
        self.cache_misses.add(1, {"cache_type": cache_type})
    
    # External API instrumentation
    def record_external_api_call(
        self,
        api_name: str,
        endpoint: str,
        status_code: int,
        duration: float,
    ):
        """Record external API call"""
        
        attributes = {
            "api": api_name,
            "endpoint": endpoint,
            "status": status_code,
            "success": 200 <= status_code < 300,
        }
        
        self.external_api_counter.add(1, attributes)
        self.external_api_latency.record(duration * 1000, attributes)
    
    @asynccontextmanager
    async def trace_streaming(
        self,
        session_id: str,
        sdk_version: str,
        protocol: str,
    ):
        """Context manager for tracing streaming operations"""
        
        if not self.tracer:
            yield None
            return
            
        with self.tracer.start_as_current_span("streaming.session") as span:
            span.set_attribute("session.id", session_id)
            span.set_attribute("sdk.version", sdk_version)
            span.set_attribute("streaming.protocol", protocol)
            
            start_time = time.time()
            chunk_count = 0
            total_bytes = 0
            
            try:
                # Yield span for use in streaming
                span.chunk_count = 0
                span.total_bytes = 0
                yield span
                
                # Record successful streaming
                duration = time.time() - start_time
                span.set_attribute("streaming.duration", duration)
                span.set_attribute("streaming.chunks", span.chunk_count)
                span.set_attribute("streaming.bytes", span.total_bytes)
                span.set_status(Status(StatusCode.OK))
                
                # Record metrics
                telemetry.record_streaming_chunk(
                    span.total_bytes // max(span.chunk_count, 1),
                    sdk_version
                )
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise


# Singleton instance
instrumentation = Instrumentation()

# Export decorators and functions
trace_method = instrumentation.trace_method
measure_time = instrumentation.measure_time
trace_streaming = instrumentation.trace_streaming

# Export record functions
record_query_analysis = instrumentation.record_query_analysis
record_property_search = instrumentation.record_property_search
record_session_created = instrumentation.record_session_created
record_session_duration = instrumentation.record_session_duration
record_cache_hit = instrumentation.record_cache_hit
record_cache_miss = instrumentation.record_cache_miss
record_external_api_call = instrumentation.record_external_api_call