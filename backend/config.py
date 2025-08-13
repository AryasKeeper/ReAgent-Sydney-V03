"""
Configuration management using Pydantic Settings
Reads from environment variables and .env file
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with validation"""

    # Environment and deployment settings
    ENVIRONMENT: str = "development"  # development|staging|production
    
    # Application settings with environment-aware defaults
    DEBUG: bool = True  # Will be overridden by environment-specific logic
    USE_MOCK: bool = False  # Switch to live mode for real intelligence

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # set via env, e.g., gpt-5-mini
    OPENAI_MODEL_FALLBACK: str = "gpt-4o-mini"  # set via env, e.g., gpt-5-nano
    OPENAI_MODEL_COMPLEX: Optional[str] = None  # optional, e.g., gpt-5
    OPENAI_USE_RESPONSES: bool = False  # toggle Responses API path for GPT-5
    OPENAI_REASONING_EFFORT: str = "medium"  # minimal|low|medium|high
    OPENAI_VERBOSITY: str = "medium"  # low|medium|high

    # Other providers
    ANTHROPIC_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    PERPLEXITY_API_KEY: Optional[str] = None
    FIRECRAWL_API_KEY: Optional[str] = None
    BRAVE_API_KEY: Optional[str] = None
    BROWSERLESS_TOKEN: Optional[str] = None
    REDIS_URL: Optional[str] = None
    USE_REDIS_SESSIONS: bool = False
    API_KEY: Optional[str] = None
    REQUIRE_API_KEY: bool = False  # Will be overridden by environment-specific logic
    
    # Database settings  
    DATABASE_URL: Optional[str] = None
    ASYNC_DATABASE_URL: Optional[str] = None
    
    # Security settings
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REQUIRE_JWT_AUTH: bool = True  # Will be overridden by environment-specific logic
    
    # Admin settings
    ADMIN_API_KEY: Optional[str] = None
    
    # Observability settings
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: Optional[str] = None
    SENTRY_SAMPLE_RATE: float = 1.0

    # Service URLs
    BACKEND_URL: str = "http://localhost:8000"

    # Session settings
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_SESSIONS: int = 100

    # Rate limiting (simple)
    MAX_REQUESTS_PER_MINUTE: int = 60

    # Response variety
    ENABLE_VARIETY: bool = True
    
    # Web Browsing Feature Flags
    BROWSE_FORCE_EXPLICIT: bool = True  # Enable explicit web search override
    BROWSE_SESSION_MEMORY: bool = True  # Enable session preference memory
    BROWSE_FALLBACK_NOTICE: bool = True  # Show fallback notices when APIs unavailable
    
    # Classification Logging Controls
    CLASSIFICATION_LOG_RATE_LIMIT: int = 100  # Max classification logs per minute
    CLASSIFICATION_LOG_MAX_LENGTH: int = 50  # Max query length in logs
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file

def apply_environment_overrides(settings: Settings) -> Settings:
    """Apply environment-specific security overrides."""
    environment = settings.ENVIRONMENT.lower()
    
    # CRITICAL: Hard-lock staging and production security settings
    if environment == "staging":
        # MANDATORY staging security settings
        settings.DEBUG = False  # NEVER allow debug in staging
        settings.REQUIRE_API_KEY = True  # ALWAYS require API key in staging
        settings.USE_MOCK = False  # NEVER use mock data in staging
        settings.SENTRY_ENVIRONMENT = "staging"
        
        # Validate required staging settings
        if not settings.API_KEY:
            raise ValueError("API_KEY must be set for staging environment")
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set for staging environment")
        if not settings.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY must be set for staging environment")
    
    elif environment == "production":
        # MANDATORY production security settings
        settings.DEBUG = False  # NEVER allow debug in production
        settings.REQUIRE_API_KEY = True  # ALWAYS require API key in production
        settings.USE_MOCK = False  # NEVER use mock data in production
        settings.SENTRY_ENVIRONMENT = "production"
        
        # Validate required production settings
        if not settings.API_KEY:
            raise ValueError("API_KEY must be set for production environment")
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set for production environment")
        if not settings.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY must be set for production environment")
        if not settings.ADMIN_API_KEY:
            raise ValueError("ADMIN_API_KEY must be set for production environment")
        
        # Additional production validations
        if "password" in (settings.DATABASE_URL or "").lower():
            raise ValueError("Production DATABASE_URL appears to contain default password")
        if len(settings.JWT_SECRET_KEY or "") < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters for production")
    
    elif environment == "development":
        # Development can have flexible settings, but warn about security
        settings.REQUIRE_JWT_AUTH = False  # Allow development without JWT
        settings.SENTRY_ENVIRONMENT = "development"
        if settings.DEBUG and settings.REQUIRE_API_KEY:
            print("WARNING: Both DEBUG and REQUIRE_API_KEY are enabled in development")
    
    return settings


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance with environment overrides."""
    base_settings = Settings()
    return apply_environment_overrides(base_settings)


def validate_security_configuration() -> dict:
    """Validate current security configuration."""
    settings = get_settings()
    environment = settings.ENVIRONMENT.lower()
    
    validations = {
        "environment": environment,
        "security_status": "unknown",
        "critical_issues": [],
        "warnings": [],
        "checks": {}
    }
    
    # Critical security checks
    if environment in ["staging", "production"]:
        # These MUST be true for staging/production
        if settings.DEBUG:
            validations["critical_issues"].append(f"DEBUG=True in {environment} environment")
        if not settings.REQUIRE_API_KEY:
            validations["critical_issues"].append(f"REQUIRE_API_KEY=False in {environment} environment")
        if settings.USE_MOCK:
            validations["critical_issues"].append(f"USE_MOCK=True in {environment} environment")
        if not settings.DATABASE_URL:
            validations["critical_issues"].append(f"DATABASE_URL not set in {environment} environment")
        if not settings.JWT_SECRET_KEY:
            validations["critical_issues"].append(f"JWT_SECRET_KEY not set in {environment} environment")
    
    # Warning-level checks
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        validations["warnings"].append("No AI provider API keys configured")
    
    if environment == "production" and not settings.ADMIN_API_KEY:
        validations["warnings"].append("ADMIN_API_KEY not set for production")
    
    # Security feature checks
    validations["checks"] = {
        "debug_disabled": not settings.DEBUG,
        "api_key_required": settings.REQUIRE_API_KEY,
        "mock_disabled": not settings.USE_MOCK,
        "database_configured": bool(settings.DATABASE_URL),
        "jwt_configured": bool(settings.JWT_SECRET_KEY),
        "admin_key_configured": bool(settings.ADMIN_API_KEY),
        "ai_keys_configured": bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)
    }
    
    # Determine overall security status
    if validations["critical_issues"]:
        validations["security_status"] = "critical"
    elif validations["warnings"]:
        validations["security_status"] = "warning"
    else:
        validations["security_status"] = "secure"
    
    return validations


# Initialize settings with validation
try:
    settings = get_settings()
    # Validate security configuration on startup
    security_validation = validate_security_configuration()
    if security_validation["critical_issues"]:
        print(f"CRITICAL SECURITY ISSUES DETECTED:")
        for issue in security_validation["critical_issues"]:
            print(f"  - {issue}")
        raise RuntimeError("Critical security configuration issues prevent startup")
except Exception as e:
    print(f"Configuration error: {e}")
    raise
