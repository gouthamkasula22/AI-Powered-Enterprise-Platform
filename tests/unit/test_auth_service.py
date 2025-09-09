"""
Authentication Service Unit Tests

Unit tests for the authentication service business logic.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.services.auth_service import AuthenticationService
from app.core.security import verify_password, create_access_token


class TestAuthenticationService:
    """Test authentication service methods"""
    
    @pytest.mark.asyncio
    async def test_password_validation(self):
        """Test password strength validation"""
        # This test doesn't require database
        
        # Test weak passwords
        weak_passwords = [
            "123",
            "password",
            "12345678",
            "abcdefgh",
            "PASSWORD"
        ]
        
        for weak_password in weak_passwords:
            from app.core.security import validate_password_strength
            result = validate_password_strength(weak_password)
            assert result["is_valid"] == False
            assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_strong_password_validation(self):
        """Test strong password validation"""
        strong_passwords = [
            "StrongP@ssw0rd123!",
            "MyVeryS3cureP@ssword!",
            "C0mpl3x$Password2024"
        ]
        
        for strong_password in strong_passwords:
            from app.core.security import validate_password_strength
            result = validate_password_strength(strong_password)
            assert result["is_valid"] == True
            assert len(result["errors"]) == 0
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        from app.core.security import get_password_hash, verify_password
        
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Verify correct password
        assert verify_password(password, hashed) == True
        
        # Verify incorrect password
        assert verify_password("wrong_password", hashed) == False
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        from app.core.security import create_access_token, verify_token
        
        user_id = "test_user_123"
        token = create_access_token(subject=user_id)
        
        # Verify token
        decoded_user_id = verify_token(token)
        assert decoded_user_id == user_id
    
    def test_expired_token_verification(self):
        """Test verification of expired token"""
        from app.core.security import create_access_token, verify_token
        
        user_id = "test_user_123"
        
        # Create token that expires immediately
        token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-1))
        
        # Should return None for expired token
        decoded_user_id = verify_token(token)
        assert decoded_user_id is None
    
    def test_invalid_token_verification(self):
        """Test verification of invalid token"""
        from app.core.security import verify_token
        
        # Test completely invalid token
        assert verify_token("invalid_token") is None
        
        # Test malformed JWT
        assert verify_token("header.payload.signature") is None


class TestAuthServiceMethods:
    """Test auth service methods with mocked dependencies"""
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.get_user_by_email')
    @patch('app.services.auth_service.create_user')
    @patch('app.services.auth_service.create_user_session')
    @patch('app.services.auth_service.log_login_attempt')
    async def test_user_registration_success(self, mock_log, mock_session, mock_create, mock_get):
        """Test successful user registration"""
        # Mock user doesn't exist
        mock_get.return_value = None
        
        # Mock user creation
        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.created_at = datetime.utcnow()
        mock_create.return_value = mock_user
        
        # Mock session creation
        mock_session.return_value = Mock()
        mock_log.return_value = None
        
        # Test registration
        result = await AuthenticationService.register_user(
            email="test@example.com",
            password="StrongP@ssw0rd123!",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify result structure
        assert "user" in result
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user"]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.get_user_by_email')
    async def test_user_registration_duplicate_email(self, mock_get):
        """Test registration with existing email"""
        # Mock user already exists
        mock_get.return_value = Mock(email="test@example.com")
        
        # Test registration should raise exception
        with pytest.raises(Exception):  # Would be a custom exception in real implementation
            await AuthenticationService.register_user(
                email="test@example.com",
                password="StrongP@ssw0rd123!",
                ip_address="127.0.0.1",
                user_agent="test-agent"
            )


class TestSecurityUtilities:
    """Test security utility functions"""
    
    def test_device_fingerprint_generation(self):
        """Test device fingerprint generation"""
        from app.core.security import generate_device_fingerprint
        
        ip_address = "192.168.1.1"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        fingerprint = generate_device_fingerprint(ip_address, user_agent)
        
        # Should be a consistent hash
        assert isinstance(fingerprint, str)
        assert len(fingerprint) > 0
        
        # Same inputs should produce same fingerprint
        fingerprint2 = generate_device_fingerprint(ip_address, user_agent)
        assert fingerprint == fingerprint2
        
        # Different inputs should produce different fingerprint
        fingerprint3 = generate_device_fingerprint("192.168.1.2", user_agent)
        assert fingerprint != fingerprint3


class TestPasswordPolicies:
    """Test password policy enforcement"""
    
    def test_password_requirements(self):
        """Test various password requirements"""
        from app.core.security import validate_password_strength
        
        test_cases = [
            # (password, should_be_valid, expected_error_count)
            ("", False, 4),  # All requirements fail
            ("abc", False, 3),  # Too short, no uppercase, no digits, no special
            ("abcdefgh", False, 3),  # No uppercase, no digits, no special
            ("Abcdefgh", False, 2),  # No digits, no special
            ("Abcdefg1", False, 1),  # No special
            ("Abcdefg!", False, 1),  # No digits
            ("Abcdefg1!", True, 0),  # All requirements met
            ("MyStr0ng!Pass", True, 0),  # Strong password
        ]
        
        for password, should_be_valid, expected_errors in test_cases:
            result = validate_password_strength(password)
            assert result["is_valid"] == should_be_valid
            if not should_be_valid:
                assert len(result["errors"]) >= expected_errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
