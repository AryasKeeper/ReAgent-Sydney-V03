"""
ReAgent Backend V3 - FastAPI Application
Clean, modular backend for Agent Whisperer MVP
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from api import health, agent_whisperer
from api import metrics as metrics_api
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Application factory pattern"""
    app = FastAPI(
        title="ReAgent Backend V3",
        description="Sydney Real Estate Intelligence Platform",
        version="3.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # CORS middleware - CRITICAL for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # V3 frontend
            "http://localhost:3001",  # V3 frontend alt port
            "http://localhost:3002",  # Dev port
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(
        agent_whisperer.router, 
        prefix="/api/v1/agent-whisperer",
        tags=["chat"]
    )
    app.include_router(metrics_api.router, prefix="/api", tags=["metrics"])
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("=" * 60)
        logger.info("ReAgent Backend V3 - Starting")
        logger.info(f"Mock Mode: {settings.USE_MOCK}")
        logger.info(f"Debug Mode: {settings.DEBUG}")
        logger.info("=" * 60)
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)