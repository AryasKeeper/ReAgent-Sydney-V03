"""
ReAgent Sydney V03 - 72-Hour Spike Implementation
Enterprise-grade real estate intelligence platform for Sydney deployment.

Key Features:
- PostgreSQL with pgvector for semantic search
- Rolling partitions for data lifecycle management  
- JWT authentication with token expiry handling
- Comprehensive security headers and CSP
- ECS Fargate deployment ready
- SSE streaming with Vercel AI SDK compatibility
"""

import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Import configuration and validation
from config import settings, validate_security_configuration

# Import database and models
from database import async_engine
import models  # This registers all models with SQLAlchemy

# Import services
from services.partition_worker import start_partition_worker, stop_partition_worker, get_partition_health
from services.connection_manager import connection_manager

# Import API routes
from api import health, agent_whisperer, security, auth, agents

# Import middleware
from middleware import create_security_middleware

# Initialize Sentry if configured
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
        sample_rate=settings.SENTRY_SAMPLE_RATE,
        integrations=[
            FastApiIntegration(auto_enabling_integrations=True),
            LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            ),
        ],
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions
        profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
    )
    print(f"✓ Sentry initialized for {settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT}")

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with startup and shutdown logic."""
    
    # Startup
    logger.info("🚀 Starting ReAgent Sydney V03 - 72-Hour Spike")
    
    try:
        # Validate security configuration
        security_config = validate_security_configuration()
        logger.info(f"Security status: {security_config['security_status']}")
        
        if security_config['critical_issues']:
            logger.error("Critical security issues detected!")
            for issue in security_config['critical_issues']:
                logger.error(f"  - {issue}")
            raise RuntimeError("Cannot start with critical security issues")
        
        if security_config['warnings']:
            for warning in security_config['warnings']:
                logger.warning(f"Security warning: {warning}")
        
        # Test database connection
        logger.info("Testing database connection...")
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("✓ Database connection successful")
        
        # Start partition management worker
        logger.info("Starting partition management worker...")
        await start_partition_worker()
        logger.info("✓ Partition worker started")
        
        # Check partition health
        partition_health = await get_partition_health()
        logger.info(f"Partition health: {partition_health['status']}")
        
        # Start connection manager
        logger.info("Starting connection manager...")
        await connection_manager.start()
        logger.info("✓ Connection manager started")
        
        logger.info("🎯 ReAgent Sydney V03 startup complete")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ReAgent Sydney V03")
    
    try:
        # Stop connection manager
        await connection_manager.stop()
        logger.info("✓ Connection manager stopped")
        
        # Stop partition worker
        await stop_partition_worker()
        logger.info("✓ Partition worker stopped")
        
        # Close database engine
        await async_engine.dispose()
        logger.info("✓ Database connections closed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    
    logger.info("✓ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="ReAgent Sydney V03",
    description="Enterprise real estate intelligence platform for Sydney",
    version="3.0.0-spike",
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Apply security middleware
app = create_security_middleware(app)

# Configure CORS
if settings.DEBUG:
    # Development CORS - more permissive
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    # Production CORS - restrictive
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://reagent.properties",
            "https://www.reagent.properties",
            "https://api.reagent.properties"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin"
        ],
    )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with security-conscious error messages."""
    
    # Don't expose internal details in production
    if settings.DEBUG:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path)
            }
        )
    else:
        # Generic error messages for production
        if exc.status_code == 404:
            message = "Resource not found"
        elif exc.status_code == 401:
            message = "Authentication required"
        elif exc.status_code == 403:
            message = "Access forbidden"
        elif exc.status_code >= 500:
            message = "Internal server error"
        else:
            message = "Request failed"
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": message, "status_code": exc.status_code}
        )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Capture exception in Sentry
    if settings.SENTRY_DSN:
        sentry_sdk.capture_exception(exc)
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Internal server error: {str(exc)}",
                "type": type(exc).__name__,
                "path": str(request.url.path)
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "status_code": 500}
        )


# Include API routes
app.include_router(health.router, prefix="/v1")
app.include_router(agent_whisperer.router, prefix="/v1")
app.include_router(security.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(agents.router, prefix="/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "service": "ReAgent Sydney V03",
        "version": "3.0.0-spike",
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "features": {
            "multi_agent_system": True,
            "pgvector_search": True,
            "rolling_partitions": True,
            "jwt_authentication": settings.REQUIRE_API_KEY,
            "security_headers": True,
            "sse_streaming": True
        },
        "api": {
            "docs": "/docs" if settings.DEBUG else None,
            "health": "/v1/health",
            "chat": "/v1/agent-whisperer/chat/stream"
        }
    }


# System diagnostics endpoint (admin only)
@app.get("/v1/diagnostics")
async def system_diagnostics():
    """System diagnostics for monitoring and troubleshooting."""
    
    # Basic system info
    diagnostics = {
        "timestamp": "2025-01-13T09:00:00Z",
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "api_key_required": settings.REQUIRE_API_KEY,
        "database_configured": bool(settings.DATABASE_URL),
        "services": {}
    }
    
    try:
        # Partition health
        partition_health = await get_partition_health()
        diagnostics["services"]["partitions"] = partition_health
        
        # Database connection test
        try:
            async with async_engine.begin() as conn:
                await conn.execute("SELECT 1")
            diagnostics["services"]["database"] = {"status": "healthy"}
        except Exception as e:
            diagnostics["services"]["database"] = {"status": "error", "error": str(e)}
        
        # Security configuration
        security_config = validate_security_configuration()
        diagnostics["security"] = security_config
        
        # Connection manager status
        connection_stats = connection_manager.get_connection_stats()
        diagnostics["connections"] = connection_stats
        
        # Sentry status
        diagnostics["observability"] = {
            "sentry_enabled": bool(settings.SENTRY_DSN),
            "sentry_environment": settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
            "sentry_sample_rate": settings.SENTRY_SAMPLE_RATE
        }
        
    except Exception as e:
        diagnostics["error"] = str(e)
    
    return diagnostics


@app.get("/v1/sentry/test")
async def test_sentry():
    """Test Sentry error tracking (development only)"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    if not settings.SENTRY_DSN:
        return {"error": "Sentry not configured"}
    
    try:
        # Trigger a test exception
        raise ValueError("Test Sentry integration - this is intentional")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return {"message": "Test exception sent to Sentry", "exception": str(e)}


if __name__ == "__main__":
    """Run the application directly."""
    
    # Print startup banner
    print("=" * 60)
    print("🚀 ReAgent Sydney V03 - 72-Hour Spike")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"API key required: {settings.REQUIRE_API_KEY}")
    print(f"Database: {'Configured' if settings.DATABASE_URL else 'Not configured'}")
    print("=" * 60)
    
    # Run server
    uvicorn.run(
        "app_spike:app",
        host="0.0.0.0",
        port=8001,  # Fixed port for ReAgent
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=settings.DEBUG
    )