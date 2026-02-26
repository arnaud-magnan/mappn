"""Async database engine, session factory, and FastAPI dependency.

Creates an async SQLAlchemy engine with connection pooling configured for
production use (pool_size=20, max_overflow=80). Provides an async session
factory and a FastAPI-compatible get_db() dependency that yields sessions.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=80,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically closed when the request completes.
    """
    async with AsyncSessionLocal() as session:
        yield session
