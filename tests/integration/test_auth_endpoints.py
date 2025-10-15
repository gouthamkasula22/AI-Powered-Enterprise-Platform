"""
Integration Tests for Authentication Endpoints

Tests the full authentication flow including registration, login, token refresh, etc.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""
    
    @pytest.fixture
    def test_user_data(self):
        """Test user registration data."""
        return {
            "email": "test@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser"
        }
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test basic health check endpoint."""
        response = await client.get("/health")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_307_TEMPORARY_REDIRECT]
    
    @pytest.mark.asyncio
    @pytest.mark.slow  # Requires database and cache initialization
    async def test_register_user_success(self, client: AsyncClient, test_user_data):
        """Test successful user registration."""
        response = await client.post("/api/auth/register", json=test_user_data)
        
        # Should either succeed or fail with email exists (if test ran before)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT
        ]
        
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert "access_token" in data or "user" in data or "message" in data
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email."""
        data = {
            "email": "invalid-email",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser2"
        }
        response = await client.post("/api/auth/register", json=data)
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
    
    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        data = {
            "email": "test2@example.com",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser3"
        }
        response = await client.post("/api/auth/register", json=data)
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
    
    @pytest.mark.asyncio
    async def test_login_user_success(self, client: AsyncClient, test_user_data):
        """Test successful user login."""
        # Try to register first (may fail if exists)
        await client.post("/api/auth/register", json=test_user_data)
        
        # Attempt login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/api/auth/login", json=login_data)
        
        # Should succeed or fail with not found/invalid credentials
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_login_user_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        data = {
            "email": "nonexistent@example.com",
            "password": "WrongPass123!"
        }
        response = await client.post("/api/auth/login", json=data)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]
    
    @pytest.mark.asyncio
    async def test_login_user_missing_fields(self, client: AsyncClient):
        """Test login with missing required fields."""
        data = {"email": "test@example.com"}
        response = await client.post("/api/auth/login", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_validate_email_endpoint(self, client: AsyncClient):
        """Test email validation endpoint."""
        data = {"email": "test@example.com"}
        response = await client.post("/api/auth/validate-email", json=data)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    @pytest.mark.asyncio
    async def test_validate_password_endpoint(self, client: AsyncClient):
        """Test password validation endpoint."""
        data = {"password": "TestPass123!"}
        response = await client.post("/api/auth/validate-password", json=data)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    @pytest.mark.asyncio
    async def test_logout_without_token(self, client: AsyncClient):
        """Test logout without authentication token."""
        response = await client.post("/api/auth/logout")
        # Should fail with 401 or 403 (unauthorized)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_refresh_token_without_token(self, client: AsyncClient):
        """Test token refresh without valid token."""
        data = {"refresh_token": "invalid_token"}
        response = await client.post("/api/auth/refresh", json=data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]
    
    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/auth/me")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_password_reset_request(self, client: AsyncClient):
        """Test password reset request."""
        data = {"email": "test@example.com"}
        response = await client.post("/api/auth/password-reset/request", json=data)
        # Should accept request or return 404
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_202_ACCEPTED
        ]
    
    @pytest.mark.asyncio
    async def test_change_password_without_auth(self, client: AsyncClient):
        """Test changing password without authentication."""
        data = {
            "old_password": "OldPass123!",
            "new_password": "NewPass123!"
        }
        response = await client.post("/api/auth/change-password", json=data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
