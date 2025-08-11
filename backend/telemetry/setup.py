"""
OpenTelemetry Setup for Backend
Configures metrics, traces, and logs collection for FastAPI
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import inject, extract
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)

# Configuration
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
SERVICE_NAME_VALUE = "reagent-backend"
SERVICE_VERSION_VALUE = os.getenv("VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
REGION = os.getenv("REGION", "sydney")
ENABLE_TELEMETRY = os.getenv("ENABLE_TELEMETRY", "true").lower() == "true"

# Skip telemetry in development unless explicitly enabled
if ENVIRONMENT == "development" and not os.getenv("FORCE_TELEMETRY"):
    ENABLE_TELEMETRY = False


class TelemetryService:
    """Singleton telemetry service for backend"""
    
    _instance: Optional['TelemetryService'] = None
    
    def __new__(cls) -> 'TelemetryService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
            
        self.initialized = False
        self.tracer: Optional[trace.Tracer] = None
        self.meter: Optional[metrics.Meter] = None
        self.tracer_provider: Optional[TracerProvider] = None
        self.meter_provider: Optional[MeterProvider] = None
        
        # Metrics
        self.request_counter: Optional[metrics.Counter] = None
        self.request_duration: Optional[metrics.Histogram] = None
        self.active_requests: Optional[metrics.UpDownCounter] = None
        self.ai_request_counter: Optional[metrics.Counter] = None
        self.ai_token_counter: Optional[metrics.Counter] = None
        self.streaming_chunk_size: Optional[metrics.Histogram] = None
        self.error_counter: Optional[metrics.Counter] = None
        
    def initialize(self, app: Optional[FastAPI] = None) -> None:
        """Initialize OpenTelemetry providers and instrumentation"""
        
        if self.initialized or not ENABLE_TELEMETRY:
            logger.info(f"Telemetry {'already initialized' if self.initialized else 'disabled'}")
            return
            
        try:
            # Create resource
            resource = Resource.create({
                SERVICE_NAME: SERVICE_NAME_VALUE,
                SERVICE_VERSION: SERVICE_VERSION_VALUE,
                "deployment.environment": ENVIRONMENT,
                "service.region": REGION,
                "service.framework": "fastapi",
                "service.language": "python",
            })
            
            # Setup tracing
            self.tracer_provider = TracerProvider(resource=resource)
            
            # Configure trace exporter
            otlp_trace_exporter = OTLPSpanExporter(
                endpoint=OTEL_ENDPOINT,
                insecure=ENVIRONMENT == "development",
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(
                otlp_trace_exporter,
                max_queue_size=2048,
                max_export_batch_size=512,
                schedule_delay_millis=5000,
            )
            self.tracer_provider.add_span_processor(span_processor)
            
            # Set global tracer provider
            trace.set_tracer_provider(self.tracer_provider)
            self.tracer = trace.get_tracer(__name__, SERVICE_VERSION_VALUE)
            
            # Setup metrics
            self.meter_provider = MeterProvider(resource=resource)
            
            # Configure metric exporter
            otlp_metric_exporter = OTLPMetricExporter(
                endpoint=OTEL_ENDPOINT,
                insecure=ENVIRONMENT == "development",
            )
            
            # Add metric reader
            metric_reader = PeriodicExportingMetricReader(
                exporter=otlp_metric_exporter,
                export_interval_millis=30000,  # 30 seconds
            )
            self.meter_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader],
            )
            
            # Set global meter provider
            metrics.set_meter_provider(self.meter_provider)
            self.meter = metrics.get_meter(__name__, SERVICE_VERSION_VALUE)
            
            # Initialize metrics
            self._initialize_metrics()
            
            # Auto-instrument if app provided
            if app:
                self.instrument_app(app)
                
            # Instrument HTTP client
            HTTPXClientInstrumentor().instrument()
            
            # Instrument logging
            LoggingInstrumentor().instrument(
                set_logging_format=True,
                log_level=logging.INFO,
            )
            
            self.initialized = True
            logger.info("Telemetry initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize telemetry: {e}")
            self.initialized = False
            
    def _initialize_metrics(self) -> None:
        """Initialize application metrics"""
        
        if not self.meter:
            return
            
        # Request metrics
        self.request_counter = self.meter.create_counter(
            name="http.server.requests",
            description="Total number of HTTP requests",
            unit="requests",
        )
        
        self.request_duration = self.meter.create_histogram(
            name="http.server.duration",
            description="HTTP request duration",
            unit="ms",
        )
        
        self.active_requests = self.meter.create_up_down_counter(
            name="http.server.active_requests",
            description="Number of active HTTP requests",
            unit="requests",
        )
        
        # AI metrics
        self.ai_request_counter = self.meter.create_counter(
            name="ai.requests",
            description="Total number of AI service requests",
            unit="requests",
        )
        
        self.ai_token_counter = self.meter.create_counter(
            name="ai.tokens",
            description="Total number of AI tokens consumed",
            unit="tokens",
        )
        
        self.streaming_chunk_size = self.meter.create_histogram(
            name="streaming.chunk.size",
            description="Size of streaming response chunks",
            unit="bytes",
        )
        
        # Error metrics
        self.error_counter = self.meter.create_counter(
            name="app.errors",
            description="Total number of application errors",
            unit="errors",
        )
        
    def instrument_app(self, app: FastAPI) -> None:
        """Instrument FastAPI application"""
        
        # Auto-instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Add custom middleware
        @app.middleware("http")
        async def telemetry_middleware(request: Request, call_next):
            """Custom middleware for additional telemetry"""
            
            if not self.initialized:
                return await call_next(request)
                
            # Extract trace context from headers
            ctx = extract(request.headers)
            
            # Start span
            with self.tracer.start_as_current_span(
                f"{request.method} {request.url.path}",
                context=ctx,
                kind=trace.SpanKind.SERVER,
            ) as span:
                # Add span attributes
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.url", str(request.url))
                span.set_attribute("http.scheme", request.url.scheme)
                span.set_attribute("http.host", request.url.hostname or "unknown")
                span.set_attribute("http.target", request.url.path)
                
                # Add custom attributes
                session_id = request.headers.get("X-Session-ID", "unknown")
                sdk_version = request.headers.get("X-SDK-Version", "v3")
                
                span.set_attribute("user.session_id", session_id)
                span.set_attribute("sdk.version", sdk_version)
                
                # Record metrics
                self.active_requests.add(1, {
                    "method": request.method,
                    "endpoint": request.url.path,
                })
                
                start_time = time.time()
                
                try:
                    # Process request
                    response = await call_next(request)
                    
                    # Calculate duration
                    duration = (time.time() - start_time) * 1000
                    
                    # Update span
                    span.set_attribute("http.status_code", response.status_code)
                    
                    if response.status_code >= 400:
                        span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                        
                    # Record metrics
                    attributes = {
                        "method": request.method,
                        "endpoint": request.url.path,
                        "status": response.status_code,
                        "sdk_version": sdk_version,
                    }
                    
                    self.request_counter.add(1, attributes)
                    self.request_duration.record(duration, attributes)
                    
                    if response.status_code >= 500:
                        self.error_counter.add(1, {
                            "type": "http_error",
                            "status": response.status_code,
                            "endpoint": request.url.path,
                        })
                        
                    return response
                    
                except Exception as e:
                    # Record error
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    
                    self.error_counter.add(1, {
                        "type": e.__class__.__name__,
                        "endpoint": request.url.path,
                    })
                    
                    raise
                    
                finally:
                    self.active_requests.add(-1, {
                        "method": request.method,
                        "endpoint": request.url.path,
                    })
                    
    def record_ai_request(
        self,
        provider: str,
        model: str,
        tokens: int,
        success: bool,
        duration: float,
    ) -> None:
        """Record AI service request metrics"""
        
        if not self.initialized:
            return
            
        attributes = {
            "provider": provider,
            "model": model,
            "success": success,
        }
        
        self.ai_request_counter.add(1, attributes)
        self.ai_token_counter.add(tokens, attributes)
        
    def record_streaming_chunk(self, size: int, sdk_version: str) -> None:
        """Record streaming chunk metrics"""
        
        if not self.initialized:
            return
            
        self.streaming_chunk_size.record(size, {
            "sdk_version": sdk_version,
        })
        
    def get_tracer(self) -> Optional[trace.Tracer]:
        """Get tracer instance"""
        return self.tracer
        
    def get_meter(self) -> Optional[metrics.Meter]:
        """Get meter instance"""
        return self.meter
        
    def shutdown(self) -> None:
        """Shutdown telemetry providers"""
        
        if not self.initialized:
            return
            
        try:
            if self.tracer_provider:
                self.tracer_provider.shutdown()
            if self.meter_provider:
                self.meter_provider.shutdown()
                
            logger.info("Telemetry shut down successfully")
            
        except Exception as e:
            logger.error(f"Error shutting down telemetry: {e}")
            
        finally:
            self.initialized = False


# Singleton instance
telemetry = TelemetryService()


@asynccontextmanager
async def trace_operation(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """Context manager for tracing operations"""
    
    tracer = telemetry.get_tracer()
    if not tracer:
        yield None
        return
        
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
                
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def init_telemetry(app: FastAPI) -> TelemetryService:
    """Initialize telemetry for FastAPI application"""
    telemetry.initialize(app)
    return telemetry