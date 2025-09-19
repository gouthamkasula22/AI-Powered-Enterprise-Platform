import sys
import os
import asyncio
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


async def list_admin_users():
    """List all admin users in the database"""
    try:
        # Direct connection to database
        db_url = "postgresql+asyncpg://auth_user:auth_password@localhost:5433/auth_db"
        engine = create_async_engine(db_url, echo=False)
        async_session_factory = async_sessionmaker(
            bind=engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        async with async_session_factory() as session:
            # Use Raw SQL query
            sql = text("""
                SELECT 
                    id, 
                    email, 
                    role, 
                    is_active, 
                    is_verified, 
                    is_staff, 
                    is_superuser,
                    created_at,
                    last_login
                FROM users 
                WHERE role IN ('ADMIN', 'admin', 'SUPERADMIN', 'superadmin')
                ORDER BY email
            """)
            result = await session.execute(sql)
            raw_users = result.fetchall()
            
            if not raw_users:
                print("❌ No admin users found!")
                return
                
            print(f"📋 Found {len(raw_users)} admin users:")
            for row in raw_users:
                print(f"ID: {row.id}")
                print(f"Email: {row.email}")
                print(f"Role: {row.role}")
                print(f"Active: {row.is_active}")
                print(f"Verified: {row.is_verified}")
                print(f"Staff: {row.is_staff}")
                print(f"Superuser: {row.is_superuser}")
                print(f"Created: {row.created_at}")
                print(f"Last Login: {row.last_login or 'Never'}")
                print("-" * 40)
                
            # Also query permissions table if any
            try:
                # Check if we have a user_permissions table
                sql = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'user_permissions'
                """)
                result = await session.execute(sql)
                has_permissions_table = result.fetchone() is not None
                
                if has_permissions_table:
                    sql = text("""
                        SELECT * FROM user_permissions
                        WHERE user_id IN (
                            SELECT id FROM users 
                            WHERE role IN ('ADMIN', 'admin', 'SUPERADMIN', 'superadmin')
                        )
                    """)
                    result = await session.execute(sql)
                    permissions = result.fetchall()
                    
                    if permissions:
                        print("\n📋 User Permissions:")
                        for perm in permissions:
                            print(f"User ID: {perm.user_id}")
                            print(f"Permission: {perm.permission}")
                            print("-" * 40)
            except Exception as e:
                print(f"❌ Permissions query error: {e}")
                
            # Also check JWT token blacklist table
            try:
                sql = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'token_blacklist'
                """)
                result = await session.execute(sql)
                has_blacklist_table = result.fetchone() is not None
                
                if has_blacklist_table:
                    sql = text("""
                        SELECT COUNT(*) as count FROM token_blacklist
                    """)
                    result = await session.execute(sql)
                    count = result.fetchone()
                    print(f"\n🔐 Blacklisted tokens: {count.count if count else 0}")
            except Exception as e:
                print(f"❌ Blacklist query error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_admin_users())
