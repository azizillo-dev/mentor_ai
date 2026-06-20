"""
SQLAlchemy declarative base.
Keeps Base class separate from model imports to avoid circular imports.
Model imports for Alembic are done in alembic/env.py directly.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass
