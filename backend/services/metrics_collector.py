"""
Metrics collection service for monitoring AI SDK v5 migration
Tracks performance, errors, and rollout health
"""
import time
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class MetricType(Enum):
    LATENCY = "latency"
    ERROR = "error"
    THROUGHPUT = "throughput"
    REQUEST = "request"
    PROTOCOL = "protocol"

@dataclass
class StreamingMetrics:
    """Metrics for a single streaming request"""
    request_id: str
    session_id: str
    sdk_version: str  # v3 or v5
    protocol: str  # legacy or ui-message-stream
    timestamp: float
    
    # Timing metrics (milliseconds)
    ttfb: float  # Time to first byte
    ttfm: float  # Time to first message
    streaming_duration: float
    total_duration: float
    
    # Data metrics
    chunks_sent: int
    total_bytes: int
    messages_count: int
    
    # Error tracking
    error_occurred: bool
    error_message: Optional[str] = None
    
    # Experiment tracking
    is_experiment: bool = False
    experiment_id: Optional[str] = None

class MetricsCollector:
    """Centralized metrics collection for migration monitoring"""
    
    def __init__(self):
        self.metrics: List[StreamingMetrics] = []
        self.request_trackers: Dict[str, Dict[str, Any]] = {}
        self.aggregated_stats: Dict[str, Any] = {}
        self.last_aggregation = time.time()
        
    def start_request(
        self,
        request_id: str,
        session_id: str,
        sdk_version: str,
        protocol: str,
        is_experiment: bool = False,
        experiment_id: Optional[str] = None
    ):
        """Start tracking a new request"""
        self.request_trackers[request_id] = {
            "session_id": session_id,
            "sdk_version": sdk_version,
            "protocol": protocol,
            "start_time": time.time(),
            "first_byte_time": None,
            "first_message_time": None,
            "chunks_sent": 0,
            "total_bytes": 0,
            "messages_count": 0,
            "error_occurred": False,
            "error_message": None,
            "is_experiment": is_experiment,
            "experiment_id": experiment_id
        }
        
        logger.debug(f"Started tracking request {request_id} with {sdk_version}/{protocol}")
        
    def record_first_byte(self, request_id: str):
        """Record when first byte is sent"""
        if request_id in self.request_trackers:
            tracker = self.request_trackers[request_id]
            if tracker["first_byte_time"] is None:
                tracker["first_byte_time"] = time.time()
                
    def record_first_message(self, request_id: str):
        """Record when first message is sent"""
        if request_id in self.request_trackers:
            tracker = self.request_trackers[request_id]
            if tracker["first_message_time"] is None:
                tracker["first_message_time"] = time.time()
                
    def record_chunk(self, request_id: str, bytes_sent: int):
        """Record a chunk being sent"""
        if request_id in self.request_trackers:
            tracker = self.request_trackers[request_id]
            tracker["chunks_sent"] += 1
            tracker["total_bytes"] += bytes_sent
            tracker["messages_count"] += 1
            
    def record_error(self, request_id: str, error_message: str):
        """Record an error during streaming"""
        if request_id in self.request_trackers:
            tracker = self.request_trackers[request_id]
            tracker["error_occurred"] = True
            tracker["error_message"] = error_message
            logger.warning(f"Error in request {request_id}: {error_message}")
            
    def complete_request(self, request_id: str) -> Optional[StreamingMetrics]:
        """Complete tracking and calculate metrics"""
        if request_id not in self.request_trackers:
            return None
            
        tracker = self.request_trackers[request_id]
        end_time = time.time()
        
        # Calculate timings
        start_time = tracker["start_time"]
        ttfb = 0
        ttfm = 0
        streaming_duration = 0
        
        if tracker["first_byte_time"]:
            ttfb = (tracker["first_byte_time"] - start_time) * 1000
            
        if tracker["first_message_time"]:
            ttfm = (tracker["first_message_time"] - start_time) * 1000
            
        if tracker["first_byte_time"]:
            streaming_duration = (end_time - tracker["first_byte_time"]) * 1000
            
        total_duration = (end_time - start_time) * 1000
        
        # Create metrics object
        metrics = StreamingMetrics(
            request_id=request_id,
            session_id=tracker["session_id"],
            sdk_version=tracker["sdk_version"],
            protocol=tracker["protocol"],
            timestamp=start_time,
            ttfb=ttfb,
            ttfm=ttfm,
            streaming_duration=streaming_duration,
            total_duration=total_duration,
            chunks_sent=tracker["chunks_sent"],
            total_bytes=tracker["total_bytes"],
            messages_count=tracker["messages_count"],
            error_occurred=tracker["error_occurred"],
            error_message=tracker["error_message"],
            is_experiment=tracker["is_experiment"],
            experiment_id=tracker["experiment_id"]
        )
        
        # Store metrics
        self.metrics.append(metrics)
        
        # Clean up tracker
        del self.request_trackers[request_id]
        
        # Log summary
        logger.info(f"Request {request_id} completed: "
                   f"{tracker['sdk_version']}/{tracker['protocol']} "
                   f"TTFB={ttfb:.1f}ms TTFM={ttfm:.1f}ms "
                   f"Duration={total_duration:.1f}ms "
                   f"Bytes={tracker['total_bytes']} "
                   f"Error={tracker['error_occurred']}")
        
        # Aggregate stats periodically
        if time.time() - self.last_aggregation > 60:  # Every minute
            self.aggregate_stats()
            
        return metrics
        
    def aggregate_stats(self):
        """Aggregate statistics for monitoring"""
        now = time.time()
        recent_cutoff = now - 300  # Last 5 minutes
        
        recent_metrics = [m for m in self.metrics if m.timestamp > recent_cutoff]
        
        if not recent_metrics:
            return
            
        # Separate by SDK version
        v3_metrics = [m for m in recent_metrics if m.sdk_version == "v3"]
        v5_metrics = [m for m in recent_metrics if m.sdk_version == "v5"]
        
        def calculate_stats(metrics_list):
            if not metrics_list:
                return {}
                
            ttfb_values = sorted([m.ttfb for m in metrics_list])
            ttfm_values = sorted([m.ttfm for m in metrics_list])
            duration_values = sorted([m.total_duration for m in metrics_list])
            error_count = sum(1 for m in metrics_list if m.error_occurred)
            
            def percentile(values, p):
                if not values:
                    return 0
                idx = int(len(values) * p)
                return values[min(idx, len(values) - 1)]
                
            return {
                "count": len(metrics_list),
                "error_rate": (error_count / len(metrics_list)) * 100,
                "ttfb": {
                    "mean": sum(ttfb_values) / len(ttfb_values),
                    "p50": percentile(ttfb_values, 0.5),
                    "p95": percentile(ttfb_values, 0.95),
                    "p99": percentile(ttfb_values, 0.99)
                },
                "ttfm": {
                    "mean": sum(ttfm_values) / len(ttfm_values),
                    "p50": percentile(ttfm_values, 0.5),
                    "p95": percentile(ttfm_values, 0.95),
                    "p99": percentile(ttfm_values, 0.99)
                },
                "duration": {
                    "mean": sum(duration_values) / len(duration_values),
                    "p50": percentile(duration_values, 0.5),
                    "p95": percentile(duration_values, 0.95),
                    "p99": percentile(duration_values, 0.99)
                }
            }
            
        self.aggregated_stats = {
            "timestamp": now,
            "window_minutes": 5,
            "v3": calculate_stats(v3_metrics),
            "v5": calculate_stats(v5_metrics),
            "total_requests": len(recent_metrics)
        }
        
        # Calculate improvement metrics if both versions have data
        if v3_metrics and v5_metrics:
            v3_stats = self.aggregated_stats["v3"]
            v5_stats = self.aggregated_stats["v5"]
            
            def calc_improvement(v3_val, v5_val):
                if v3_val == 0:
                    return 0
                return ((v3_val - v5_val) / v3_val) * 100
                
            self.aggregated_stats["improvement"] = {
                "ttfb_mean": calc_improvement(v3_stats["ttfb"]["mean"], v5_stats["ttfb"]["mean"]),
                "ttfb_p95": calc_improvement(v3_stats["ttfb"]["p95"], v5_stats["ttfb"]["p95"]),
                "ttfm_mean": calc_improvement(v3_stats["ttfm"]["mean"], v5_stats["ttfm"]["mean"]),
                "ttfm_p95": calc_improvement(v3_stats["ttfm"]["p95"], v5_stats["ttfm"]["p95"]),
                "duration_mean": calc_improvement(v3_stats["duration"]["mean"], v5_stats["duration"]["mean"]),
                "duration_p95": calc_improvement(v3_stats["duration"]["p95"], v5_stats["duration"]["p95"])
            }
            
        self.last_aggregation = now
        
        # Log aggregated stats
        logger.info(f"Aggregated stats: {json.dumps(self.aggregated_stats, indent=2)}")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status for monitoring"""
        # Ensure we have recent stats
        if time.time() - self.last_aggregation > 60:
            self.aggregate_stats()
            
        health = {
            "status": "healthy",
            "timestamp": time.time(),
            "active_requests": len(self.request_trackers),
            "metrics_collected": len(self.metrics)
        }
        
        if self.aggregated_stats:
            health["stats"] = self.aggregated_stats
            
            # Determine overall health
            v5_stats = self.aggregated_stats.get("v5", {})
            if v5_stats:
                error_rate = v5_stats.get("error_rate", 0)
                p95_latency = v5_stats.get("ttfm", {}).get("p95", 0)
                
                if error_rate > 5:
                    health["status"] = "critical"
                    health["reason"] = f"High error rate: {error_rate:.1f}%"
                elif error_rate > 2:
                    health["status"] = "warning"
                    health["reason"] = f"Elevated error rate: {error_rate:.1f}%"
                elif p95_latency > 1000:
                    health["status"] = "warning"
                    health["reason"] = f"High P95 latency: {p95_latency:.1f}ms"
                    
        return health
        
    def export_metrics(self, since: Optional[float] = None) -> List[Dict[str, Any]]:
        """Export metrics for analysis"""
        if since:
            metrics = [m for m in self.metrics if m.timestamp > since]
        else:
            metrics = self.metrics
            
        return [asdict(m) for m in metrics]
        
    def cleanup_old_metrics(self, retention_hours: int = 24):
        """Clean up old metrics to prevent memory growth"""
        cutoff = time.time() - (retention_hours * 3600)
        self.metrics = [m for m in self.metrics if m.timestamp > cutoff]
        logger.info(f"Cleaned up metrics older than {retention_hours} hours, "
                   f"remaining: {len(self.metrics)}")

# Global collector instance
metrics_collector = MetricsCollector()