"""Smoke tests verifying the test infrastructure fixture chain works.

These tests validate that:
- PostGIS testcontainer starts and is accessible
- Async session fixture creates tables and supports rollback
- FastAPI test client fixture serves requests
- Authenticated user fixture creates a user with valid JWT headers
- Redis fixture provides a clean fakeredis instance
- The complete fixture chain integrates correctly end-to-end
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

# All tests must share the session-scoped event loop to work with the
# session-scoped async engine fixture (pytest-asyncio 0.25 pattern).
pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# PostGIS container and engine fixtures
# ---------------------------------------------------------------------------


async def test_postgis_container_is_running(async_engine):
    """The PostGIS test container should be running and accepting connections."""
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


async def test_postgis_extension_is_enabled(async_engine):
    """The PostGIS extension should be installed in the test database."""
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'postgis'")
        )
        assert result.scalar() == "postgis"


async def test_tables_are_created(async_engine):
    """All ORM model tables should exist in the test database."""
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        )
        tables = sorted(row[0] for row in result.fetchall())

    for table in ["areas", "places", "users", "visits"]:
        assert table in tables, f"Table '{table}' not found. Found: {tables}"


# ---------------------------------------------------------------------------
# Async session with rollback
# ---------------------------------------------------------------------------


async def test_session_is_usable(db_session: AsyncSession):
    """The db_session fixture should yield a working async session."""
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


async def test_session_rollback_isolation(db_session: AsyncSession):
    """Data inserted in one test should not be visible in subsequent tests.

    This test inserts a user. Because each test rolls back, the user
    should not persist. The next test (test_session_rollback_verification)
    checks that the user does not exist.
    """
    user = User(
        username="rollback_test_user",
        email="rollback@example.com",
        password_hash="fakehash",
    )
    db_session.add(user)
    await db_session.flush()
    assert user.id is not None


async def test_session_rollback_verification(db_session: AsyncSession):
    """Verify the user from the previous test was rolled back.

    This depends on test_session_rollback_isolation running first (pytest
    runs tests in file order by default). The user inserted there should
    not exist in this test's session.
    """
    result = await db_session.execute(
        text("SELECT count(*) FROM users WHERE username = 'rollback_test_user'")
    )
    assert result.scalar() == 0


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


async def test_client_health_check(client: AsyncClient):
    """The test client should be able to reach the health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Authenticated user fixture
# ---------------------------------------------------------------------------


async def test_user_is_created(test_user: User):
    """The test_user fixture should create a user with expected attributes."""
    assert test_user.id is not None
    assert test_user.username == "testuser"
    assert test_user.email == "test@example.com"
    assert test_user.password_hash.startswith("$2b$")


async def test_auth_headers_contain_bearer_token(auth_headers: dict):
    """The auth_headers fixture should return a valid Bearer token header."""
    assert "Authorization" in auth_headers
    assert auth_headers["Authorization"].startswith("Bearer ")
    token = auth_headers["Authorization"].split(" ")[1]
    assert len(token) > 0


async def test_auth_headers_token_is_valid(auth_headers: dict, test_user: User):
    """The JWT in auth_headers should decode to the test user's ID."""
    from app.core.security import decode_token

    token = auth_headers["Authorization"].split(" ")[1]
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == str(test_user.id)


async def test_authenticated_client_has_headers(authenticated_client: AsyncClient):
    """The authenticated_client fixture should include auth headers."""
    response = await authenticated_client.get("/health")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Redis fixture
# ---------------------------------------------------------------------------


async def test_redis_client_is_usable(redis_client):
    """The redis_client fixture should support basic set/get operations."""
    await redis_client.set("test_key", "test_value")
    value = await redis_client.get("test_key")
    assert value == "test_value"


async def test_redis_client_is_clean_per_test(redis_client):
    """Each test should get a clean Redis instance (no leftover keys)."""
    # If the previous test's data leaked, this would find "test_key"
    value = await redis_client.get("test_key")
    assert value is None


async def test_redis_patch_works_with_app_code(redis_client):
    """The app's Redis module should use the fakeredis client."""
    from app.core.redis import get_redis_client

    client = await get_redis_client()
    # The patched client should be our fakeredis instance
    assert client is redis_client


# ---------------------------------------------------------------------------
# End-to-end fixture chain
# ---------------------------------------------------------------------------


async def test_full_fixture_chain(
    db_session: AsyncSession,
    client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    redis_client,
):
    """Verify the complete fixture chain works together.

    This test exercises all fixtures simultaneously:
    - db_session for database operations
    - client for HTTP requests
    - test_user for user data
    - auth_headers for authentication
    - redis_client for cache/rate-limit operations
    """
    # DB session works
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

    # Client works
    response = await client.get("/health")
    assert response.status_code == 200

    # User is in the database
    assert test_user.id is not None

    # Auth headers are valid
    assert "Authorization" in auth_headers

    # Redis works
    await redis_client.set("chain_test", "ok")
    assert await redis_client.get("chain_test") == "ok"
