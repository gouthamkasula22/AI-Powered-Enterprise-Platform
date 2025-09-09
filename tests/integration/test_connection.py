"""
Test script to verify PostgreSQL connection with asyncpg.
This helps debug the Alembic connection issue.
"""

import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def test_asyncpg_direct():
    """Test direct asyncpg connection."""
    try:
        print("Testing direct asyncpg connection...")
        conn = await asyncpg.connect(
            host='localhost',
            port=5433,
            user='auth_user',
            password='auth_password',
            database='auth_db'
        )
        
        # Test query
        result = await conn.fetchval('SELECT current_database()')
        print(f"✅ Direct asyncpg connection successful: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Direct asyncpg connection failed: {e}")
        return False


async def test_sqlalchemy_async():
    """Test SQLAlchemy async engine connection."""
    try:
        print("Testing SQLAlchemy async engine...")
        engine = create_async_engine(
            "postgresql+asyncpg://auth_user:auth_password@localhost:5433/auth_db",
            echo=True
        )
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"✅ SQLAlchemy async connection successful: {db_name}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy async connection failed: {e}")
        return False


async def main():
    """Run all connection tests."""
    print("=" * 50)
    print("PostgreSQL Connection Tests")
    print("=" * 50)
    
    # Test 1: Direct asyncpg
    direct_success = await test_asyncpg_direct()
    
    print("-" * 50)
    
    # Test 2: SQLAlchemy async
    sqlalchemy_success = await test_sqlalchemy_async()
    
    print("=" * 50)
    print("Summary:")
    print(f"Direct asyncpg: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"SQLAlchemy async: {'✅ PASS' if sqlalchemy_success else '❌ FAIL'}")
    
    if direct_success and sqlalchemy_success:
        print("🎉 All tests passed! Alembic should work.")
    else:
        print("🚨 Some tests failed. Need to investigate further.")


if __name__ == "__main__":
    asyncio.run(main())
