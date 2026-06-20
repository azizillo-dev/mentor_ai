import asyncio
import asyncpg


async def create_db():
    conn = await asyncpg.connect(
        "postgresql://postgres:CEO517984@localhost:5432/postgres"
    )
    db_exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = 'men_mentor_db'"
    )
    if not db_exists:
        await conn.execute("CREATE DATABASE men_mentor_db")
        print("Database men_mentor_db created successfully!")
    else:
        print("Database men_mentor_db already exists.")
    await conn.close()


asyncio.run(create_db())
