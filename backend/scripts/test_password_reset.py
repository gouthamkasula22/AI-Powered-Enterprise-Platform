#!/usr/bin/env python3
"""
Test password reset functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

# Also add the backend directory for local modules
sys.path.insert(0, str(backend_dir))

from infrastructure.database.database import get_db_session
from infrastructure.database.repositories import SqlUserRepository
from infrastructure.security.jwt_service import JWTService, AuthenticationService, TokenBlacklistService
from infrastructure.email.email_service import SMTPEmailService
from application.use_cases.auth_use_cases import AuthenticationUseCases
from application.dto import RegisterRequestDTO, PasswordResetRequestDTO
from shared.config import get_settings
from domain.value_objects import Email, Password


async def test_password_reset():
    """Test the complete password reset flow"""
    print("Testing password reset functionality...")
    
    # Get settings
    settings = get_settings()
    
    # Setup services
    async for db in get_db_session():
        user_repo = SqlUserRepository(db)
        
        jwt_service = JWTService(
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
            refresh_token_expire_days=settings.jwt_refresh_token_expire_days
        )
        
        # Mock blacklist service for testing
        class MockBlacklistService:
            async def is_blacklisted(self, token: str) -> bool:
                return False
            async def blacklist_token(self, token: str, expires_at: int) -> None:
                pass
        
        blacklist_service = MockBlacklistService()
        auth_service = AuthenticationService(jwt_service, blacklist_service)
        
        email_service = SMTPEmailService(
            smtp_server=settings.smtp_host,
            smtp_port=settings.smtp_port,
            username=settings.smtp_username or "",
            password=settings.smtp_password or ""
        )
        
        # Template service is None for now
        auth_use_cases = AuthenticationUseCases(user_repo, auth_service, email_service, None)
        
        # Test email
        test_email = "testuser@example.com"
        
        try:
            # First, register a test user
            print(f"Registering test user: {test_email}")
            register_dto = RegisterRequestDTO(
                email=test_email,
                password="TestPassword123!",
                first_name="Test",
                last_name="User",
                username="testuser"
            )
            
            try:
                await auth_use_cases.register_user(register_dto)
                print("✓ User registered successfully")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✓ User already exists, proceeding with test")
                else:
                    print(f"✗ Registration failed: {e}")
                    return
            
            # Now test password reset
            print(f"Initiating password reset for: {test_email}")
            reset_dto = PasswordResetRequestDTO(email=test_email)
            
            result = await auth_use_cases.initiate_password_reset(reset_dto)
            print(f"✓ Password reset initiated: {result.message}")
            
            # Check if user has reset token
            user = await user_repo.find_by_email(Email(test_email))
            if user and user.password_reset_token:
                print(f"✓ Reset token generated: {user.password_reset_token[:10]}...")
                print(f"✓ Reset expires: {user.password_reset_expires}")
            else:
                print("✗ No reset token found in user record")
            
        except Exception as e:
            print(f"✗ Error during password reset test: {e}")
            import traceback
            traceback.print_exc()
        
        break


if __name__ == "__main__":
    asyncio.run(test_password_reset())