"""
Authentication Middleware

Middleware for handling authentication, rate limiting, and security.
"""

from typing import Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from collections import defaultdict, deque

from app.core.security import verify_token

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent brute force attacks
    """
    
    def __init__(self, app, calls_per_minute: int = 1000):  # Very high limit for debugging
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            response = await call_next(request)
            return response
            
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Log all requests for debugging
        logger.info(f"Request from {client_ip}: {request.method} {request.url.path}")
        
        # Clean old requests (older than 1 minute)
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Remove old entries - more thorough cleanup
        if client_ip in self.calls:
            old_count = len(self.calls[client_ip])
            self.calls[client_ip] = deque([timestamp for timestamp in self.calls[client_ip] if timestamp >= minute_ago])
            new_count = len(self.calls[client_ip])
            if old_count != new_count:
                logger.debug(f"Cleaned {old_count - new_count} old requests for {client_ip}")
        
        # Check rate limit
        current_requests = len(self.calls[client_ip])
        if current_requests >= self.calls_per_minute:
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {current_requests} requests in last minute (limit: {self.calls_per_minute})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record this request
        self.calls[client_ip].append(current_time)
        
        # Log current request count
        logger.debug(f"Request count for {client_ip}: {len(self.calls[client_ip])}/{self.calls_per_minute}")
        
        # Continue to next middleware/endpoint
        response = await call_next(request)
        return response
        
        # Continue to next middleware/endpoint
        response = await call_next(request)
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for protected routes
    """
    
    # Routes that don't require authentication
    PUBLIC_ROUTES = {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/validate-password",
        "/api/v1/health",
        "/api/v1/auth/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    }
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public routes
        if request.url.path in self.PUBLIC_ROUTES:
            return await call_next(request)
        
        # Skip authentication for root path and static files
        if request.url.path == "/" or request.url.path.startswith("/static"):
            return await call_next(request)
        
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        user_id = verify_token(token)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Add user ID to request state for use in endpoints
        request.state.user_id = user_id
        
        # Continue to next middleware/endpoint
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests for monitoring and debugging
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate request time
            process_time = time.time() - start_time
            
            # Log successful request
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} "
                f"- Time: {process_time:.3f}s "
                f"- IP: {client_ip} "
                f"- User-Agent: {user_agent}"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate request time
            process_time = time.time() - start_time
            
            # Log failed request
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} "
                f"- Time: {process_time:.3f}s "
                f"- IP: {client_ip} "
                f"- User-Agent: {user_agent}"
            )
            
            # Re-raise the exception
            raise
