#!/usr/bin/env python3
"""
Test Email Functionality

This script tests the email sending functionality to debug password reset issues.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.email_service import send_password_reset_email, email_service
from app.core.config import settings


async def test_email_config():
    """Test email configuration and sending"""
    print("=== Email Configuration Test ===")
    print(f"SMTP Host: {settings.SMTP_HOST}")
    print(f"SMTP Port: {settings.SMTP_PORT}")
    print(f"SMTP Username: {settings.SMTP_USERNAME}")
    print(f"SMTP Password: {'*' * len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 'Not set'}")
    print(f"From Email: {settings.FROM_EMAIL}")
    print(f"From Name: {settings.FROM_NAME}")
    print(f"Use TLS: {settings.SMTP_USE_TLS}")
    print(f"Use SSL: {settings.SMTP_USE_SSL}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    print(f"Email Templates Dir: {settings.EMAIL_TEMPLATES_DIR}")
    print()
    
    # Test SMTP connection
    print("=== Testing SMTP Connection ===")
    try:
        connection_result = await email_service.test_connection()
        print(f"SMTP Connection Test: {'✅ SUCCESS' if connection_result else '❌ FAILED'}")
    except Exception as e:
        print(f"SMTP Connection Test: ❌ ERROR - {e}")
    print()
    
    # Test password reset email
    print("=== Testing Password Reset Email ===")
    test_email = "goutham.kasula1@marist.edu"
    test_token = "test-reset-token-123456"
    test_user = "Test User"
    
    try:
        result = await send_password_reset_email(
            user_email=test_email,
            user_name=test_user,
            reset_token=test_token
        )
        print(f"Password Reset Email: {'✅ SENT' if result else '❌ FAILED'}")
        
        if result:
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={test_token}"
            print(f"Reset Link: {reset_link}")
            
    except Exception as e:
        print(f"Password Reset Email: ❌ ERROR - {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_email_config())
