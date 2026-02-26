"""Shared test fixtures for the Mappn backend test suite.

Provides:
- Session-scoped PostGIS testcontainers fixture for test DB isolation
- Function-scoped async session with rollback after each test
- FastAPI test client (httpx AsyncClient) bound to a lightweight test app
- Authenticated user fixture that creates a test user and returns JWT headers
- Redis fixture using fakeredis for visit tracking and rate limiting tests

Fixtures use pytest-asyncio 0.25 patterns with ``asyncio_mode = auto`` and
``asyncio_default_fixture_loop_scope = session`` in pytest.ini.

IMPORTANT: All test modules using database fixtures (db_session, test_user,
client, etc.) MUST set the module-level marker::

    pytestmark = pytest.mark.asyncio(loop_scope="session")

This ensures tests run on the same event loop as the session-scoped
async engine fixture. Without this, asyncpg connections created in the
session loop will raise ``RuntimeError: Future attached to a different
loop`` when accessed from a function-scoped test loop.

The PostGIS container is created once per session; each test gets its own
transaction that rolls back on teardown for complete isolation.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

# ---------------------------------------------------------------------------
# Environment setup -- must happen before any app imports
# ---------------------------------------------------------------------------

# Set required env vars for app.config.Settings before importing app modules.
# These defaults will be overridden by the actual testcontainer URL once it
# starts, but they prevent pydantic-settings from raising on import.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-integration-tests")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

# Clear the lru_cache so our env vars take effect
from app.config import get_settings

get_settings.cache_clear()

# Now safe to import app modules
import fakeredis

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.models import Area, JournalNote, Place, User, Visit  # noqa: F401 -- ensure models registered


# ---------------------------------------------------------------------------
# PostGIS testcontainers fixture (session scope)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgis_container():
    """Start a PostGIS container for the entire test session.

    Uses the postgis/postgis Docker image for PostGIS support.
    The container is started once and shared across all tests.
    """
    # Use 16-3.4 because 16-3.5 lacks an ARM64 manifest (Apple Silicon).
    # Both provide PostGIS 3.x on PostgreSQL 16 which is functionally equivalent.
    with PostgresContainer(
        image="postgis/postgis:16-3.4",
        username="test",
        password="test",
        dbname="test_mappn",
        driver="asyncpg",
    ) as container:
        yield container


@pytest_asyncio.fixture(scope="session")
async def async_engine(postgis_container: PostgresContainer) -> AsyncGenerator[AsyncEngine, None]:
    """Create an async SQLAlchemy engine connected to the PostGIS test container.

    Creates all tables from the ORM metadata (equivalent to running migrations).
    The engine is shared across the entire test session.
    """
    # Build the asyncpg connection URL from the container
    connection_url = postgis_container.get_connection_url()

    engine = create_async_engine(
        connection_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,
    )

    # Create PostGIS extension and all ORM tables
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup: drop all tables and dispose of the engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# Function-scoped async session with rollback
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a function-scoped async session that rolls back after each test.

    Each test runs inside a connection-level transaction. After the test
    completes, the transaction is rolled back, ensuring complete isolation
    between tests without recreating tables.
    """
    # Start a connection-level transaction
    async with async_engine.connect() as connection:
        # Begin a transaction on the connection
        transaction = await connection.begin()

        # Create a session bound to this connection
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        yield session

        # Close the session and roll back the transaction
        await session.close()
        await transaction.rollback()


# ---------------------------------------------------------------------------
# Redis fixture (fakeredis)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def redis_client() -> AsyncGenerator[Any, None]:
    """Provide a clean fakeredis async client for each test.

    Uses fakeredis to avoid needing a real Redis container for tests.
    A new FakeServer is created per test, ensuring no state leaks.
    """
    server = fakeredis.FakeServer()
    client = fakeredis.FakeAsyncRedis(server=server, decode_responses=True)

    # Patch the app's Redis module to use this fake client
    import app.core.redis as redis_module

    original_client = redis_module._redis_client
    original_get = redis_module.get_redis_client
    redis_module._redis_client = client

    async def _fake_get_redis_client():
        return client

    redis_module.get_redis_client = _fake_get_redis_client

    yield client

    # Restore originals
    redis_module._redis_client = original_client
    redis_module.get_redis_client = original_get

    await client.flushall()
    await client.aclose()


# ---------------------------------------------------------------------------
# FastAPI test app and client fixture
# ---------------------------------------------------------------------------


def _create_test_app():
    """Create a minimal FastAPI app for testing.

    Since main.py does not exist yet (Step 10), this creates a lightweight
    app that registers the exception handlers and provides a health endpoint.
    Routers are registered as they are implemented in subsequent steps.
    """
    from fastapi import FastAPI

    from app.core.exceptions import register_exception_handlers

    app = FastAPI(title="Mappn Test App")
    register_exception_handlers(app)

    # Register implemented routers
    from app.api.auth import router as auth_router
    from app.api.places import router as places_router
    from app.api.utility import router as utility_router
    from app.api.visits import router as visits_router

    app.include_router(auth_router)
    app.include_router(places_router)
    app.include_router(visits_router)
    app.include_router(utility_router)

    # Health check endpoint for smoke testing
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


@pytest_asyncio.fixture(scope="function")
async def test_app(db_session: AsyncSession) -> Any:
    """Create a test FastAPI app with dependency overrides.

    Overrides ``get_db`` from deps.py to return the test session
    so all endpoints use the rollback-protected session.
    """
    from app.api.deps import get_db

    app = _create_test_app()

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    yield app

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(test_app: Any) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient bound to the test FastAPI app.

    Uses ASGITransport to send requests directly to the app without
    starting a real HTTP server.
    """
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Authenticated user fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database and return the ORM instance.

    The user has known credentials:
    - email: test@example.com
    - username: testuser
    - password: testpassword123 (hashed with bcrypt)
    """
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
    )
    db_session.add(user)
    await db_session.flush()  # Assigns the user ID without committing
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: User) -> dict[str, str]:
    """Provide valid JWT Authorization headers for the test user.

    Returns a dict suitable for passing as ``headers`` to httpx requests:
    ``{"Authorization": "Bearer <token>"}``
    """
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(
    test_app: Any, test_user: User
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient with pre-set auth headers.

    Convenience fixture that combines the test client and auth headers
    so tests don't need to pass headers manually on every request.
    """
    token = create_access_token(subject=str(test_user.id))
    transport = ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
