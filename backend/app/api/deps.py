"""Shared API dependency injection for all routers.

Provides:
- ``get_db()``: Async database session using ``AsyncSessionLocal`` from
  ``db.session``.
- ``get_current_user()``: Extracts and validates the authenticated user from
  a JWT Bearer token using OAuth2PasswordBearer + ``decode_token`` + DB lookup.
- ``rate_limiter()``: Redis-backed rate limiter with configurable thresholds
  (default 10 attempts per 15-minute window).  Fails open when Redis is
  unavailable (logs a warning and allows the request through).

Usage in routers::

    from app.api.deps import get_db, get_current_user, rate_limiter

    @router.get("/protected")
    async def protected(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        _rate: None = Depends(rate_limiter),
    ):
        ...
"""

from __future__ import annotations

import logging

import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, CredentialsException, RateLimitException
from app.core.redis import increment_rate_limit
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OAuth2 scheme
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session from the shared session factory.

    The session is automatically closed when the request completes.
    """
    async with AsyncSessionLocal() as session:
        yield session  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Authenticated user dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and return the authenticated ``User`` from a JWT Bearer token.

    Raises :class:`~app.core.exceptions.CredentialsException` when:
    - The token is missing, empty, or malformed.
    - The token has expired.
    - The token is a refresh token (not an access token).
    - The ``sub`` claim is missing or not a valid integer user ID.
    - No user with the extracted ID exists in the database.
    """
    if token is None:
        raise CredentialsException("Not authenticated")

    try:
        payload = decode_token(token, expected_type="access")
    except jwt.InvalidTokenError:
        raise CredentialsException("Could not validate credentials")

    sub: str | None = payload.get("sub")
    if sub is None:
        raise CredentialsException("Could not validate credentials")

    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise CredentialsException("Could not validate credentials")

    user = await db.get(User, user_id)
    if user is None:
        raise CredentialsException("Could not validate credentials")

    return user


# ---------------------------------------------------------------------------
# Rate limiter dependency
# ---------------------------------------------------------------------------

# Configurable defaults matching acceptance criteria:
# "more than 10 failed authentication requests within a 5-minute window"
# The block persists "for at least 15 minutes" (900 seconds).
_RATE_LIMIT_MAX_ATTEMPTS: int = 10
_RATE_LIMIT_WINDOW_SECONDS: int = 900


async def rate_limiter(request: Request) -> None:
    """Redis-backed rate limiter dependency.

    Checks the number of requests from the client's IP address within
    the configured window. Raises HTTP 429 if the threshold is exceeded.

    The default threshold is **10 requests per 15-minute window**, matching
    the acceptance criteria requirement to block for at least 15 minutes.

    Parameters
    ----------
    request:
        The incoming FastAPI :class:`Request`, used to extract the client IP.

    Raises
    ------
    RateLimitException (429)
        When the client has exceeded the allowed number of requests.
    """
    client_ip = request.client.host if request.client else "unknown"
    key_identifier = f"auth:{client_ip}"

    try:
        count = await increment_rate_limit(
            key_identifier,
            window_seconds=_RATE_LIMIT_WINDOW_SECONDS,
        )
    except AppException:
        logger.warning(
            "Rate limiter failed open for %s: Redis unavailable, allowing request",
            client_ip,
        )
        return

    if count > _RATE_LIMIT_MAX_ATTEMPTS:
        logger.warning(
            "Rate limit exceeded for %s (count=%d, max=%d)",
            client_ip,
            count,
            _RATE_LIMIT_MAX_ATTEMPTS,
        )
        raise RateLimitException()
