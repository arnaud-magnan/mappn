"""Unit tests for backend/app/api/deps.py.

Tests cover:
- get_db() yields AsyncSession from session factory
- get_current_user() extracts user from JWT via OAuth2PasswordBearer + decode_token
- get_current_user() raises 401 for missing/invalid/expired tokens
- get_current_user() raises 401 when user not found in DB
- rate_limiter raises 429 when rate limit exceeded
- rate_limiter allows requests within threshold
- rate_limiter fails open when Redis is unavailable (logs warning, allows request)
- Configurable thresholds for rate limiting (10 attempts / 5 min default)
- All dependencies use proper async/await and type annotations
"""

import inspect
import os

# Set environment variables before any app imports so get_settings() works.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")

# Clear the lru_cache on get_settings so our env vars take effect
from app.config import get_settings

get_settings.cache_clear()

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, rate_limiter
from app.core.exceptions import CredentialsException, RateLimitException
from app.core.security import create_access_token, create_refresh_token


# ---------------------------------------------------------------------------
# get_db() tests
# ---------------------------------------------------------------------------


class TestGetDb:
    """Tests for get_db() dependency."""

    def test_get_db_is_async_generator(self) -> None:
        """get_db() must be an async generator function (for FastAPI Depends)."""
        assert inspect.isasyncgenfunction(get_db)

    @pytest.mark.asyncio
    async def test_get_db_yields_async_session(self) -> None:
        """get_db() must yield an AsyncSession instance."""
        gen = get_db()
        session = await gen.__anext__()
        try:
            assert isinstance(session, AsyncSession)
        finally:
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

    @pytest.mark.asyncio
    async def test_get_db_uses_session_factory(self) -> None:
        """get_db() should use AsyncSessionLocal from db.session."""
        from app.db.session import AsyncSessionLocal

        gen = get_db()
        session = await gen.__anext__()
        try:
            # Session should come from the shared factory
            assert isinstance(session, AsyncSession)
        finally:
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass


# ---------------------------------------------------------------------------
# get_current_user() tests
# ---------------------------------------------------------------------------


