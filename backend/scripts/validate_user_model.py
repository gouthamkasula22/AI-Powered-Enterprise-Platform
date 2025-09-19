"""
Validate UserModel instantiation

This script validates that the UserModel can be instantiated with proper parameters
to catch any type errors.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.infrastructure.database.models import UserModel

def test_user_model_creation():
    """Test creating a user model with constructor parameters"""
    try:
        # Create a test model with all fields
        model = UserModel(
            email="test@example.com",
            username="testuser",
            password_hash="password_hash_example",
            auth_method="PASSWORD",
            auth_provider_id=None,
            first_name="Test",
            last_name="User",
            display_name="Test User",
            profile_picture_url=None,
            bio=None,
            phone_number=None,
            date_of_birth=None,
            is_active=True,
            is_verified=True,
            email_verification_token=None,
            email_verification_expires=None,  # Note field name without _at
            password_reset_token=None,
            password_reset_expires=None,  # Note field name without _at
            is_staff=False,
            is_superuser=False,
            role="user",
            failed_login_attempts=0,
            last_login=None,
            timezone="UTC",
            locale="en",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        print("✅ User model created successfully with constructor parameters")
        print(f"Email: {model.email}")
        print(f"Username: {model.username}")
        print(f"Is Active: {model.is_active}")
        return True
    except Exception as e:
        print(f"❌ Error creating user model: {e}")
        return False

if __name__ == "__main__":
    success = test_user_model_creation()
    if not success:
        sys.exit(1)