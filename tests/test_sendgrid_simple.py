#!/usr/bin/env python3
"""
Simple SendGrid Test using emails library
This bypasses aiosmtplib TLS issues by using the emails library directly.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to path so we can import our modules
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Set the working directory to backend so .env file is found
os.chdir(str(backend_path))

from app.core.config import settings
import emails


def test_sendgrid_simple():
    """Test SendGrid using the emails library directly"""
    print("🔧 Simple SendGrid Test")
    print("=" * 50)
    
    # Check configuration
    print(f"SMTP Host: {settings.SMTP_HOST}")
    print(f"SMTP Port: {settings.SMTP_PORT}")
    print(f"SMTP Username: {settings.SMTP_USERNAME}")
    print(f"From Email: {settings.FROM_EMAIL}")
    print()
    
    if not all([settings.SMTP_HOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]):
        print("❌ Missing SMTP configuration!")
        return False
    
    # Test recipient email
    recipient = input("Enter test recipient email: ").strip()
    if not recipient:
        print("❌ No recipient provided!")
        return False
    
    print(f"📧 Sending test email to: {recipient}")
    
    # Create simple test email
    html_content = """
    <html>
        <body>
            <h2>🎉 SendGrid Test Email</h2>
            <p>Congratulations! Your SendGrid configuration is working.</p>
            <p>This email was sent from your User Authentication System.</p>
            <hr>
            <p><small>Test sent via emails library</small></p>
        </body>
    </html>
    """
    
    text_content = """
    🎉 SendGrid Test Email
    
    Congratulations! Your SendGrid configuration is working.
    This email was sent from your User Authentication System.
    
    ---
    Test sent via emails library
    """
    
    try:
        # Create email message
        message = emails.html(
            html=html_content,
            text=text_content,
            subject="🔧 SendGrid Test Email",
            mail_from=(settings.FROM_NAME, settings.FROM_EMAIL)
        )
        
        # Send using SendGrid SMTP
        smtp_config = {
            'host': settings.SMTP_HOST,
            'port': settings.SMTP_PORT,
            'tls': settings.SMTP_USE_TLS,
            'ssl': settings.SMTP_USE_SSL,
            'user': settings.SMTP_USERNAME,
            'password': settings.SMTP_PASSWORD
        }
        
        print("🚀 Sending email...")
        response = message.send(to=recipient, smtp=smtp_config)
        
        if response.status_code == 250:
            print("✅ Email sent successfully!")
            print(f"Status: {response.status_code}")
            return True
        else:
            print(f"❌ Email sending failed!")
            print(f"Status: {response.status_code}")
            print(f"Response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        
        # Check for common issues
        if "authentication" in str(e).lower():
            print("\n💡 Possible issues:")
            print("1. Check if your SendGrid API key is correct")
            print("2. Verify API key has 'Mail Send' permissions")
        elif "sender" in str(e).lower() or "from" in str(e).lower():
            print("\n💡 Possible issues:")
            print("1. Verify your sender email in SendGrid Dashboard")
            print("2. Go to Settings → Sender Authentication")
            print("3. Click 'Verify a Single Sender'")
        elif "recipient" in str(e).lower():
            print("\n💡 Possible issue:")
            print("1. Check if recipient email is valid")
        
        return False


if __name__ == "__main__":
    print("🚀 Starting simple SendGrid test...")
    try:
        test_sendgrid_simple()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
