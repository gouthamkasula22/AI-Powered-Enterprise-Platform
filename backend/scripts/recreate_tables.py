#!/usr/bin/env python3
"""
Recreate Database Tables

Drops and recreates all database tables to ensure they match the current model schema.
"""

import asyncio
from src.infrastructure.database.database import get_database_manager

async def recreate_tables():
    """Drop and recreate all database tables"""
    mgr = get_database_manager()
    
    print("� Initializing database...")
    await mgr.initialize()
    
    print("�🗑️  Dropping existing tables...")
    await mgr.drop_tables()
    
    print("🔨 Creating new tables...")
    await mgr.create_tables()
    
    print("✅ Tables recreated successfully!")
    
    await mgr.close()

if __name__ == "__main__":
    asyncio.run(recreate_tables())