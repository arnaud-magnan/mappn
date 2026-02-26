"""SQLAlchemy 2.0 DeclarativeBase for ORM models.

All ORM models in the project inherit from Base defined here.
This module is imported by Alembic for migration autodiscovery.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    Uses SQLAlchemy 2.0 DeclarativeBase pattern.
    All models should inherit from this class.
    """

    pass
