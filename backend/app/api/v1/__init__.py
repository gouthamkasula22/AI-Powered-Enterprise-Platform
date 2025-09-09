"""
API v1 Routes

Main API router for version 1 of the authentication system.
"""

from fastapi import APIRouter
from .auth import router as auth_router

# Create main API v1 router
api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth_router, prefix="/api/v1")

# Global health check
@api_router.get("/api/v1/health")
async def health_check():
    """API health check"""
    return {"status": "healthy", "version": "1.0.0", "service": "user-auth-system"}
