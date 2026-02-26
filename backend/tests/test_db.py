"""Tests for database layer (db/base.py and db/session.py).

Validates:
- DeclarativeBase subclass exists and is usable by ORM models
- Async engine is created with correct postgresql+asyncpg:// URL
- Engine pool_size=20, max_overflow=80
- async_sessionmaker configured with expire_on_commit=False
- get_db() yields an AsyncSession and properly closes it

Environment variables are set via monkeypatch at the module level
so that importing session.py (which calls get_settings()) succeeds.
"""

import inspect
import os

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Set environment variables before any app imports so get_settings() works.
# These are test-only values; no real database connection is made for unit tests.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")

# Clear the lru_cache on get_settings so our env vars take effect
from app.config import get_settings
get_settings.cache_clear()


class TestDeclarativeBase:
    """Tests for db/base.py DeclarativeBase."""

    def test_base_is_declarative_base_subclass(self):
        """Base must be a subclass of SQLAlchemy 2.0 DeclarativeBase."""
        from app.db.base import Base

        assert issubclass(Base, DeclarativeBase)

    def test_base_can_define_orm_model(self):
        """Base must be usable to define ORM models with mapped_column."""
        from app.db.base import Base

        # Define a test model using the Base -- this verifies it's a real
        # DeclarativeBase that can host table definitions.
        class _TestModel(Base):
            __tablename__ = "_test_db_layer_model"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column()

        assert hasattr(_TestModel, "__table__")
        assert _TestModel.__tablename__ == "_test_db_layer_model"

    def test_base_has_metadata(self):
        """Base must expose metadata for Alembic migrations."""
        from app.db.base import Base

        assert hasattr(Base, "metadata")
        assert Base.metadata is not None


class TestAsyncEngine:
    """Tests for db/session.py engine creation."""

    def test_engine_is_async_engine(self):
        """engine must be an AsyncEngine instance."""
        from app.db.session import engine

        assert isinstance(engine, AsyncEngine)

    def test_engine_uses_asyncpg_driver(self):
        """Engine URL must use postgresql+asyncpg:// scheme."""
        from app.db.session import engine

        url_str = str(engine.url)
        assert url_str.startswith("postgresql+asyncpg://")

    def test_engine_pool_size_is_20(self):
        """Engine pool_size must be 20."""
        from app.db.session import engine

        pool = engine.pool
        assert pool.size() == 20

    def test_engine_max_overflow_is_80(self):
        """Engine max_overflow must be 80."""
        from app.db.session import engine

        pool = engine.pool
        assert pool._max_overflow == 80


class TestAsyncSessionmaker:
    """Tests for db/session.py async_sessionmaker."""

    def test_async_session_local_is_sessionmaker(self):
        """AsyncSessionLocal must be an async_sessionmaker instance."""
        from app.db.session import AsyncSessionLocal

        assert isinstance(AsyncSessionLocal, async_sessionmaker)

    def test_expire_on_commit_is_false(self):
        """Session factory must have expire_on_commit=False."""
        from app.db.session import AsyncSessionLocal

        assert AsyncSessionLocal.kw.get("expire_on_commit") is False


class TestGetDb:
    """Tests for db/session.py get_db() async generator."""

    @pytest.mark.asyncio
    async def test_get_db_yields_async_session(self):
        """get_db() must yield an AsyncSession instance."""
        from app.db.session import get_db

        gen = get_db()
        session = await gen.__anext__()
        try:
            assert isinstance(session, AsyncSession)
        finally:
            # Exhaust the generator to trigger cleanup
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

    @pytest.mark.asyncio
    async def test_get_db_properly_handles_session_lifecycle(self):
        """get_db() must yield exactly one session and then stop (proper cleanup)."""
        from app.db.session import get_db

        gen = get_db()
        session = await gen.__anext__()

        # Session should be usable (active) while yielded
        assert session.is_active
        assert isinstance(session, AsyncSession)

        # Generator must stop after yielding once (context manager __aexit__
        # calls session.close(), then the generator finishes).
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

    @pytest.mark.asyncio
    async def test_get_db_uses_async_context_manager_pattern(self):
        """get_db() implementation uses 'async with' for session lifecycle management."""
        import textwrap
        from app.db import session as session_module

        source = inspect.getsource(session_module.get_db)
        # Verify the implementation uses the async context manager pattern
        # which ensures session.close() is called on exit
        assert "async with" in source, (
            "get_db() must use 'async with AsyncSessionLocal()' to ensure "
            "the session is properly closed when the dependency exits"
        )

    def test_get_db_is_async_generator_function(self):
        """get_db() must be an async generator function (for FastAPI Depends)."""
        from app.db.session import get_db

        assert inspect.isasyncgenfunction(get_db)
