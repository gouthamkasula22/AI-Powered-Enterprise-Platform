"""
Authentication Service Unit Tests - Clean Architecture

Unit tests for the new clean architecture authentication services.
Tests password validation, JWT tokens, and authentication business logic.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add backend to path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_path)

# New architecture imports
from src.domain.value_objects.password import Password, PasswordValidationException
from src.infrastructure.security.jwt_service import JWTService, TokenType, SecurityUtils
from src.domain.services.authentication_service import AuthenticationService


class TestPasswordValueObject:
    """Test Password value object functionality"""
    
    def test_password_validation_weak_passwords(self):
        """Test password strength validation for weak passwords"""
        weak_passwords = [
            "123",          # Too short
            "password",     # No uppercase, digits, special chars
            "12345678",     # No letters or special chars
            "abcdefgh",     # No uppercase, digits, special chars
            "PASSWORD",     # No lowercase, digits, special chars
            "Password",     # No digits or special chars
            "Password1",    # No special chars
        ]
        
        for weak_password in weak_passwords:
            with pytest.raises(PasswordValidationException):
                Password(weak_password)
    
    def test_password_validation_strong_passwords(self):
        """Test password strength validation for strong passwords"""
        strong_passwords = [
            "StrongP@ssw0rd123!",
            "MyVeryS3cureP@ssword!",
            "C0mpl3x$Password2024",
            "Test123!@#",
            "Abc123!@#"
        ]
        
        for strong_password in strong_passwords:
            # Should not raise exception
            password = Password(strong_password)
            assert password.value == strong_password
    
    def test_password_hashing_and_verification(self):
        """Test password hashing and verification"""
        password_value = "TestPassword123!"
        password = Password(password_value)
        
        # Hash the password
        hashed = password.hash()
        
        # Verify correct password
        assert Password.verify(hashed, password_value) == True
        
        # Verify incorrect password
        assert Password.verify(hashed, "wrong_password") == False
    
    def test_password_meets_requirements(self):
        """Test internal password requirements checking"""
        # Test that static method works correctly
        assert Password._meets_requirements("StrongP@ssw0rd123!") == True
        assert Password._meets_requirements("weak") == False
        assert Password._meets_requirements("NoSpecialChar123") == False


class TestJWTService:
    """Test JWT service functionality"""
    
    def setUp(self):
        """Set up JWT service for testing"""
        self.jwt_service = JWTService(
            secret_key="test-secret-key-for-testing",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        self.setUp()
        
        user_id = 123
        email = "test@example.com"
        
        # Create access token
        token = self.jwt_service.create_access_token(user_id, email)
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        token_data = self.jwt_service.decode_token(token)
        assert token_data is not None
        assert token_data.user_id == user_id
        assert token_data.email == email
        assert token_data.token_type == TokenType.ACCESS
    
    def test_expired_token_verification(self):
        """Test verification of expired token"""
        # Create JWT service with very short expiration
        jwt_service = JWTService(
            secret_key="test-secret-key",
            algorithm="HS256",
            access_token_expire_minutes=-1  # Already expired
        )
        
        user_id = 123
        email = "test@example.com"
        
        # Create expired token
        token = jwt_service.create_access_token(user_id, email)
        
        # Should return None for expired token
        token_data = jwt_service.decode_token(token)
        assert token_data is None
    
    def test_invalid_token_verification(self):
        """Test verification of invalid token"""
        self.setUp()
        
        # Test completely invalid token
        token_data = self.jwt_service.decode_token("invalid_token")
        assert token_data is None
        
        # Test malformed JWT
        token_data = self.jwt_service.decode_token("header.payload.signature")
        assert token_data is None
    
    def test_refresh_token_creation(self):
        """Test refresh token creation"""
        self.setUp()
        
        user_id = 123
        email = "test@example.com"
        
        # Create refresh token
        token = self.jwt_service.create_refresh_token(user_id, email)
        assert isinstance(token, str)
        
        # Decode and verify token type
        token_data = self.jwt_service.decode_token(token)
        assert token_data is not None
        assert token_data.token_type == TokenType.REFRESH
    
    def test_verification_token_creation(self):
        """Test email verification token creation"""
        self.setUp()
        
        user_id = 123
        email = "test@example.com"
        
        # Create verification token
        token = self.jwt_service.create_verification_token(user_id, email)
        assert isinstance(token, str)
        
        # Decode and verify token type
        token_data = self.jwt_service.decode_token(token)
        assert token_data is not None
        assert token_data.token_type == TokenType.EMAIL_VERIFICATION


class TestSecurityUtilities:
    """Test security utility functions"""
    
    def test_secure_token_generation(self):
        """Test secure token generation"""
        token = SecurityUtils.generate_secure_token(32)
        
        # Should be a string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Different calls should produce different tokens
        token2 = SecurityUtils.generate_secure_token(32)
        assert token != token2
    
    def test_verification_code_generation(self):
        """Test verification code generation"""
        code = SecurityUtils.generate_verification_code(6)
        
        # Should be 6 digits
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isdigit()
        
        # Different calls should produce different codes
        code2 = SecurityUtils.generate_verification_code(6)
        assert code != code2  # Very unlikely to be the same
    
    def test_constant_time_compare(self):
        """Test constant-time string comparison"""
        string1 = "test_string"
        string2 = "test_string"
        string3 = "different_string"
        
        # Same strings should compare equal
        assert SecurityUtils.constant_time_compare(string1, string2) == True
        
        # Different strings should compare unequal
        assert SecurityUtils.constant_time_compare(string1, string3) == False


class TestPasswordPolicies:
    """Test password policy enforcement"""
    
    def test_password_requirements_comprehensive(self):
        """Test various password requirements comprehensively"""
        test_cases = [
            # (password, should_be_valid, description)
            ("", False, "Empty password"),
            ("abc", False, "Too short"),
            ("abcdefgh", False, "No uppercase, digits, special chars"),
            ("Abcdefgh", False, "No digits, special chars"),
            ("Abcdefg1", False, "No special chars"),
            ("Abcdefg!", False, "No digits"),
            ("ABCDEFG1!", False, "No lowercase"),
            ("abcdefg1!", False, "No uppercase"),
            ("Abcdefg1!", True, "All requirements met"),
            ("MyStr0ng!Pass", True, "Strong password"),
            ("Test123!@#", True, "Minimum strong password"),
        ]
        
        for password, should_be_valid, description in test_cases:
            if should_be_valid:
                # Should not raise exception
                password_obj = Password(password)
                assert password_obj.value == password, f"Failed for: {description}"
            else:
                # Should raise exception
                with pytest.raises(PasswordValidationException):
                    Password(password)


@pytest.mark.asyncio
class TestAuthenticationServiceMocking:
    """Test authentication service methods with mocked dependencies"""
    
    async def test_password_validation_integration(self):
        """Test that authentication service properly validates passwords"""
        # This would test integration with Password value object
        # when creating or changing passwords
        
        # For now, just test that Password validation works as expected
        with pytest.raises(PasswordValidationException):
            Password("weak")
        
        # Strong password should work
        strong_password = Password("StrongP@ssw0rd123!")
        assert strong_password.value == "StrongP@ssw0rd123!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])