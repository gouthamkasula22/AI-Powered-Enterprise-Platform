import asyncio
import sys
import os
from sqlalchemy import text

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend'))

from app.core.database import engine

async def check_tables():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        tables = [row[0] for row in result]
        print(f"Tables created: {tables}")
        
        # Check alembic version
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version;"))
            version = result.scalar()
            print(f"Current migration version: {version}")
        except:
            print("No alembic version table found")

if __name__ == "__main__":
    asyncio.run(check_tables())
