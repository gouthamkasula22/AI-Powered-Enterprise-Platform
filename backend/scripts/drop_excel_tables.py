"""
Drop and recreate Excel tables
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.infrastructure.database.database import DatabaseManager, get_db_session

async def drop_and_recreate_excel_tables():
    """Drop all Excel tables with CASCADE and recreate them"""
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    engine = db_manager._engine
    
    # Drop existing tables
    async with engine.begin() as conn:
        await conn.execute(text('DROP TABLE IF EXISTS excel_visualizations CASCADE'))
        await conn.execute(text('DROP TABLE IF EXISTS excel_queries CASCADE'))
        await conn.execute(text('DROP TABLE IF EXISTS excel_sheets CASCADE'))
        await conn.execute(text('DROP TABLE IF EXISTS excel_documents CASCADE'))
    print("Excel tables dropped successfully")
    
    # Tables will be recreated automatically by create_tables() during initialization
    # which was already called above
    print("Tables recreated via Base.metadata.create_all()")

if __name__ == "__main__":
    asyncio.run(drop_and_recreate_excel_tables())
