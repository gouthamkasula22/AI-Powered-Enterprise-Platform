#!/usr/bin/env python3
"""
Quick Setup Script for Database and Redis

This script helps you quickly set up and test your database and Redis connections.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def test_database_connection():
    """Test database connectivity"""
    print("🔍 Testing Database Connection...")
    
    try:
        from src.infrastructure.database.database import initialize_database, check_database_health
        
        # Initialize database
        await initialize_database()
        print("✅ Database initialized successfully")
        
        # Check health
        health = await check_database_health()
        if health["status"] == "healthy":
            print("✅ Database health check passed")
            return True
        else:
            print(f"❌ Database health check failed: {health['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_redis_connection():
    """Test Redis connectivity"""
    print("\n🔍 Testing Redis Connection...")
    
    try:
        from src.infrastructure.cache import initialize_cache, get_cache_manager
        
        # Initialize Redis
        await initialize_cache()
        print("✅ Redis initialized successfully")
        
        # Test basic operations
        cache_manager = get_cache_manager()
        health = await cache_manager.health_check()
        
        if health["status"] == "healthy":
            print("✅ Redis health check passed")
            return True
        else:
            print(f"❌ Redis health check failed: {health['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


async def setup_database_schema():
    """Initialize database schema"""
    print("\n🔍 Setting up Database Schema...")
    
    try:
        from src.infrastructure.database.database import get_database_manager
        
        db_manager = get_database_manager()
        await db_manager.initialize()
        print("✅ Database schema created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database schema setup failed: {e}")
        return False


def check_environment():
    """Check if environment variables are set"""
    print("🔍 Checking Environment Configuration...")
    
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL", 
        "JWT_SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("📝 Please create a .env file based on .env.example")
        return False
    else:
        print("✅ Environment configuration looks good")
        return True


async def main():
    """Main setup function"""
    print("🚀 User Authentication System - Quick Setup")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    if not env_ok:
        print("\n💡 Setup Instructions:")
        print("1. Copy .env.example to .env")
        print("2. Update the values in .env with your configuration")
        print("3. Start PostgreSQL and Redis services")
        print("4. Run this script again")
        return False
    
    # Test connections
    db_ok = await test_database_connection()
    redis_ok = await test_redis_connection()
    
    if db_ok and redis_ok:
        # Setup schema
        schema_ok = await setup_database_schema()
        
        if schema_ok:
            print("\n🎉 Setup completed successfully!")
            print("\n🚀 You can now start the application:")
            print("   python scripts/run_dev_server.py")
            print("\n📖 API Documentation will be available at:")
            print("   http://localhost:8000/docs")
            return True
    
    print("\n❌ Setup failed. Please check the errors above.")
    print("\n🔧 Troubleshooting:")
    if not db_ok:
        print("   - Check if PostgreSQL is running")
        print("   - Verify DATABASE_URL in .env file")
        print("   - Ensure database exists and user has permissions")
    if not redis_ok:
        print("   - Check if Redis is running")
        print("   - Verify REDIS_URL in .env file")
    
    return False


if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("📦 Installing python-dotenv...")
        os.system("pip install python-dotenv")
        from dotenv import load_dotenv
        load_dotenv()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)