"""Security utilities for password hashing (bcrypt) and JWT token management.

Uses PyJWT (import jwt) for token encoding/decoding and bcrypt for password
hashing.  All functions are synchronous as they perform CPU-bound work
(hashing) or lightweight encoding (JWT).
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt

from app.config import get_settings

# ---------------------------------------------------------------------------
# Password hashing (bcrypt)
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Returns a bcrypt hash string (starts with ``$2b$``).
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify *plain_password* against a bcrypt *hashed_password*.

    Returns ``True`` when the password matches, ``False`` otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

_ALGORITHM = "HS256"


def create_access_token(
    subject: str,
    expires_delta_seconds: int | None = None,
) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    subject:
        Value for the ``sub`` claim (typically a user ID).
    expires_delta_seconds:
        Override for token lifetime in seconds.  When *None* the value from
        ``Settings.access_token_expire_minutes`` is used.  A negative value
        produces an already-expired token (useful in tests).
    """
    settings = get_settings()
    if expires_delta_seconds is not None:
        delta = timedelta(seconds=expires_delta_seconds)
    else:
        delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "exp": now + delta,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def create_refresh_token(
    subject: str,
    expires_delta_seconds: int | None = None,
) -> str:
    """Create a signed JWT refresh token.

    Each refresh token includes a unique ``jti`` (JWT ID) claim so it can
    be individually revoked via Redis blacklisting on token rotation.

    Parameters
    ----------
    subject:
        Value for the ``sub`` claim (typically a user ID).
    expires_delta_seconds:
        Override for token lifetime in seconds.  When *None* the value from
        ``Settings.refresh_token_expire_days`` is used.  A negative value
        produces an already-expired token (useful in tests).
    """
    settings = get_settings()
    if expires_delta_seconds is not None:
        delta = timedelta(seconds=expires_delta_seconds)
    else:
        delta = timedelta(days=settings.refresh_token_expire_days)

    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "exp": now + delta,
        "type": "refresh",
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_token(token: str, expected_type: str | None = None) -> dict:
    """Decode and validate a JWT token.

    Parameters
    ----------
    token:
        The JWT string to decode.
    expected_type:
        If provided, the ``type`` claim in the token must match this value.
        For example, pass ``"access"`` to reject refresh tokens.

    Returns the payload dictionary on success.

    Raises
    ------
    jwt.ExpiredSignatureError
        When the token has expired.
    jwt.InvalidTokenError
        When the token is malformed, tampered, signed with a wrong key,
        or has a ``type`` claim that does not match *expected_type*.
    """
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    if expected_type and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Invalid token type")
    return payload
