"""
Alembic environment configuration.
Uses async SQLAlchemy engine for async PostgreSQL support.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ─── Alembic Config ───────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─── Import app settings and models ───────────────────────────────────────────
# Models must be imported here for Alembic autogenerate to detect them.
from app.core.config import settings
from app.db.base import Base
from app.models import user as _user_models  # noqa: F401 - triggers model registration
from app.models import group as _group_models  # noqa: F401
from app.models import group_member as _group_member_models  # noqa: F401
from app.models import homework as _homework_models  # noqa: F401
from app.models import submission as _submission_models  # noqa: F401
from app.models import ai_result as _ai_result_models  # noqa: F401

# Override sqlalchemy.url from environment variable (never hardcode credentials)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


# ─── Offline Mode ─────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (generates SQL without DB connection).
    Useful for reviewing migration SQL before applying it.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ─── Online Mode (Async) ──────────────────────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# ─── Entry Point ──────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
