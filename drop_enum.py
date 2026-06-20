import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from sqlalchemy import text

async def drop():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("DROP TYPE IF EXISTS submission_status CASCADE;"))
    print("Enum dropped")

if __name__ == "__main__":
    asyncio.run(drop())
