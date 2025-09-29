#!/usr/bin/env python3
"""
Fix Admin User Script
Sets up proper admin user with correct role in the database
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from passlib.context import CryptContext


async def fix_admin_user():
    """Fix admin user by setting proper role and ensuring admin access"""
    
    # Database connection
    engine = create_async_engine('postgresql+asyncpg://auth_user:auth_password@localhost:5433/auth_db')
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    # Password hasher
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    try:
        # First, let's check if there's a role column and add it if needed
        async with async_session() as session:
            try:
                await session.execute(text("SELECT role FROM users LIMIT 1"))
                print("✓ Role column exists")
            except Exception:
                print("➜ Adding role column to users table...")
                await session.rollback()  # Rollback any failed transaction
                
        # Add role column in a separate session if needed
        async with async_session() as session:
            try:
                await session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user'"))
                await session.commit()
                print("✓ Role column added")
            except Exception:
                # Column might already exist, that's okay
                await session.rollback()
                pass
        
        # Now work with user data
        async with async_session() as session:
            # Check for existing admin users
            result = await session.execute(text("""
                SELECT id, email, first_name, last_name, is_superuser, role 
                FROM users 
                WHERE email LIKE '%admin%' OR is_superuser = true
                ORDER BY id
            """))
            existing_admins = result.fetchall()
            
            print(f"\n📋 Found {len(existing_admins)} potential admin users:")
            for admin in existing_admins:
                print(f"   ID: {admin[0]}, Email: {admin[1]}, Name: {admin[2]} {admin[3]}, Superuser: {admin[4]}, Role: {admin[5]}")
            
            # Create or update admin user
            admin_email = "admin@example.com"
            admin_password = "admin123"  # Change this in production!
            hashed_password = pwd_context.hash(admin_password)
            
            # Check if admin user exists
            result = await session.execute(text("""
                SELECT id FROM users WHERE email = :email
            """), {"email": admin_email})
            
            existing_admin = result.fetchone()
            
            if existing_admin:
                # Update existing admin user
                print(f"\n🔄 Updating existing admin user (ID: {existing_admin[0]})...")
                await session.execute(text("""
                    UPDATE users 
                    SET 
                        role = 'admin',
                        is_superuser = true,
                        is_staff = true,
                        is_active = true,
                        is_verified = true,
                        password_hash = :password_hash,
                        updated_at = NOW()
                    WHERE email = :email
                """), {
                    "email": admin_email,
                    "password_hash": hashed_password
                })
                
            else:
                # Create new admin user
                print(f"\n➕ Creating new admin user...")
                await session.execute(text("""
                    INSERT INTO users (
                        email, password_hash, first_name, last_name,
                        role, is_active, is_verified, is_staff, is_superuser,
                        created_at, updated_at, auth_method
                    ) VALUES (
                        :email, :password_hash, 'Admin', 'User',
                        'admin', true, true, true, true,
                        NOW(), NOW(), 'password'
                    )
                """), {
                    "email": admin_email,
                    "password_hash": hashed_password
                })
            
            await session.commit()
            
            # Verify the admin user
            result = await session.execute(text("""
                SELECT id, email, first_name, last_name, role, is_superuser, is_active 
                FROM users 
                WHERE email = :email
            """), {"email": admin_email})
            
            admin_user = result.fetchone()
            if admin_user:
                print(f"\n✅ Admin user confirmed:")
                print(f"   ID: {admin_user[0]}")
                print(f"   Email: {admin_user[1]}")
                print(f"   Name: {admin_user[2]} {admin_user[3]}")
                print(f"   Role: {admin_user[4]}")
                print(f"   Is Superuser: {admin_user[5]}")
                print(f"   Is Active: {admin_user[6]}")
                print(f"\n🔑 Login credentials:")
                print(f"   Email: {admin_email}")
                print(f"   Password: {admin_password}")
            else:
                print("❌ Failed to create/update admin user")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("🚀 Fixing admin user setup...")
    asyncio.run(fix_admin_user())
    print("✅ Admin user setup complete!")