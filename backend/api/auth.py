"""
Authentication API endpoints for ReAgent Sydney V03
Handles JWT token generation and validation
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

from models.auth import AuthRequest, TokenResponse, TokenVerifyResponse
from services.jwt_auth import jwt_auth
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/auth/token", response_model=TokenResponse)
async def generate_token(auth_request: AuthRequest, request: Request):
    """
    Generate a JWT access token
    
    Requires API key validation in staging/production environments.
    Returns JWT token for subsequent API requests.
    """
    try:
        # Validate API key if required
        if getattr(settings, 'REQUIRE_API_KEY', False):
            provided_api_key = request.headers.get('x-api-key')
            if not provided_api_key or provided_api_key != getattr(settings, 'API_KEY', None):
                raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Generate JWT token
        access_token = jwt_auth.generate_token(
            user_id=auth_request.user_id,
            session_id=auth_request.session_id,
            additional_claims={
                "api_key_validated": bool(getattr(settings, 'REQUIRE_API_KEY', False)),
                "environment": settings.ENVIRONMENT
            }
        )
        
        # Calculate expiry time
        expires_in_seconds = jwt_auth.access_token_expire_minutes * 60
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        
        logger.info(f"JWT token generated for user: {auth_request.user_id}, session: {auth_request.session_id}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in_seconds,
            expires_at=expires_at,
            user_id=auth_request.user_id,
            session_id=auth_request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        raise HTTPException(status_code=500, detail="Token generation failed")

@router.post("/auth/verify", response_model=TokenVerifyResponse)
async def verify_token(request: Request):
    """
    Verify a JWT token from Authorization header
    
    Returns token validity and decoded payload information.
    """
    try:
        # Extract token from Authorization header
        token = jwt_auth.extract_bearer_token(request)
        if not token:
            return TokenVerifyResponse(
                valid=False,
                error="Missing or invalid Authorization header"
            )
        
        # Verify token
        payload = jwt_auth.verify_token(token)
        
        return TokenVerifyResponse(
            valid=True,
            user_id=payload.get('sub'),
            session_id=payload.get('session_id'),
            expires_at=datetime.fromtimestamp(payload.get('exp', 0), tz=timezone.utc)
        )
        
    except HTTPException as e:
        return TokenVerifyResponse(
            valid=False,
            error=str(e.detail)
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return TokenVerifyResponse(
            valid=False,
            error="Token verification failed"
        )

@router.get("/auth/status")
async def auth_status():
    """
    Get authentication configuration status
    
    Returns current authentication requirements and configuration.
    """
    return {
        "jwt_required": getattr(settings, 'REQUIRE_JWT_AUTH', True),
        "api_key_required": getattr(settings, 'REQUIRE_API_KEY', False),
        "environment": settings.ENVIRONMENT,
        "token_expiry_minutes": jwt_auth.access_token_expire_minutes,
        "supported_algorithms": [jwt_auth.algorithm],
        "issuer": "reagent-sydney-v03",
        "audience": "reagent-api"
    }