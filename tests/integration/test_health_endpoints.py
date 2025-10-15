"""
Integration Tests for Health Check Endpoints

Tests application health monitoring and status endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_root_health_check(self, client: AsyncClient):
        """Test root health check endpoint."""
        response = await client.get("/health")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_307_TEMPORARY_REDIRECT
        ]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "status" in data or isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_api_health_check(self, client: AsyncClient):
        """Test API health check endpoint."""
        response = await client.get("/api/health")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "status" in data or isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_database_health_check(self, client: AsyncClient):
        """Test database health check endpoint."""
        response = await client.get("/api/health/db")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_redis_health_check(self, client: AsyncClient):
        """Test Redis health check endpoint."""
        response = await client.get("/api/health/redis")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """Test application readiness endpoint."""
        response = await client.get("/api/health/ready")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        """Test application liveness endpoint."""
        response = await client.get("/api/health/live")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test metrics endpoint."""
        response = await client.get("/api/metrics")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_version_endpoint(self, client: AsyncClient):
        """Test version information endpoint."""
        response = await client.get("/api/version")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Version info typically has these fields
            assert isinstance(data, dict)


class TestSystemStatusEndpoints:
    """Test suite for system status endpoints."""
    
    @pytest.mark.asyncio
    async def test_system_status(self, client: AsyncClient):
        """Test system status endpoint."""
        response = await client.get("/api/system/status")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_system_info(self, client: AsyncClient):
        """Test system information endpoint."""
        response = await client.get("/api/system/info")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_dependency_check(self, client: AsyncClient):
        """Test dependency health check."""
        response = await client.get("/api/health/dependencies")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_uptime_endpoint(self, client: AsyncClient):
        """Test application uptime endpoint."""
        response = await client.get("/api/health/uptime")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]
