"""Shared ORM models package.

Re-exports all shared models and the Base class for Alembic autodiscovery.
All models must be imported here so that Alembic can detect them when
generating or running migrations.
"""

from app.db.base import Base
from app.models.area import Area
from app.models.journal import JournalNote
from app.models.place import Place
from app.models.user import User
from app.models.visit import Visit

__all__ = [
    "Base",
    "User",
    "Place",
    "Area",
    "Visit",
    "JournalNote",
]
