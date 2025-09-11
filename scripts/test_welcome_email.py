#!/usr/bin/env python3
"""
Test Welcome Email Script
Send a test welcome email to verify email functionality
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.email_service import send_welcome_email

async def test_welcome_email():
    """Test sending a welcome email"""
    print("🧪 Testing Welcome Email...")
    
    try:
        # Send test welcome email
        result = await send_welcome_email(
            user_email="gk.qihydepark@gmail.com",  # Your test email
            user_name="Test User",
            verification_token="test_token_123"
        )
        
        if result:
            print("✅ Welcome email sent successfully!")
        else:
            print("❌ Welcome email failed to send")
            
    except Exception as e:
        print(f"❌ Error sending welcome email: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Welcome Email Test...")
    asyncio.run(test_welcome_email())