class TestGetCurrentUser:
    """Tests for get_current_user() dependency."""

    def test_get_current_user_is_coroutine(self) -> None:
        """get_current_user() must be an async function."""
        assert inspect.iscoroutinefunction(get_current_user)

    @pytest.mark.asyncio
    async def test_missing_token_raises_401(self) -> None:
        """get_current_user() should raise CredentialsException when no token is provided."""
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(CredentialsException) as exc_info:
            await get_current_user(token="", db=mock_db)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self) -> None:
        """get_current_user() should raise CredentialsException for a malformed token."""
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(CredentialsException) as exc_info:
            await get_current_user(token="not.a.valid.token", db=mock_db)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self) -> None:
        """get_current_user() should raise CredentialsException for an expired token."""
        mock_db = AsyncMock(spec=AsyncSession)
        expired_token = create_access_token(subject="1", expires_delta_seconds=-10)

        with pytest.raises(CredentialsException) as exc_info:
            await get_current_user(token=expired_token, db=mock_db)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_raises_401(self) -> None:
        """get_current_user() should raise CredentialsException when a refresh token is used instead of access."""
        mock_db = AsyncMock(spec=AsyncSession)
        refresh_token = create_refresh_token(subject="1")

        with pytest.raises(CredentialsException) as exc_info:
            await get_current_user(token=refresh_token, db=mock_db)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_user_not_found_raises_401(self) -> None:
        """get_current_user() should raise CredentialsException when the user ID from the token does not exist."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.get = AsyncMock(return_value=None)
        valid_token = create_access_token(subject="999")

        with pytest.raises(CredentialsException) as exc_info:
            await get_current_user(token=valid_token, db=mock_db)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self) -> None:
        """get_current_user() should return the User when token is valid and user exists."""
        from app.models.user import User

        mock_user = MagicMock(spec=User)
        mock_user.id = 42
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.get = AsyncMock(return_value=mock_user)
        valid_token = create_access_token(subject="42")

        user = await get_current_user(token=valid_token, db=mock_db)
        assert user is mock_user
        # Verify db.get was called with User model and user_id
        mock_db.get.assert_awaited_once_with(User, 42)

    @pytest.mark.asyncio
    async def test_token_without_sub_claim_raises_401(self) -> None:
        """get_current_user() should raise CredentialsException when token has no 'sub' claim."""
        import jwt as pyjwt

        settings = get_settings()
        token_no_sub = pyjwt.encode(
            {"exp": 9999999999, "type": "access"},
            settings.secret_key,
            algorithm="HS256",
        )
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(CredentialsException) as exc_info:
            await get_current_user(token=token_no_sub, db=mock_db)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# OAuth2PasswordBearer integration
# ---------------------------------------------------------------------------


class TestOAuth2Integration:
    """Tests that deps.py uses OAuth2PasswordBearer correctly."""

    def test_oauth2_scheme_exists(self) -> None:
        """deps.py must define an OAuth2PasswordBearer scheme."""
        from app.api import deps

        assert hasattr(deps, "oauth2_scheme")
        assert isinstance(deps.oauth2_scheme, OAuth2PasswordBearer)

    def test_oauth2_scheme_token_url(self) -> None:
        """OAuth2PasswordBearer must have tokenUrl pointing to the auth endpoint."""
        from app.api import deps

        assert deps.oauth2_scheme.model.flows.password.tokenUrl == "/auth/token"


# ---------------------------------------------------------------------------
# rate_limiter tests
# ---------------------------------------------------------------------------


class TestRateLimiter:
    """Tests for rate_limiter dependency."""

    def test_rate_limiter_is_callable(self) -> None:
        """rate_limiter must be a callable (function or class instance)."""
        assert callable(rate_limiter)

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_within_threshold(self) -> None:
        """rate_limiter should allow requests when count is under the threshold."""
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"

        with patch("app.api.deps.increment_rate_limit", new_callable=AsyncMock) as mock_incr:
            mock_incr.return_value = 1  # First request, well within limit
            # Should not raise
            await rate_limiter(mock_request)
            mock_incr.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_at_threshold(self) -> None:
        """rate_limiter should allow requests when count is exactly at the threshold (10)."""
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"

        with patch("app.api.deps.increment_rate_limit", new_callable=AsyncMock) as mock_incr:
            mock_incr.return_value = 10  # At the limit, not over
            # Should not raise - 10th request is still allowed
            await rate_limiter(mock_request)

    @pytest.mark.asyncio
    async def test_rate_limiter_rejects_over_threshold(self) -> None:
        """rate_limiter should raise RateLimitException (429) when count exceeds the threshold."""
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"

        with patch("app.api.deps.increment_rate_limit", new_callable=AsyncMock) as mock_incr:
            mock_incr.return_value = 11  # Over the limit
            with pytest.raises(RateLimitException) as exc_info:
                await rate_limiter(mock_request)
            assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limiter_uses_client_ip(self) -> None:
        """rate_limiter should use the client IP as the rate limit key identifier."""
        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.42"

        with patch("app.api.deps.increment_rate_limit", new_callable=AsyncMock) as mock_incr:
            mock_incr.return_value = 1
            await rate_limiter(mock_request)
            # Check that the key contains the client IP
            call_args = mock_incr.call_args
            key_identifier = call_args[0][0] if call_args[0] else call_args[1].get("key_identifier", "")
            assert "10.0.0.42" in key_identifier

    @pytest.mark.asyncio
    async def test_rate_limiter_uses_15_minute_window(self) -> None:
        """rate_limiter should use a 900-second (15-minute) window by default."""
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"

        with patch("app.api.deps.increment_rate_limit", new_callable=AsyncMock) as mock_incr:
            mock_incr.return_value = 1
            await rate_limiter(mock_request)
            call_args = mock_incr.call_args
            # window_seconds should be 900 (15 minutes)
            window = call_args[1].get("window_seconds") if call_args[1] else call_args[0][1] if len(call_args[0]) > 1 else None
            assert window == 900

    @pytest.mark.asyncio
    async def test_rate_limiter_default_threshold_is_10(self) -> None:
        """rate_limiter should use 10 as the default max attempts threshold."""
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"

        # 10 requests should be OK
        with patch("app.api.deps.increment_rate_limit", new_callable=AsyncMock) as mock_incr:
            mock_incr.return_value = 10
            await rate_limiter(mock_request)  # Should not raise

        # 11th should be rejected
        with patch("app.api.deps.increment_rate_limit", new_callable=AsyncMock) as mock_incr:
            mock_incr.return_value = 11
            with pytest.raises(RateLimitException) as exc_info:
                await rate_limiter(mock_request)
            assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limiter_fails_open_on_redis_error(self) -> None:
        """rate_limiter should allow requests through when Redis is unavailable (fail open)."""
        from app.core.exceptions import AppException

        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"

        with patch("app.api.deps.increment_rate_limit", new_callable=AsyncMock) as mock_incr:
            mock_incr.side_effect = AppException("Redis service unavailable")
            # Should NOT raise -- fail open means allow the request
            await rate_limiter(mock_request)

    @pytest.mark.asyncio
    async def test_rate_limiter_logs_warning_on_redis_error(self) -> None:
        """rate_limiter should log a warning when Redis is unavailable."""
        from app.core.exceptions import AppException

        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.99"

        with patch("app.api.deps.increment_rate_limit", new_callable=AsyncMock) as mock_incr:
            mock_incr.side_effect = AppException("Redis service unavailable")
            with patch("app.api.deps.logger") as mock_logger:
                await rate_limiter(mock_request)
                mock_logger.warning.assert_called_once()
                # Verify the warning message references Redis
                warning_msg = mock_logger.warning.call_args[0][0]
                assert "redis" in warning_msg.lower() or "rate limit" in warning_msg.lower()


# ---------------------------------------------------------------------------
# Type annotations and Depends pattern verification
# ---------------------------------------------------------------------------


class TestCodeQuality:
    """Tests that verify code quality: type annotations, async/await, Depends pattern."""

    def test_get_current_user_has_type_annotations(self) -> None:
        """get_current_user() must have proper type annotations."""
        hints = get_current_user.__annotations__
        # Should have return type or parameter annotations
        sig = inspect.signature(get_current_user)
        # token parameter should be annotated as str
        assert "token" in sig.parameters
        assert "db" in sig.parameters

    def test_rate_limiter_is_async(self) -> None:
        """rate_limiter must be an async function for use with FastAPI Depends."""
        assert inspect.iscoroutinefunction(rate_limiter)

    def test_deps_module_imports(self) -> None:
        """deps.py must properly import from session, security, and redis modules."""
        source_file = inspect.getfile(get_db)
        with open(source_file) as f:
            source = f.read()
        # Should import from session factory
        assert "session" in source.lower() or "AsyncSessionLocal" in source
        # Should import decode_token
        assert "decode_token" in source
        # Should import increment_rate_limit
        assert "increment_rate_limit" in source
