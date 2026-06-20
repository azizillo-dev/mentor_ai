"""
Async SQLAlchemy engine and session factory.
Uses asyncpg driver for high-performance async PostgreSQL connections.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# ─── Async Engine ─────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,           # SQL queries are logged in debug mode
    pool_size=10,                  # Connection pool size
    max_overflow=20,               # Extra connections beyond pool_size
    pool_pre_ping=True,            # Verify connections before checkout
    pool_recycle=3600,             # Recycle connections after 1 hour
)

# ─── Session Factory ──────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # Prevent lazy-load errors after commit
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides an async database session.

    Yields:
        AsyncSession: Database session that is automatically closed.

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
