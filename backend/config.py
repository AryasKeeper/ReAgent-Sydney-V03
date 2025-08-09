"""
Configuration management using Pydantic Settings
Reads from environment variables and .env file
"""
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with validation"""

    # Application settings
    DEBUG: bool = True
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
    REQUIRE_API_KEY: bool = False

    # Service URLs
    BACKEND_URL: str = "http://localhost:8000"

    # Session settings
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_SESSIONS: int = 100

    # Rate limiting (simple)
    MAX_REQUESTS_PER_MINUTE: int = 60

    # Response variety
    ENABLE_VARIETY: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file

@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()

settings = get_settings()
