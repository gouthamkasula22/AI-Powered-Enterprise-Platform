#!/usr/bin/env python3
"""
SMTP Configuration Helper

This script helps you configure your SMTP settings interactively.
"""

import os
import re
from pathlib import Path


def get_env_file_path():
    """Get the path to the .env file"""
    return Path(__file__).parent.parent / "backend" / ".env"


def update_env_file(smtp_config):
    """Update the .env file with new SMTP configuration"""
    env_file = get_env_file_path()
    
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current content
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update SMTP settings
    for key, value in smtp_config.items():
        pattern = rf'^{key}=.*$'
        replacement = f'{key}={value}'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Write back
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ .env file updated successfully!")
    return True


def configure_gmail():
    """Configure Gmail SMTP settings"""
    print("\n📧 Gmail SMTP Configuration")
    print("=" * 40)
    print("Before proceeding, make sure you have:")
    print("1. ✅ Enabled 2-Factor Authentication on your Gmail account")
    print("2. ✅ Generated an App Password for this application")
    print("   (Google Account → Security → 2-Step Verification → App passwords)")
    print()
    
    proceed = input("Have you completed the above steps? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Please complete the Gmail setup first, then run this script again.")
        return None
    
    email = input("Enter your Gmail address: ").strip()
    if not email or not re.match(r'^[^@]+@gmail\.com$', email):
        print("❌ Please enter a valid Gmail address (example@gmail.com)")
        return None
    
    app_password = input("Enter your 16-character App Password (no spaces): ").strip()
    if not app_password or len(app_password) != 16:
        print("❌ App Password should be exactly 16 characters")
        return None
    
    return {
        'SMTP_HOST': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': email,
        'SMTP_PASSWORD': app_password,
        'SMTP_USE_TLS': 'true',
        'SMTP_USE_SSL': 'false',
        'FROM_EMAIL': email,
        'FROM_NAME': 'User Authentication System'
    }


def configure_outlook():
    """Configure Outlook SMTP settings"""
    print("\n📧 Outlook/Hotmail SMTP Configuration")
    print("=" * 40)
    
    email = input("Enter your Outlook/Hotmail address: ").strip()
    if not email or '@' not in email:
        print("❌ Please enter a valid email address")
        return None
    
    password = input("Enter your email password: ").strip()
    if not password:
        print("❌ Password cannot be empty")
        return None
    
    return {
        'SMTP_HOST': 'smtp-mail.outlook.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': email,
        'SMTP_PASSWORD': password,
        'SMTP_USE_TLS': 'true',
        'SMTP_USE_SSL': 'false',
        'FROM_EMAIL': email,
        'FROM_NAME': 'User Authentication System'
    }


def configure_sendgrid():
    """Configure SendGrid SMTP settings"""
    print("\n📧 SendGrid SMTP Configuration")
    print("=" * 40)
    print("Before proceeding, make sure you have:")
    print("1. ✅ Created a SendGrid account")
    print("2. ✅ Generated an API Key")
    print("3. ✅ Verified a sender email address")
    print()
    
    from_email = input("Enter your verified sender email: ").strip()
    if not from_email or '@' not in from_email:
        print("❌ Please enter a valid email address")
        return None
    
    api_key = input("Enter your SendGrid API Key: ").strip()
    if not api_key:
        print("❌ API Key cannot be empty")
        return None
    
    return {
        'SMTP_HOST': 'smtp.sendgrid.net',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'apikey',
        'SMTP_PASSWORD': api_key,
        'SMTP_USE_TLS': 'true',
        'SMTP_USE_SSL': 'false',
        'FROM_EMAIL': from_email,
        'FROM_NAME': 'User Authentication System'
    }


def main():
    """Main configuration function"""
    print("🔧 SMTP Configuration Helper")
    print("=" * 50)
    print("This tool will help you configure email settings for your application.")
    print()
    
    print("Choose your email provider:")
    print("1. SendGrid (recommended for production)")
    print("2. Gmail (for development)")
    print("3. Outlook/Hotmail")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    config = None
    if choice == '1':
        config = configure_sendgrid()
    elif choice == '2':
        config = configure_gmail()
    elif choice == '3':
        config = configure_outlook()
    elif choice == '4':
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
        return
    
    if config:
        print("\n📝 Configuration Summary:")
        print("-" * 30)
        for key, value in config.items():
            if 'PASSWORD' in key:
                print(f"{key}: [HIDDEN]")
            else:
                print(f"{key}: {value}")
        
        confirm = input("\nSave this configuration? (y/n): ").strip().lower()
        if confirm == 'y':
            if update_env_file(config):
                print("\n✅ Configuration saved!")
                print("\nNext steps:")
                print("1. Restart your backend server")
                print("2. Run 'python test_smtp.py' to test the configuration")
                print("3. Try registering a new user to test email sending")
            else:
                print("❌ Failed to save configuration")
        else:
            print("Configuration not saved.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Configuration cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
