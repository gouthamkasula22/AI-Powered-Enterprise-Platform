"""
User Authentication System - FastAPI Backend

A production-ready authentication system built with FastAPI, featuring:
- JWT-based authentication with token blacklisting
- OAuth 2.0 social login integration
- Email verification and password recovery
- Rate limiting and security middleware
- Comprehensive logging and monitoring
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

from app.core.config import settings
from app.core.database import test_database_connection, create_database_tables, check_database_health, close_database_connections

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log") if settings.ENVIRONMENT != "test" else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application,
    including database connection testing and cleanup.
    """
    # Startup
    logger.info("Starting User Authentication System...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Test database connection
    try:
        await test_database_connection()
        logger.info("Database connection successful")
        
        # Create database tables if they don't exist
        await create_database_tables()
        logger.info("Database tables verified/created")
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        if settings.ENVIRONMENT == "production":
            raise e
        else:
            logger.warning("Continuing without database in development mode")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down User Authentication System...")
    
    # Gracefully close database connections
    try:
        await close_database_connections()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
    
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create FastAPI application with configuration"""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Production-ready authentication system with JWT, OAuth 2.0, and comprehensive security features",
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1", "*.ngrok.io"] if settings.DEBUG else ["yourdomain.com"]
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "HTTPException"
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation exceptions"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": 422,
                    "message": "Validation Error",
                    "type": "ValidationError",
                    "details": exc.errors()
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal Server Error",
                    "type": "InternalServerError"
                }
            }
        )
    
    # Include authentication routes
    try:
        from app.api.v1 import api_router
        app.include_router(api_router)
        logger.info("Authentication API routes enabled")
    except ImportError as e:
        logger.warning(f"Authentication API routes not available: {e}")
    
    # Add authentication and security middleware
    try:
        from app.middleware.auth import (
            RateLimitMiddleware, 
            AuthenticationMiddleware, 
            SecurityHeadersMiddleware,
            RequestLoggingMiddleware
        )
        
        # Add middleware in reverse order (last added = first executed)
        app.add_middleware(RequestLoggingMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)
        # Re-enable rate limiting with reasonable development limits
        app.add_middleware(RateLimitMiddleware, calls_per_minute=120)
        # Note: AuthenticationMiddleware commented out for development
        # app.add_middleware(AuthenticationMiddleware)
        
        logger.info("Security middleware enabled")
    except ImportError as e:
        logger.warning(f"Security middleware not available: {e}")
    
    # Include monitoring router for database performance monitoring
    try:
        from app.api.v1.monitoring import router as monitoring_router
        app.include_router(monitoring_router, tags=["Database Monitoring"])
        logger.info("Database monitoring endpoints enabled")
    except ImportError as e:
        logger.warning(f"Database monitoring endpoints not available: {e}")
    
    return app

app = create_app()

@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API information"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "status": "healthy",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production"
    }

@app.get("/health", tags=["health"])
async def health_check():
    """Enhanced health check endpoint with database connectivity and performance metrics"""
    try:
        # Get comprehensive database health data
        db_health = await check_database_health()
        
        # Determine overall service status based on database health
        service_status = "healthy"
        status_code = status.HTTP_200_OK
        
        if db_health["status"] == "unhealthy":
            service_status = "unhealthy"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif db_health["status"] == "degraded":
            service_status = "degraded"
            status_code = status.HTTP_200_OK
        
        response_data = {
            "status": service_status,
            "service": settings.APP_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_health,
            "timestamp": db_health["timestamp"]
        }
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "service": settings.APP_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
            }
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disabled file watching
        log_level=settings.LOG_LEVEL.lower()
    )
