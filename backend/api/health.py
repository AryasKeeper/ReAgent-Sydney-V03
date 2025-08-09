"""Health check endpoint for monitoring"""
from fastapi import APIRouter
from datetime import datetime
from config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "ok",
        "service": "ReAgent Backend V3",
        "timestamp": datetime.utcnow().isoformat(),
        "mode": "mock" if settings.USE_MOCK else "live",
        "models_available": {
            "openai": bool(settings.OPENAI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY),
            "tavily": bool(settings.TAVILY_API_KEY),
            "firecrawl": bool(settings.FIRECRAWL_API_KEY),
        }
    }