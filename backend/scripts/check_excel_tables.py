"""Check Excel tables structure"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.infrastructure.database.database import DatabaseManager

async def check_tables():
    dm = DatabaseManager()
    await dm.initialize()
    
    async with dm._engine.connect() as conn:
        # Check excel_documents columns
        result = await conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'excel_documents' ORDER BY ordinal_position"
        ))
        rows = result.fetchall()
        print('Excel Documents table columns:')
        for row in rows:
            print(f'  {row[0]}: {row[1]}')

if __name__ == "__main__":
    asyncio.run(check_tables())
