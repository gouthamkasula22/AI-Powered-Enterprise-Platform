"""
Authentication Middleware

Custom middleware for JWT authentication, rate limiting, and request processing.
"""

import time
import logging
from typing import Optional, Dict, Any, List, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling authentication and security headers
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/health",
            "/health/ready",
            "/health/live",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/forgot-password",
            "/auth/reset-password",
            "/auth/refresh",
            "/auth/verify-email"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers"""
        
        # Add security headers to all responses
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # CORS headers are handled by FastAPI CORS middleware
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware
    In production, use Redis or similar distributed store
    """
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.clients: Dict[str, Dict] = {}
        
        # Different limits for different endpoint types
        self.endpoint_limits = {
            "/auth/login": 5,          # 5 login attempts per minute
            "/auth/register": 3,       # 3 registration attempts per minute
            "/auth/forgot-password": 3, # 3 password reset requests per minute
            "/auth/reset-password": 5,  # 5 password reset attempts per minute
        }
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def is_rate_limited(self, client_ip: str, endpoint: str) -> bool:
        """Check if client is rate limited"""
        current_time = time.time()
        
        # Get endpoint-specific limit or use default
        limit = self.endpoint_limits.get(endpoint, self.requests_per_minute)
        
        # Initialize client data if not exists
        if client_ip not in self.clients:
            self.clients[client_ip] = {}
        
        if endpoint not in self.clients[client_ip]:
            self.clients[client_ip][endpoint] = {
                "requests": [],
                "blocked_until": None
            }
        
        client_data = self.clients[client_ip][endpoint]
        
        # Check if client is currently blocked
        if client_data["blocked_until"] and current_time < client_data["blocked_until"]:
            return True
        
        # Clean old requests (older than 1 minute)
        client_data["requests"] = [
            req_time for req_time in client_data["requests"]
            if current_time - req_time < 60
        ]
        
        # Check if limit exceeded
        if len(client_data["requests"]) >= limit:
            # Block client for 1 minute
            client_data["blocked_until"] = current_time + 60
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return True
        
        # Add current request
        client_data["requests"].append(current_time)
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limiting before processing request"""
        
        client_ip = self.get_client_ip(request)
        endpoint = request.url.path
        
        # Check rate limiting
        if self.is_rate_limited(client_ip, endpoint):
            logger.warning(f"Rate limit exceeded: {client_ip} -> {endpoint}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details"""
        
        start_time = time.time()
        
        # Get client info
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.headers.get("X-Real-IP", "")
        if not client_ip and request.client:
            client_ip = request.client.host
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {client_ip} "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"Error: {str(e)} "
                f"Time: {process_time:.3f}s"
            )
            raise


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with security considerations
    """
    
    def __init__(self, app: ASGIApp, allowed_origins: Optional[List[str]] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["http://localhost:3000", "http://localhost:5173"]
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in allowed list"""
        if not origin:
            return False
        
        # Check exact matches
        if origin in self.allowed_origins:
            return True
        
        # In development, allow localhost with any port
        if origin.startswith("http://localhost:") or origin.startswith("https://localhost:"):
            return True
        
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS with security checks"""
        
        origin = request.headers.get("Origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            if origin and self.is_origin_allowed(origin):
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                        "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With",
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Max-Age": "86400",  # 24 hours
                    }
                )
            else:
                return Response(status_code=403)
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        if origin and self.is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response