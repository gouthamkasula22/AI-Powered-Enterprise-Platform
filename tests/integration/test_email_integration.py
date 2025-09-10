"""
Email Integration Tests

Test email functionality in the authentication flow including registration
emails, verification links, and resend functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.services.auth_service import AuthenticationService
from app.services.email_service import send_welcome_email, send_verification_email
from app.models import User
from app.core.database import get_db_session
from app.core.security import generate_random_token


class TestEmailIntegration:
    """Test email integration with authentication flow"""
    
    @pytest.mark.asyncio
    async def test_registration_sends_welcome_email(self):
        """Test that user registration automatically sends welcome email"""
        with patch('app.services.email_service.send_welcome_email') as mock_send_email:
            mock_send_email.return_value = True
            
            # Mock user registration
            result = await AuthenticationService.register_user(
                email="test@example.com",
                password="TestPassword123!",
                ip_address="127.0.0.1",
                user_agent="test-agent"
            )
            
            # Verify email was called
            mock_send_email.assert_called_once()
            args, kwargs = mock_send_email.call_args
            assert kwargs['user_email'] == "test@example.com"
            assert 'verification_token' in kwargs
    
    @pytest.mark.asyncio
    async def test_email_verification_workflow(self):
        """Test complete email verification workflow"""
        # Test data
        verification_token = generate_random_token(32)
        
        with patch('app.core.database.get_db_session') as mock_session:
            # Mock database session and user
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.is_verified = False
            mock_user.email_verification_token = verification_token
            mock_user.email_verification_expires = datetime.utcnow() + timedelta(hours=12)
            
            mock_session_instance = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Test verification
            result = await AuthenticationService.verify_email(verification_token)
            
            # Verify result
            assert result["message"] == "Email verified successfully"
            assert result["user"]["email"] == "test@example.com"
            assert result["user"]["is_verified"] == True
            
            # Verify user was updated
            assert mock_user.is_verified == True
            assert mock_user.email_verification_token is None
            assert mock_user.email_verification_expires is None
    
    @pytest.mark.asyncio
    async def test_resend_verification_email(self):
        """Test resending verification email"""
        with patch('app.services.email_service.send_welcome_email') as mock_send_email:
            with patch('app.core.database.get_db_session') as mock_session:
                mock_send_email.return_value = True
                
                # Mock database session and user
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.email = "test@example.com"
                mock_user.is_verified = False
                
                mock_session_instance = MagicMock()
                mock_session.return_value.__aenter__.return_value = mock_session_instance
                mock_session_instance.execute.return_value.scalar_one_or_none.return_value = mock_user
                
                # Test resend
                result = await AuthenticationService.resend_verification_email("test@example.com")
                
                # Verify result
                assert "resent" in result["message"].lower()
                
                # Verify email was called
                mock_send_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_email_service_template_rendering(self):
        """Test that email templates render correctly"""
        with patch('app.services.email_service.email_service.send_template_email') as mock_send:
            mock_send.return_value = True
            
            # Test welcome email
            result = await send_welcome_email(
                user_email="test@example.com",
                user_name="testuser",
                verification_token="test_token_123"
            )
            
            # Verify email service was called with correct parameters
            mock_send.assert_called_once()
            
            # Get the call arguments
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs['to_email'] == "test@example.com"
            assert call_kwargs['template_name'] == "welcome"
            assert "Welcome" in call_kwargs['subject']
            
            # Verify context contains required data
            context = call_kwargs['context']
            assert context['user_name'] == "testuser"
            assert "test_token_123" in context['verification_link']
    
    @pytest.mark.asyncio
    async def test_expired_verification_token(self):
        """Test handling of expired verification tokens"""
        with patch('app.core.database.get_db_session') as mock_session:
            # Mock database session and user with expired token
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.is_verified = False
            mock_user.email_verification_token = "expired_token"
            mock_user.email_verification_expires = datetime.utcnow() - timedelta(hours=1)  # Expired
            
            mock_session_instance = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Test verification with expired token
            with pytest.raises(Exception) as exc_info:
                await AuthenticationService.verify_email("expired_token")
            
            assert "expired" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_verification_token(self):
        """Test handling of invalid verification tokens"""
        with patch('app.core.database.get_db_session') as mock_session:
            # Mock database session returning no user
            mock_session_instance = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.execute.return_value.scalar_one_or_none.return_value = None
            
            # Test verification with invalid token
            with pytest.raises(Exception) as exc_info:
                await AuthenticationService.verify_email("invalid_token")
            
            assert "invalid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_already_verified_email(self):
        """Test handling of already verified emails"""
        with patch('app.core.database.get_db_session') as mock_session:
            # Mock database session and already verified user
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.is_verified = True
            mock_user.email_verification_token = "test_token"
            mock_user.email_verification_expires = datetime.utcnow() + timedelta(hours=1)
            
            mock_session_instance = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Test verification
            result = await AuthenticationService.verify_email("test_token")
            
            # Verify result
            assert "already verified" in result["message"].lower()
            assert result["user"]["is_verified"] == True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
