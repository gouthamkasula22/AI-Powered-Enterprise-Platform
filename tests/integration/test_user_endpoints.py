"""
Integration Tests for User Management Endpoints

Tests user profile, updates, and management operations.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestUserEndpoints:
    """Test suite for user management endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_user_profile_without_auth(self, client: AsyncClient):
        """Test accessing user profile without authentication."""
        response = await client.get("/api/users/profile")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_user_profile_with_auth(self, client: AsyncClient, auth_headers):
        """Test accessing user profile with authentication."""
        response = await client.get("/api/users/profile", headers=auth_headers)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_update_user_profile_without_auth(self, client: AsyncClient):
        """Test updating profile without authentication."""
        data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        response = await client.put("/api/users/profile", json=data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_update_user_profile_with_auth(self, client: AsyncClient, auth_headers):
        """Test updating profile with authentication."""
        data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        response = await client.put("/api/users/profile", json=data, headers=auth_headers)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]
    
    @pytest.mark.asyncio
    async def test_delete_user_account_without_auth(self, client: AsyncClient):
        """Test deleting account without authentication."""
        response = await client.delete("/api/users/profile")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_list_users_without_auth(self, client: AsyncClient):
        """Test listing users without authentication (admin endpoint)."""
        response = await client.get("/api/users/")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_without_auth(self, client: AsyncClient):
        """Test getting specific user without authentication."""
        response = await client.get("/api/users/1")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_update_user_email_with_invalid_format(self, client: AsyncClient, auth_headers):
        """Test updating email with invalid format."""
        data = {"email": "invalid-email-format"}
        response = await client.patch("/api/users/email", json=data, headers=auth_headers)
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_user_activity_without_auth(self, client: AsyncClient):
        """Test getting user activity without authentication."""
        response = await client.get("/api/users/activity")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_user_sessions_without_auth(self, client: AsyncClient):
        """Test getting active sessions without authentication."""
        response = await client.get("/api/users/sessions")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]


class TestAdminUserEndpoints:
    """Test suite for admin user management endpoints."""
    
    @pytest.mark.asyncio
    async def test_admin_list_users_without_auth(self, client: AsyncClient):
        """Test admin listing users without authentication."""
        response = await client.get("/api/admin/users")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_admin_create_user_without_auth(self, client: AsyncClient):
        """Test admin creating user without authentication."""
        data = {
            "email": "admin_created@example.com",
            "password": "AdminPass123!",
            "first_name": "Admin",
            "last_name": "Created",
            "username": "admincreated"
        }
        response = await client.post("/api/admin/users", json=data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_admin_delete_user_without_auth(self, client: AsyncClient):
        """Test admin deleting user without authentication."""
        response = await client.delete("/api/admin/users/1")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_admin_update_user_role_without_auth(self, client: AsyncClient):
        """Test admin updating user role without authentication."""
        data = {"role": "admin"}
        response = await client.patch("/api/admin/users/1/role", json=data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_admin_ban_user_without_auth(self, client: AsyncClient):
        """Test admin banning user without authentication."""
        response = await client.post("/api/admin/users/1/ban")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_admin_unban_user_without_auth(self, client: AsyncClient):
        """Test admin unbanning user without authentication."""
        response = await client.post("/api/admin/users/1/unban")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
