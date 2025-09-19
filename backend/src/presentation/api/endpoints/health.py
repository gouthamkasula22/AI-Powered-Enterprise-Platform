"""
Health Check Endpoint

Simple health check endpoint for monitoring and load balancer integration.
"""

from fastapi import APIRouter, status, Depends
from datetime import datetime
from typing import Dict, Any
import psutil
import asyncio

from ....shared.config import get_settings
from ....infrastructure.database.database import check_database_health

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "user-authentication-system",
        "version": get_settings().app_version
    }


@router.get("/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with system metrics and database status
    
    Returns:
        Detailed health status and system information
    """
    try:
        # Basic system metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database health check
        db_health = await check_database_health()
        
        overall_status = "healthy" if db_health["status"] == "healthy" else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "user-authentication-system",
            "version": get_settings().app_version,
            "database": db_health,
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "uptime_seconds": psutil.boot_time()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes deployment
    
    Returns:
        Readiness status
    """
    # Add checks for:
    # - Database connectivity
    # - Redis connectivity
    # - Essential services
    
    checks = {
        "database": await _check_database(),
        "cache": await _check_redis(),
        "email_service": await _check_email_service()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes deployment
    
    Returns:
        Liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


async def _check_database() -> bool:
    """Check database connectivity"""
    try:
        health_status = await check_database_health()
        return health_status["status"] == "healthy"
    except Exception:
        return False


async def _check_redis() -> bool:
    """Check Redis connectivity"""
    try:
        # TODO: Implement actual Redis health check
        await asyncio.sleep(0.01)  # Simulate check
        return True
    except Exception:
        return False


async def _check_email_service() -> bool:
    """Check email service availability"""
    try:
        # TODO: Implement actual email service check
        await asyncio.sleep(0.01)  # Simulate check
        return True
    except Exception:
        return False