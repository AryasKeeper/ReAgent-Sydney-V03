"""
Monitoring API endpoints for AI SDK v5 migration metrics
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from services.metrics_collector import metrics_collector

router = APIRouter()

@router.get("/health")
async def get_health_status():
    """
    Get current health status of the streaming service
    Including v3 vs v5 performance metrics
    """
    health = metrics_collector.get_health_status()
    
    # Add additional health checks
    health["service"] = "agent-whisperer"
    health["version"] = "3.0.0"
    health["migration_status"] = "in_progress"
    
    # Determine HTTP status based on health
    if health["status"] == "critical":
        raise HTTPException(status_code=503, detail=health)
    elif health["status"] == "warning":
        # Return 200 with warning in body
        pass
        
    return health

@router.get("/stats")
async def get_aggregated_stats():
    """
    Get aggregated statistics for the last 5 minutes
    """
    # Force aggregation to get fresh stats
    metrics_collector.aggregate_stats()
    
    if not metrics_collector.aggregated_stats:
        return {
            "message": "No statistics available yet",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    return metrics_collector.aggregated_stats

@router.get("/metrics")
async def get_metrics(
    since: Optional[int] = Query(None, description="Unix timestamp to get metrics since"),
    limit: Optional[int] = Query(100, description="Maximum number of metrics to return")
):
    """
    Get raw metrics data for analysis
    """
    metrics = metrics_collector.export_metrics(since)
    
    # Apply limit
    if limit and len(metrics) > limit:
        metrics = metrics[-limit:]
        
    return {
        "count": len(metrics),
        "metrics": metrics,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/comparison")
async def get_version_comparison():
    """
    Get detailed comparison between v3 and v5 performance
    """
    # Force aggregation
    metrics_collector.aggregate_stats()
    stats = metrics_collector.aggregated_stats
    
    if not stats or "v3" not in stats or "v5" not in stats:
        return {
            "message": "Insufficient data for comparison",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    comparison = {
        "timestamp": datetime.utcnow().isoformat(),
        "window_minutes": stats.get("window_minutes", 5),
        "v3": stats["v3"],
        "v5": stats["v5"],
        "improvement": stats.get("improvement", {}),
        "recommendation": determine_recommendation(stats)
    }
    
    return comparison

@router.post("/cleanup")
async def cleanup_old_metrics(
    retention_hours: int = Query(24, description="Hours of metrics to retain")
):
    """
    Clean up old metrics to free memory
    """
    metrics_collector.cleanup_old_metrics(retention_hours)
    
    return {
        "message": f"Cleaned up metrics older than {retention_hours} hours",
        "remaining_metrics": len(metrics_collector.metrics),
        "timestamp": datetime.utcnow().isoformat()
    }

def determine_recommendation(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine rollout recommendation based on metrics
    """
    recommendation = {
        "action": "continue",
        "confidence": "high",
        "reasons": []
    }
    
    v3_stats = stats.get("v3", {})
    v5_stats = stats.get("v5", {})
    improvement = stats.get("improvement", {})
    
    # Check sample size
    v5_count = v5_stats.get("count", 0)
    if v5_count < 10:
        recommendation["action"] = "wait"
        recommendation["confidence"] = "low"
        recommendation["reasons"].append(f"Insufficient v5 samples: {v5_count}")
        return recommendation
        
    # Check error rate
    v5_error_rate = v5_stats.get("error_rate", 0)
    if v5_error_rate > 5:
        recommendation["action"] = "rollback"
        recommendation["confidence"] = "high"
        recommendation["reasons"].append(f"High v5 error rate: {v5_error_rate:.1f}%")
        return recommendation
    elif v5_error_rate > 2:
        recommendation["confidence"] = "medium"
        recommendation["reasons"].append(f"Elevated v5 error rate: {v5_error_rate:.1f}%")
        
    # Check latency
    v5_p95_ttfm = v5_stats.get("ttfm", {}).get("p95", 0)
    if v5_p95_ttfm > 1000:
        recommendation["action"] = "pause"
        recommendation["confidence"] = "medium"
        recommendation["reasons"].append(f"High v5 P95 latency: {v5_p95_ttfm:.1f}ms")
        return recommendation
        
    # Check improvements
    ttfm_improvement = improvement.get("ttfm_mean", 0)
    if ttfm_improvement > 10:
        recommendation["action"] = "accelerate"
        recommendation["reasons"].append(f"Excellent TTFM improvement: {ttfm_improvement:.1f}%")
    elif ttfm_improvement < -10:
        recommendation["action"] = "pause"
        recommendation["confidence"] = "medium"
        recommendation["reasons"].append(f"TTFM regression: {ttfm_improvement:.1f}%")
        
    # Overall assessment
    if not recommendation["reasons"]:
        recommendation["reasons"].append("All metrics within acceptable ranges")
        
    return recommendation