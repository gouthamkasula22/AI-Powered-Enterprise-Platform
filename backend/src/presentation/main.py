"""
FastAPI Application Entry Point

Main application configuration and setup for the User Authentication System.
Implements clean architecture with proper dependency injection.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Import API routes
from .api.endpoints.health import router as health_router
from .api.endpoints.auth import router as auth_router
from .api.endpoints.admin import router as admin_router
from .api.endpoints.admin_users import router as admin_users_router
from .api.endpoints.users import router as users_router  # Temporarily disabled due to syntax errors
from .api.chat_router import router as chat_router  # Enhanced RAG-powered Chat API router
from .api.routes.document_routes import router as document_router  # Document upload API
from .api.image_router import router as image_router  # Image Generation API
from .api.v1.excel_router import router as excel_router  # Excel Q&A Assistant API

# Import configuration
from ..shared.config import get_settings

# Import database initialization
from ..infrastructure.database.database import (
    initialize_database,
    close_database,
    check_database_health
)

# Import cache initialization
from ..infrastructure.cache import (
    initialize_cache,
    close_cache,
    get_cache_manager
)

# Import middleware
# from .api.middleware.auth_middleware import (
#     AuthenticationMiddleware,
#     RateLimitMiddleware,
#     RequestLoggingMiddleware
# )

# Import exception handlers
# from .api.exception_handlers.handlers import register_exception_handlers

# Import dependencies
# from .api.dependencies.auth import set_application_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def initialize_services():
    """Initialize all application services"""
    try:
        # Initialize database
        logger.info("Initializing database...")
        await initialize_database()
        
        # Test database connectivity
        health_status = await check_database_health()
        if health_status["status"] == "healthy":
            logger.info("Database connection verified successfully")
        else:
            logger.warning(f"Database health check warning: {health_status['message']}")
        
        # Initialize Redis cache
        logger.info("Initializing Redis cache...")
        await initialize_cache()
        
        # Verify cache connectivity
        cache_manager = get_cache_manager()
        cache_health = await cache_manager.health_check()
        if cache_health["status"] == "healthy":
            logger.info("Redis cache connection verified successfully")
        else:
            logger.warning(f"Redis cache health check warning: {cache_health['message']}")
        
        logger.info("All services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


async def cleanup_services():
    """Cleanup application services"""
    try:
        logger.info("Cleaning up services...")
        
        # Close Redis cache connections
        await close_cache()
        logger.info("Redis cache connections closed")
        
        # Close database connections
        await close_database()
        logger.info("Database connections closed")
        
        logger.info("All services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error during service cleanup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting User Authentication System...")
    
    try:
        # Initialize all services
        await initialize_services()
        logger.info("Application startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down User Authentication System...")
        await cleanup_services()
        logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="User Authentication System",
    description="A comprehensive user authentication and management system built with clean architecture",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Register exception handlers
# register_exception_handlers(app)

# Add custom middleware
# app.add_middleware(AuthenticationMiddleware)
# app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
# app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Configure trusted hosts (security)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "testserver"]
)

# Include routers with API versioning
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(health_router, prefix="/api/health", tags=["Health"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(admin_users_router, prefix="/api", tags=["Admin User Management"])
app.include_router(users_router, prefix="/api/users", tags=["User Management"])  # Temporarily disabled
app.include_router(chat_router, prefix="/api", tags=["Chat"])  # Chat API
app.include_router(document_router, tags=["Documents"])  # Document upload API (Admin only)
app.include_router(image_router, tags=["Image Generation"])  # Image Generation API
app.include_router(excel_router, prefix="/api/v1", tags=["Excel Q&A"])  # Excel Q&A Assistant API

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information
    """
    return {
        "message": "User Authentication System API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "authentication": "/auth",
            "user_management": "/users",
            "health_checks": "/health"
        }
    }