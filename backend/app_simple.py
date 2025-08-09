"""Simplified ReAgent Backend using only GPT-5"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from datetime import datetime

# Import routers
from api import agent_whisperer, health

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ReAgent Backend V3 - GPT-5 Edition",
    description="Sydney Real Estate Intelligence Platform powered by GPT-5",
    version="3.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
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

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 60)
    logger.info("ReAgent Backend V3 - GPT-5 Edition Starting")
    logger.info(f"Started at: {datetime.now()}")
    logger.info("=" * 60)
    
    from config import settings
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Live Mode Active: {not settings.USE_MOCK}")
    logger.info("Using GPT-5 exclusively for all AI operations")
    
    # Test OpenAI connection
    if settings.OPENAI_API_KEY:
        logger.info("OpenAI API key configured - GPT-5 ready")
    else:
        logger.warning("No OpenAI API key found - please add to .env")
    
    logger.info("Backend ready at http://127.0.0.1:8001")

if __name__ == "__main__":
    # Run on port 8001 to avoid conflict with stuck process
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)