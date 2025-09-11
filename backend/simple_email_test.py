#!/usr/bin/env python3
"""
Simple Email Test Script

Test basic email sending using the configured SMTP settings.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings


def test_simple_email():
    """Test basic SMTP email sending"""
    print("=== Simple SMTP Email Test ===")
    print(f"SMTP Host: {settings.SMTP_HOST}")
    print(f"SMTP Port: {settings.SMTP_PORT}")
    print(f"SMTP Username: {settings.SMTP_USERNAME}")
    print(f"From Email: {settings.FROM_EMAIL}")
    print(f"SMTP TLS: {settings.SMTP_USE_TLS}")
    print()
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = "goutham.kasula1@marist.edu"
        msg['Subject'] = "Test Email from Authentication System"
        
        body = """
        This is a test email from your User Authentication System.
        
        If you receive this email, the SMTP configuration is working correctly.
        
        Test details:
        - SMTP Host: {smtp_host}
        - From Email: {from_email}
        - Frontend URL: {frontend_url}
        
        Best regards,
        Authentication System
        """.format(
            smtp_host=settings.SMTP_HOST,
            from_email=settings.FROM_EMAIL,
            frontend_url=settings.FRONTEND_URL
        )
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server and send email
        print("Connecting to SMTP server...")
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        
        if settings.SMTP_USE_TLS:
            print("Starting TLS...")
            server.starttls()
        
        print("Logging in...")
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        print("Sending email...")
        text = msg.as_string()
        server.sendmail(settings.FROM_EMAIL, "goutham.kasula1@marist.edu", text)
        
        server.quit()
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False


if __name__ == "__main__":
    test_simple_email()
