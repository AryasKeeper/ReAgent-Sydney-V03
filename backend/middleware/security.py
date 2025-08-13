"""Security middleware for ReAgent Sydney V03."""

import os
from typing import Dict, List, Optional
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(
        self,
        app,
        csp_policy: Optional[str] = None,
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[str] = None,
        hsts_max_age: int = 31536000,  # 1 year
        enable_hsts: bool = True,
        additional_headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(app)
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.referrer_policy = referrer_policy
        self.hsts_max_age = hsts_max_age
        self.enable_hsts = enable_hsts
        self.additional_headers = additional_headers or {}
        
        # Build CSP policy
        self.csp_policy = csp_policy or self._build_default_csp_policy()
        
        # Build Permissions Policy
        self.permissions_policy = permissions_policy or self._build_default_permissions_policy()
    
    def _build_default_csp_policy(self) -> str:
        """Build default Content Security Policy."""
        # Different policies for development vs production
        is_development = os.getenv("DEBUG", "false").lower() == "true"
        
        if is_development:
            # More permissive for development
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:*",
                "style-src 'self' 'unsafe-inline' fonts.googleapis.com",
                "font-src 'self' fonts.gstatic.com",
                "img-src 'self' data: blob: https:",
                "connect-src 'self' localhost:* 127.0.0.1:* ws: wss:",
                "media-src 'self'",
                "object-src 'none'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
        else:
            # Strict policy for production
            csp_directives = [
                "default-src 'self'",
                "script-src 'self'",
                "style-src 'self' 'unsafe-inline' fonts.googleapis.com",
                "font-src 'self' fonts.gstatic.com",
                "img-src 'self' data: blob:",
                "connect-src 'self' api.openai.com api.anthropic.com",
                "media-src 'self'",
                "object-src 'none'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "upgrade-insecure-requests"
            ]
        
        return "; ".join(csp_directives)
    
    def _build_default_permissions_policy(self) -> str:
        """Build default Permissions Policy."""
        permissions = [
            "camera=()",
            "microphone=()",
            "geolocation=()",
            "interest-cohort=()",
            "payment=()",
            "usb=()",
            "bluetooth=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
            "ambient-light-sensor=()",
            "autoplay=()",
            "fullscreen=(self)",
            "display-capture=()"
        ]
        return ", ".join(permissions)
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy
        
        # Frame Options
        response.headers["X-Frame-Options"] = self.frame_options
        
        # Content Type Options
        response.headers["X-Content-Type-Options"] = self.content_type_options
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = self.referrer_policy
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = self.permissions_policy
        
        # HSTS (only for HTTPS)
        if self.enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains"
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Remove potentially revealing headers
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        # Add any additional custom headers
        for header_name, header_value in self.additional_headers.items():
            response.headers[header_name] = header_value
        
        return response


def get_security_headers_config() -> Dict:
    """Get security headers configuration based on environment."""
    is_development = os.getenv("DEBUG", "false").lower() == "true"
    is_staging = os.getenv("ENVIRONMENT", "development").lower() == "staging"
    
    if is_development:
        return {
            "frame_options": "SAMEORIGIN",  # Less restrictive for dev
            "enable_hsts": False,  # No HSTS for local development
            "additional_headers": {
                "X-Development-Mode": "true"
            }
        }
    elif is_staging:
        return {
            "frame_options": "DENY",
            "enable_hsts": True,
            "hsts_max_age": 86400,  # 24 hours for staging
            "additional_headers": {
                "X-Environment": "staging"
            }
        }
    else:
        # Production
        return {
            "frame_options": "DENY",
            "enable_hsts": True,
            "hsts_max_age": 31536000,  # 1 year for production
            "additional_headers": {
                "X-Environment": "production"
            }
        }


class RateLimitingSecurityMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting middleware for security."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests: Dict[str, List[float]] = {}
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers (for load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, now: float, client_ip: str):
        """Remove requests older than 1 minute."""
        if client_ip in self.client_requests:
            self.client_requests[client_ip] = [
                req_time for req_time in self.client_requests[client_ip]
                if now - req_time < 60
            ]
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting."""
        import time
        
        now = time.time()
        client_ip = self._get_client_ip(request)
        
        # Clean up old requests
        self._cleanup_old_requests(now, client_ip)
        
        # Check rate limit
        if client_ip in self.client_requests:
            request_count = len(self.client_requests[client_ip])
            if request_count >= self.requests_per_minute:
                # Rate limit exceeded
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(now + 60))
                    }
                )
        
        # Record this request
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []
        self.client_requests[client_ip].append(now)
        
        # Add rate limit headers
        response = await call_next(request)
        remaining = max(0, self.requests_per_minute - len(self.client_requests[client_ip]))
        
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + 60))
        
        return response


def create_security_middleware(app):
    """Create and configure security middleware."""
    config = get_security_headers_config()
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware, **config)
    
    # Add rate limiting in production/staging
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment in ["staging", "production"]:
        requests_per_minute = 120 if environment == "staging" else 60
        app.add_middleware(RateLimitingSecurityMiddleware, requests_per_minute=requests_per_minute)
    
    return app


def get_security_headers_report() -> Dict:
    """Generate security headers report for monitoring."""
    config = get_security_headers_config()
    environment = os.getenv("ENVIRONMENT", "development").lower()
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    security_features = {
        "csp_enabled": True,
        "frame_protection": config["frame_options"],
        "hsts_enabled": config["enable_hsts"],
        "content_type_protection": True,
        "referrer_policy": True,
        "permissions_policy": True,
        "cors_protection": True,
        "rate_limiting": environment in ["staging", "production"]
    }
    
    security_warnings = []
    
    if debug_mode and environment == "production":
        security_warnings.append("DEBUG mode enabled in production")
    
    if not config["enable_hsts"] and environment == "production":
        security_warnings.append("HSTS disabled in production")
    
    if config["frame_options"] == "SAMEORIGIN" and environment == "production":
        security_warnings.append("Frame options not set to DENY in production")
    
    return {
        "environment": environment,
        "debug_mode": debug_mode,
        "security_features": security_features,
        "warnings": security_warnings,
        "config": config
    }