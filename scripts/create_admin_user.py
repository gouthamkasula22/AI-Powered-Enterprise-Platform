#!/usr/bin/env python3

"""
Promote any existing user to admin role with proper verification
"""

import asyncio
import asyncpg
import argparse
import sys

async def promote_to_admin(email: str):
    """Promote an existing user to admin role"""
    # Fixed database connection with correct credentials and port
    DATABASE_URL = "postgresql://auth_user:auth_password@localhost:5433/auth_db"
    
    try:
        # Connect to database using asyncpg (simpler approach)
        conn = await asyncpg.connect(DATABASE_URL)
        
        # First check if user exists
        user = await conn.fetchrow(
            "SELECT id, first_name, last_name, role, is_verified FROM users WHERE email = $1",
            email
        )
        
        if not user:
            print(f"❌ User with email '{email}' not found!")
            print("Please register the user first using the registration API:")
            print(f"POST /api/v1/auth/register with email: {email}")
            await conn.close()
            return False
        
        print(f"📋 Found user: {user['first_name']} {user['last_name']} (Current role: {user['role']})")
        
        # Check if already admin
        if user['role'] == 'ADMIN':
            print(f"ℹ️  User '{email}' is already an ADMIN!")
            await conn.close()
            return True
        
        # Promote user to admin
        result = await conn.execute("""
            UPDATE users 
            SET role = 'ADMIN', 
                is_verified = true, 
                is_active = true, 
                email_verification_token = NULL, 
                email_verification_expires_at = NULL,
                updated_at = NOW()
            WHERE email = $1
        """, email)
        
        await conn.close()
        
        if result == "UPDATE 1":
            print(f"✅ Successfully promoted '{email}' to ADMIN!")
            print(f"   - Role: {user['role']} → ADMIN")
            print(f"   - Verified: ✓")
            print(f"   - Active: ✓")
            print(f"   - Email verification cleared")
            return True
        else:
            print(f"❌ Failed to promote user '{email}'")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Promote user to admin role')
    parser.add_argument('email', nargs='?', 
                       help='Email of user to promote to admin')
    
    args = parser.parse_args()
    
    if not args.email:
        email = input("Enter email of user to promote to admin: ").strip()
        if not email:
            print("❌ Email is required!")
            sys.exit(1)
    else:
        email = args.email
    
    print(f"🔄 Promoting user '{email}' to admin...")
    success = asyncio.run(promote_to_admin(email))
    
    if success:
        print(f"\n🎉 User can now access admin endpoints!")
        print(f"Test with: POST /api/v1/auth/login with email: {email}")
        print(f"Then use the JWT token to access: GET /api/v1/admin/dashboard")
    else:
        sys.exit(1)