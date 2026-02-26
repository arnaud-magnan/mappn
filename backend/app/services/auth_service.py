"""Authentication service layer.

Provides business logic for user registration, authentication, JWT token
pair creation, and token refresh with rotation and JTI blacklisting.

All functions are async and accept an ``AsyncSession`` for database
operations.

Public API:
- ``register_user()``     -- create account, check duplicates, hash password
- ``authenticate_user()`` -- verify email + password, return user or ``None``
- ``create_token_pair()`` -- issue an access + refresh JWT pair
- ``refresh_token_pair()``-- decode refresh JWT, blacklist old JTI, issue new pair
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import CredentialsException, DuplicateEntityException
from app.core.redis import blacklist_jti, is_jti_blacklisted
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse

# Pre-computed bcrypt hash used for constant-time comparison when the user
# does not exist.  This prevents timing side-channel attacks that could
# reveal whether an email is registered.
_DUMMY_HASH = hash_password("dummy-password-for-timing-equalisation")


async def register_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str,
) -> User:
    """Register a new user account.

    Checks for duplicate email and username, hashes the password with bcrypt,
    and inserts a new ``User`` row.

    Parameters
    ----------
    db:
        Async database session.
    email:
        User-provided email address (already validated by Pydantic schema).
    username:
        User-provided username (already validated by Pydantic schema).
    password:
        Plaintext password (will be hashed before storage).

    Returns
    -------
    User
        The newly created user ORM instance (with ``id`` assigned after flush).

    Raises
    ------
    DuplicateEntityException
        When a user with the same email or username already exists.
    """
    # Check for duplicate email
    result = await db.execute(select(User).where(User.email == email))
    if result.scalars().first() is not None:
        raise DuplicateEntityException("Email is already taken")

    # Check for duplicate username
    result = await db.execute(select(User).where(User.username == username))
    if result.scalars().first() is not None:
        raise DuplicateEntityException("Username is already taken")

    # Hash password and create user
    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.flush()  # Assigns user.id without committing

    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Authenticate a user by email and password.

    Performs a constant-time password comparison even when the email does not
    exist.  When no user is found for the given email, a dummy bcrypt
    ``verify_password()`` call is made against ``_DUMMY_HASH`` so that the
    response time is indistinguishable from a real comparison.  This prevents
    timing side-channel attacks that could enumerate registered emails.

    Parameters
    ----------
    db:
        Async database session.
    email:
        User-provided email.
    password:
        User-provided plaintext password.

    Returns
    -------
    User | None
        The authenticated user, or ``None`` if credentials are invalid.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user is None:
        # Perform a dummy bcrypt comparison to equalise timing regardless
        # of whether the email exists in the database.
        verify_password(password, _DUMMY_HASH)
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_token_pair(user: User) -> TokenResponse:
    """Generate an access + refresh JWT pair for *user*.

    Token lifetimes are read from application settings.

    Parameters
    ----------
    user:
        The authenticated user ORM instance.

    Returns
    -------
    TokenResponse
        Contains ``access_token``, ``refresh_token``, ``token_type``, and
        ``expires_in`` (access token lifetime in seconds).
    """
    settings = get_settings()
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def refresh_token_pair(
    token: str,
    db: AsyncSession,
) -> TokenResponse:
    """Validate a refresh token and issue a new access + refresh pair.

    Implements refresh token rotation with JTI blacklisting:

    1. Decode the JWT and verify it is a refresh token.
    2. Check whether the token's ``jti`` has been blacklisted in Redis.
    3. Blacklist the old token's ``jti`` (TTL = refresh token lifetime).
    4. Issue a fresh token pair with a new ``jti``.

    This ensures that each refresh token can only be used once.

    Parameters
    ----------
    token:
        The JWT refresh token string.
    db:
        Async database session (used to verify the user still exists).

    Returns
    -------
    TokenResponse
        A new token pair (access + refresh).

    Raises
    ------
    CredentialsException
        When the token is invalid, expired, not a refresh token, has a
        blacklisted JTI, or the user no longer exists.
    """
    import jwt as pyjwt

    try:
        payload = decode_token(token, expected_type="refresh")
    except pyjwt.InvalidTokenError:
        raise CredentialsException("Invalid or expired refresh token")

    sub = payload.get("sub")
    if sub is None:
        raise CredentialsException("Invalid refresh token")

    # Check JTI blacklist -- reject previously-used refresh tokens
    jti = payload.get("jti")
    if jti is not None and await is_jti_blacklisted(jti):
        raise CredentialsException("Refresh token has been revoked")

    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise CredentialsException("Invalid refresh token")

    user = await db.get(User, user_id)
    if user is None:
        raise CredentialsException("User not found")

    # Blacklist the old refresh token's JTI so it cannot be reused.
    # TTL = refresh token lifetime in seconds so the blacklist entry
    # auto-expires when the token would have expired anyway.
    if jti is not None:
        settings = get_settings()
        ttl = settings.refresh_token_expire_days * 86400  # days -> seconds
        await blacklist_jti(jti, ttl_seconds=ttl)

    return create_token_pair(user)
