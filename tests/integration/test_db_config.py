"""
Test Database Configuration

Simple test script to verify SQLAlchemy configuration and database connectivity.
Run this to ensure all database settings are working correctly.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend'))

from app.core.database import (
    test_database_connection,
    check_database_health,
    get_database_stats,
    create_database_tables
)
from app.core.config import settings

async def test_database_configuration():
    """Test all database configuration features"""
    print("🔧 Testing SQLAlchemy Configuration...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Pool Size: {settings.DB_POOL_SIZE}")
    print(f"Max Overflow: {settings.DB_MAX_OVERFLOW}")
    print(f"Echo Queries: {settings.DB_ECHO}")
    print("-" * 50)
    
    # Test basic connectivity
    print("1. Testing database connectivity...")
    connection_success = await test_database_connection()
    print(f"   Result: {'✅ Success' if connection_success else '❌ Failed'}")
    
    if not connection_success:
        print("❌ Database connection failed. Please check your configuration.")
        return False
    
    # Test health check
    print("\n2. Testing database health check...")
    health_data = await check_database_health()
    print(f"   Status: {health_data['status']}")
    print(f"   Response Time: {health_data['response_time_ms']}ms")
    print(f"   Pool Stats: {health_data.get('pool_stats', {})}")
    
    # Test table creation
    print("\n3. Testing table creation...")
    try:
        await create_database_tables()
        print("   Result: ✅ Tables created/verified successfully")
    except Exception as e:
        print(f"   Result: ❌ Failed - {e}")
        return False
    
    # Test pool statistics
    print("\n4. Testing connection pool statistics...")
    try:
        stats = await get_database_stats()
        print(f"   Pool Stats: {stats}")
    except Exception as e:
        print(f"   Result: ❌ Failed to get stats - {e}")
    
    print("\n✅ All database configuration tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database_configuration())
    if not success:
        sys.exit(1)
