"""
Authentication API Router

Combines all authentication endpoints into a single router.
"""

from fastapi import APIRouter
from .endpoints import router as auth_router

# Create main authentication router
router = APIRouter()

# Include all authentication endpoints
router.include_router(auth_router)

# Health check endpoint for authentication service
@router.get("/auth/health")
async def auth_health_check():
    """Health check for authentication service"""
    return {"status": "healthy", "service": "authentication"}
