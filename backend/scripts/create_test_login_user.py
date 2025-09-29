"""
Create a test user with a known password for login testing.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password
from src.domain.value_objects.role import UserRole
from src.infrastructure.database.repositories import SqlUserRepository
from src.infrastructure.database.database import initialize_database, get_db_session

async def create_test_user():
    """Create a test user with a known password"""
    
    # Initialize the database
    await initialize_database()
    
    # Get a database session
    async for session in get_db_session():
        try:
            # Create the user repository
            user_repo = SqlUserRepository(session)
            
            # Create a test user
            email = Email("test@example.com")
            password = Password("Test123!")  # Simple password for testing
            password_hash = password.hash()
            
            # Create the user entity
            user = User(
                email=email,
                username="testuser",
                password_hash=password_hash,
                role=UserRole.USER,
                is_active=True,
                is_verified=True
            )
            
            # Save the user to the database
            await user_repo.save(user)
            
            print(f"Test user created with email: {email.value}")
            print(f"Password: Test123!")
            print(f"User ID: {user.id}")
            
            # Also create an admin user
            admin_email = Email("admin@example.com")
            admin_password = Password("Admin123!")
            admin_password_hash = admin_password.hash()
            
            # Create the admin user entity
            admin_user = User(
                email=admin_email,
                username="adminuser",
                password_hash=admin_password_hash,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                is_staff=True,
                is_superuser=True
            )
            
            # Save the admin user to the database
            await user_repo.save(admin_user)
            
            print(f"Admin user created with email: {admin_email.value}")
            print(f"Password: Admin123!")
            print(f"User ID: {admin_user.id}")
            
            await session.commit()
            
        except Exception as e:
            print(f"Error creating test user: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(create_test_user())