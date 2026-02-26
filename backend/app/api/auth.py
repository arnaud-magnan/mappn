"""Authentication API endpoints.

Provides:
- ``POST /auth/register`` -- create a new user account, return token pair
- ``POST /auth/login``    -- authenticate with email + password, return token pair
- ``POST /auth/refresh``  -- exchange a refresh token for a new pair

All endpoints use the shared dependencies from :mod:`app.api.deps`:
``get_db`` for database sessions, ``rate_limiter`` for brute-force protection
on login, and ``get_current_user`` for the ``/auth/me`` protected endpoint.

Rate limiting is applied to ``/auth/login`` to enforce the acceptance
criteria: block after 10 failed attempts in 5 minutes from the same IP.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, rate_limiter
from app.core.exceptions import CredentialsException
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import (
    authenticate_user,
    create_token_pair,
    refresh_token_pair,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user account.

    Validates the input fields (email format, username >= 3 chars,
    password >= 8 chars) via the ``RegisterRequest`` Pydantic model.
    Returns a JWT token pair on success.

    Raises
    ------
    ValidationError (422)
        When input validation fails (handled by FastAPI/Pydantic).
    DuplicateEntityException (409)
        When the email or username is already taken (handled by the
        global exception handler via :mod:`app.core.exceptions`).
    """
    user = await register_user(
        db=db,
        email=body.email,
        username=body.username,
        password=body.password,
    )
    return create_token_pair(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limiter),
) -> TokenResponse:
    """Authenticate a user and return a token pair.

    Rate-limited: after 10 failed attempts in 5 minutes from the same IP,
    further requests are blocked for at least 15 minutes.

    The error message is intentionally generic ("Invalid credentials") to
    avoid revealing whether the email or password was incorrect.

    Raises
    ------
    CredentialsException (401)
        When the email or password is incorrect.
    RateLimitException (429)
        When the rate limit is exceeded (handled by ``rate_limiter``
        dependency).
    """
    user = await authenticate_user(db=db, email=body.email, password=body.password)
    if user is None:
        raise CredentialsException("Invalid credentials")
    return create_token_pair(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a refresh token for a new access + refresh pair.

    The refresh token must be sent in the ``Authorization`` header as
    ``Bearer <refresh_token>``.

    Raises
    ------
    CredentialsException (401)
        When the Authorization header is missing or the refresh token
        is invalid/expired.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise CredentialsException("Missing or invalid Authorization header")

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        raise CredentialsException("Missing refresh token")

    return await refresh_token_pair(token=token, db=db)


@router.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the currently authenticated user's basic info.

    This is a protected endpoint that demonstrates ``get_current_user``
    dependency injection.  It requires a valid access token in the
    Authorization header.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }
