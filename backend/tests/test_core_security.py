"""Unit tests for backend/app/core/security.py.

Tests cover:
- Password hashing and verification (bcrypt)
- Access token creation and decoding (JWT)
- Refresh token creation and decoding (JWT)
- Expired token handling
- Invalid token handling
- Token type validation
"""

import os
import time

# Set environment variables before any app imports so get_settings() works.
# These are test-only values; no real connections are made for unit tests.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")

# Clear the lru_cache on get_settings so our env vars take effect
from app.config import get_settings
get_settings.cache_clear()

import pytest
import jwt as pyjwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


# ---------------------------------------------------------------------------
# Password hashing / verification
# ---------------------------------------------------------------------------


class TestPasswordHashing:
    """Tests for hash_password() and verify_password()."""

    def test_hash_password_returns_bcrypt_hash(self) -> None:
        """hash_password() should return a string starting with '$2b$' (bcrypt)."""
        hashed = hash_password("mysecretpassword")
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_different_each_call(self) -> None:
        """Two calls with the same plaintext should produce different hashes (salted)."""
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2

    def test_verify_password_correct(self) -> None:
        """verify_password() should return True for the correct plaintext."""
        hashed = hash_password("correctpassword")
        assert verify_password("correctpassword", hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """verify_password() should return False for a wrong plaintext."""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty_string(self) -> None:
        """verify_password() should handle empty string comparison."""
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False


# ---------------------------------------------------------------------------
# Access token creation / decoding
# ---------------------------------------------------------------------------


class TestAccessToken:
    """Tests for create_access_token() and decode_token()."""

    def test_create_access_token_returns_string(self) -> None:
        """create_access_token() should return a JWT string."""
        token = create_access_token(subject="user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_required_claims(self) -> None:
        """Decoded access token must contain sub, exp, and type claims."""
        token = create_access_token(subject="user-456")
        payload = decode_token(token)
        assert payload["sub"] == "user-456"
        assert "exp" in payload
        assert payload["type"] == "access"

    def test_access_token_subject_preserved(self) -> None:
        """The subject (sub) claim must exactly match what was provided."""
        token = create_access_token(subject="42")
        payload = decode_token(token)
        assert payload["sub"] == "42"


# ---------------------------------------------------------------------------
# Refresh token creation / decoding
# ---------------------------------------------------------------------------


class TestRefreshToken:
    """Tests for create_refresh_token() and decode_token()."""

    def test_create_refresh_token_returns_string(self) -> None:
        """create_refresh_token() should return a JWT string."""
        token = create_refresh_token(subject="user-789")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_contains_required_claims(self) -> None:
        """Decoded refresh token must contain sub, exp, and type='refresh'."""
        token = create_refresh_token(subject="user-789")
        payload = decode_token(token)
        assert payload["sub"] == "user-789"
        assert "exp" in payload
        assert payload["type"] == "refresh"

    def test_refresh_token_different_from_access_token(self) -> None:
        """Access and refresh tokens for the same subject should differ."""
        access = create_access_token(subject="user-1")
        refresh = create_refresh_token(subject="user-1")
        assert access != refresh


# ---------------------------------------------------------------------------
# Expired token handling
# ---------------------------------------------------------------------------


class TestExpiredToken:
    """Tests that expired tokens are properly rejected."""

    def test_expired_access_token_raises(self) -> None:
        """decode_token() should raise for an expired access token."""
        # Create a token that expired 10 seconds ago
        token = create_access_token(subject="user-exp", expires_delta_seconds=-10)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_token(token)

    def test_expired_refresh_token_raises(self) -> None:
        """decode_token() should raise for an expired refresh token."""
        token = create_refresh_token(subject="user-exp", expires_delta_seconds=-10)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_token(token)


# ---------------------------------------------------------------------------
# Invalid token handling
# ---------------------------------------------------------------------------


class TestInvalidToken:
    """Tests that malformed or tampered tokens are properly rejected."""

    def test_invalid_token_string_raises(self) -> None:
        """decode_token() should raise for a garbage string."""
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_token("not.a.valid.token")

    def test_tampered_token_raises(self) -> None:
        """decode_token() should raise when the token payload is tampered."""
        token = create_access_token(subject="user-tamper")
        # Flip a character in the payload section (second segment)
        parts = token.split(".")
        payload_chars = list(parts[1])
        # Change last char
        payload_chars[-1] = "A" if payload_chars[-1] != "A" else "B"
        parts[1] = "".join(payload_chars)
        tampered = ".".join(parts)
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_token(tampered)

    def test_token_with_wrong_secret_raises(self) -> None:
        """decode_token() should reject tokens signed with a different secret."""
        wrong_token = pyjwt.encode(
            {"sub": "user-wrong", "exp": time.time() + 3600, "type": "access"},
            "completely-wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_token(wrong_token)


# ---------------------------------------------------------------------------
# Token type validation
# ---------------------------------------------------------------------------


class TestTokenTypeValidation:
    """Tests that decode_token() validates the 'type' claim when expected_type is provided."""

    def test_access_token_accepted_with_expected_type_access(self) -> None:
        """decode_token() should accept an access token when expected_type='access'."""
        token = create_access_token(subject="user-type-1")
        payload = decode_token(token, expected_type="access")
        assert payload["sub"] == "user-type-1"
        assert payload["type"] == "access"

    def test_refresh_token_accepted_with_expected_type_refresh(self) -> None:
        """decode_token() should accept a refresh token when expected_type='refresh'."""
        token = create_refresh_token(subject="user-type-2")
        payload = decode_token(token, expected_type="refresh")
        assert payload["sub"] == "user-type-2"
        assert payload["type"] == "refresh"

    def test_refresh_token_rejected_when_access_expected(self) -> None:
        """decode_token() should reject a refresh token when expected_type='access'."""
        token = create_refresh_token(subject="user-type-3")
        with pytest.raises(pyjwt.InvalidTokenError, match="Invalid token type"):
            decode_token(token, expected_type="access")

    def test_access_token_rejected_when_refresh_expected(self) -> None:
        """decode_token() should reject an access token when expected_type='refresh'."""
        token = create_access_token(subject="user-type-4")
        with pytest.raises(pyjwt.InvalidTokenError, match="Invalid token type"):
            decode_token(token, expected_type="refresh")

    def test_no_type_validation_when_expected_type_is_none(self) -> None:
        """decode_token() should not validate type when expected_type is None (default)."""
        access_token = create_access_token(subject="user-type-5")
        refresh_token = create_refresh_token(subject="user-type-5")
        # Both should decode without error
        decode_token(access_token)
        decode_token(refresh_token)

    def test_token_without_type_claim_rejected_when_type_expected(self) -> None:
        """decode_token() should reject a token missing the 'type' claim when expected_type is set."""
        # Create a token manually without a type claim
        from app.config import get_settings
        settings = get_settings()
        token_no_type = pyjwt.encode(
            {"sub": "user-no-type", "exp": time.time() + 3600},
            settings.secret_key,
            algorithm="HS256",
        )
        with pytest.raises(pyjwt.InvalidTokenError, match="Invalid token type"):
            decode_token(token_no_type, expected_type="access")
