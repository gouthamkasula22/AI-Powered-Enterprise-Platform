"""
Quick script to promote a user to SUPERADMIN role
"""
import sys
import os
import asyncio

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


async def promote_to_superadmin(email: str):
    """Promote a user to SUPERADMIN role"""
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
            # Update user role
            sql = text("""
                UPDATE users 
                SET role = 'SUPERADMIN',
                    is_superuser = true,
                    is_staff = true
                WHERE email = :email
                RETURNING id, email, role
            """)
            result = await session.execute(sql, {"email": email})
            user = result.fetchone()
            
            if not user:
                print(f"❌ User with email '{email}' not found!")
                return
            
            await session.commit()
            
            print(f"✅ Successfully promoted user to SUPERADMIN:")
            print(f"   ID: {user[0]}")
            print(f"   Email: {user[1]}")
            print(f"   Role: {user[2]}")
            print(f"\n⚠️  Please logout and login again for changes to take effect!")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_to_superadmin.py <email>")
        print("\nExample:")
        print("  python promote_to_superadmin.py user@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(promote_to_superadmin(email))
