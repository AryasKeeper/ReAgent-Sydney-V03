"""
JWT Authentication utilities for ReAgent Sydney V03
Handles JWT token generation, validation, and bearer token extraction
"""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from config import settings
import logging

logger = logging.getLogger(__name__)

class JWTAuthService:
    """JWT authentication service for secure token handling"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 60)
        
    def generate_token(self, user_id: str, session_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a JWT access token
        
        Args:
            user_id: User identifier
            session_id: Session identifier  
            additional_claims: Optional additional claims to include
            
        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "session_id": session_id,
            "iat": now,
            "exp": expire,
            "iss": "reagent-sydney-v03",
            "aud": "reagent-api"
        }
        
        if additional_claims:
            payload.update(additional_claims)
            
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid, expired, or malformed
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="reagent-api",
                issuer="reagent-sydney-v03"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            raise HTTPException(status_code=401, detail="Token verification failed")
    
    def extract_bearer_token(self, request: Request) -> Optional[str]:
        """
        Extract Bearer token from Authorization header
        
        Args:
            request: FastAPI request object
            
        Returns:
            Token string without 'Bearer ' prefix, or None if not found
        """
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
            
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
            
        return parts[1]
    
    def require_jwt_auth(self, request: Request) -> Dict[str, Any]:
        """
        Require valid JWT authentication from request
        
        Args:
            request: FastAPI request object
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If authentication is missing or invalid
        """
        token = self.extract_bearer_token(request)
        if not token:
            raise HTTPException(
                status_code=401, 
                detail="Missing or invalid Authorization header. Expected: Bearer <token>"
            )
        
        return self.verify_token(token)
    
    def optional_jwt_auth(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Optional JWT authentication - returns payload if valid, None if missing
        
        Args:
            request: FastAPI request object
            
        Returns:
            Decoded token payload or None if no token provided
            
        Raises:
            HTTPException: If token is provided but invalid
        """
        token = self.extract_bearer_token(request)
        if not token:
            return None
            
        return self.verify_token(token)

# Global instance
jwt_auth = JWTAuthService()