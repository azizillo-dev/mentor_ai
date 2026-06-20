"""
Database initialization utilities.
Used for creating tables in development/testing (not for production - use Alembic).
"""

import logging

from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)


async def create_all_tables() -> None:
    """
    Create all tables defined in SQLAlchemy models.

    WARNING: Use only in development/testing.
    In production, always use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("All database tables created successfully.")


async def drop_all_tables() -> None:
    """
    Drop all tables. USE WITH EXTREME CAUTION.

    Only for testing environments.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("All database tables dropped.")
