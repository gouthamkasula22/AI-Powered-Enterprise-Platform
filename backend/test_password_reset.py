#!/usr/bin/env python3
"""
Test Password Reset Email Template

Test the actual password reset email function with template rendering.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.email_service import send_password_reset_email
from app.core.config import settings


async def test_password_reset_email():
    """Test the password reset email function"""
    print("=== Password Reset Email Test ===")
    print(f"From Email: {settings.FROM_EMAIL}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    print(f"Templates Dir: {settings.EMAIL_TEMPLATES_DIR}")
    print()
    
    try:
        print("Sending password reset email...")
        result = await send_password_reset_email(
            user_email="goutham.kasula1@marist.edu",
            user_name="Goutham Kasula",
            reset_token="test-reset-token-12345"
        )
        
        if result:
            print("✅ Password reset email sent successfully!")
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token=test-reset-token-12345"
            print(f"Reset link: {reset_link}")
        else:
            print("❌ Password reset email failed to send")
            
        return result
        
    except Exception as e:
        print(f"❌ Error sending password reset email: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_password_reset_email())
