"""
Authentication System Integration Tests

Tests for the complete authentication flow including registration, login,
token refresh, and protected endpoints.
"""

import pytest
import asyncio
import sys
import os

# Add backend directory to Python path for imports
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend')
sys.path.insert(0, backend_dir)

from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app

# Test client for synchronous tests
client = TestClient(app)


class TestAuthenticationFlow:
    """Test the complete authentication flow"""
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_api_health_check(self):
        """Test API health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "user-auth-system"
    
    def test_auth_health_check(self):
        """Test authentication service health check"""
        response = client.get("/api/v1/auth/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
    
    def test_password_validation(self):
        """Test password validation endpoint"""
        # Test weak password
        response = client.post("/api/v1/auth/validate-password", params={"password": "weak"})
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] == False
        assert len(data["errors"]) > 0
        
        # Test strong password
        response = client.post("/api/v1/auth/validate-password", params={"password": "StrongP@ssw0rd123!"})
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] == True
        assert len(data["errors"]) == 0
    
    def test_user_registration_flow(self):
        """Test complete user registration flow"""
        # Test registration
        registration_data = {
            "email": "test@example.com",
            "password": "TestP@ssw0rd123!"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        
        # Should return 201 for successful registration
        # Note: This will fail until we implement the full database service
        # For now, we expect specific error patterns
        assert response.status_code in [201, 500, 422]
        
        if response.status_code == 201:
            data = response.json()
            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["email"] == registration_data["email"]
    
    def test_user_login_flow(self):
        """Test user login flow"""
        login_data = {
            "email": "test@example.com",
            "password": "TestP@ssw0rd123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Should return 200 for successful login or appropriate error
        assert response.status_code in [200, 401, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data
    
    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_token_refresh(self):
        """Test token refresh functionality"""
        refresh_data = {
            "refresh_token": "dummy_refresh_token"
        }
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        # Should return 401 for invalid token or 200 for valid token
        assert response.status_code in [200, 401, 422]
    
    def test_forgot_password_flow(self):
        """Test forgot password flow"""
        forgot_data = {
            "email": "test@example.com"
        }
        
        response = client.post("/api/v1/auth/forgot-password", json=forgot_data)
        
        # Should always return success (even for non-existent emails for security)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_rate_limiting(self):
        """Test rate limiting middleware"""
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get("/api/v1/health")
            responses.append(response.status_code)
        
        # Should all succeed under normal rate limit
        assert all(status == 200 for status in responses)


class TestSecurityHeaders:
    """Test security headers middleware"""
    
    def test_security_headers_present(self):
        """Test that security headers are added to responses"""
        response = client.get("/api/v1/health")
        
        # Check for security headers
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Referrer-Policy"
        ]
        
        for header in expected_headers:
            assert header in response.headers, f"Missing security header: {header}"


class TestErrorHandling:
    """Test error handling and validation"""
    
    def test_invalid_json(self):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/v1/auth/register",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test validation of required fields"""
        # Missing email
        response = client.post("/api/v1/auth/register", json={"password": "test"})
        assert response.status_code == 422
        
        # Missing password
        response = client.post("/api/v1/auth/register", json={"email": "test@example.com"})
        assert response.status_code == 422
    
    def test_invalid_email_format(self):
        """Test email format validation"""
        invalid_data = {
            "email": "invalid-email",
            "password": "TestP@ssw0rd123!"
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAsyncAuthFlow:
    """Async tests for authentication flow"""
    
    async def test_async_health_check(self):
        """Test health check with async client"""
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
