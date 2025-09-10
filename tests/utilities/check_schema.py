from app.core.database import engine
from sqlalchemy import text
import asyncio

async def check_schema():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position"))
        print('Database columns:')
        for row in result:
            print(f'  {row[0]}: {row[1]}')

asyncio.run(check_schema())
