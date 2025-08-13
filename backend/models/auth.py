"""
Authentication data models for ReAgent Sydney V03 API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AuthRequest(BaseModel):
    """Request model for JWT token generation"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier") 
    api_key: Optional[str] = Field(None, description="API key for additional verification")

class TokenResponse(BaseModel):
    """Response model for JWT token generation"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    expires_at: datetime = Field(..., description="Token expiry timestamp")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")

class TokenVerifyResponse(BaseModel):
    """Response model for token verification"""
    valid: bool = Field(..., description="Whether token is valid")
    user_id: Optional[str] = Field(None, description="User identifier if valid")
    session_id: Optional[str] = Field(None, description="Session identifier if valid")
    expires_at: Optional[datetime] = Field(None, description="Token expiry timestamp if valid")
    error: Optional[str] = Field(None, description="Error message if invalid")