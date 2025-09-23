import asyncio
import asyncpg

async def add_column():
    # Connect to the database with correct credentials
    conn = await asyncpg.connect('postgresql://auth_user:auth_password@localhost:5433/auth_db')
    
    try:
        # Add the last_logout column if it doesn't exist
        await conn.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_logout TIMESTAMP WITH TIME ZONE')
        print('Column added successfully!')
    except Exception as e:
        print(f'Error adding column: {e}')
    finally:
        # Close the connection
        await conn.close()

# Run the async function
asyncio.run(add_column())