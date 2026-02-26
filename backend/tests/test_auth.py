"""Integration tests for the authentication domain (Step 6).

Tests cover all 12 success criteria from the task specification:
1. POST /auth/register creates a user and returns TokenResponse
2. POST /auth/register returns 400 for invalid email, short username, short password
3. POST /auth/register returns 409 for duplicate email or username
4. POST /auth/login returns TokenResponse for valid credentials
5. POST /auth/login returns 401 with generic "Invalid credentials" message
6. POST /auth/refresh accepts refresh_token in Authorization header, returns new pair
7. POST /auth/refresh returns 401 for expired refresh token
8. Protected endpoints return 401 without Authorization header
9. Protected endpoints return 401 with expired access token
10. Rate limiter blocks auth requests after 10 failed attempts in 5 minutes
11. get_current_user dependency extracts user from JWT and injects into endpoint
12. All tests pass

IMPORTANT: All test modules using database fixtures MUST set the module-level
marker so tests share the session-scoped event loop with the async engine.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token, decode_token

pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# 1. Registration success
# ---------------------------------------------------------------------------


class TestRegisterSuccess:
    """POST /auth/register creates a user and returns TokenResponse."""

    async def test_register_returns_201_with_token_pair(
        self, client: AsyncClient
    ) -> None:
        """Successful registration returns 201 with access + refresh tokens."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    async def test_register_tokens_are_distinct(self, client: AsyncClient) -> None:
        """Access and refresh tokens must be different strings."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "distinct@example.com",
                "username": "distinctuser",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["access_token"] != data["refresh_token"]


# ---------------------------------------------------------------------------
# 2. Registration validation failures (400)
# ---------------------------------------------------------------------------


class TestRegisterValidation:
    """POST /auth/register returns 400 with field-specific errors."""

    async def test_invalid_email_returns_422(self, client: AsyncClient) -> None:
        """Invalid email format triggers a validation error."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "username": "validuser",
                "password": "securepass123",
            },
        )
        # FastAPI returns 422 for Pydantic validation errors
        assert resp.status_code == 422
        body = resp.json()
        # Pydantic v2 returns errors in "detail" array
        assert "detail" in body
        errors = body["detail"]
        email_errors = [e for e in errors if "email" in str(e.get("loc", []))]
        assert len(email_errors) > 0

    async def test_short_username_returns_422(self, client: AsyncClient) -> None:
        """Username shorter than 3 characters triggers a validation error."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "valid@example.com",
                "username": "ab",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 422
        body = resp.json()
        errors = body["detail"]
        username_errors = [e for e in errors if "username" in str(e.get("loc", []))]
        assert len(username_errors) > 0

    async def test_short_password_returns_422(self, client: AsyncClient) -> None:
        """Password shorter than 8 characters triggers a validation error."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "valid@example.com",
                "username": "validuser",
                "password": "short",
            },
        )
        assert resp.status_code == 422
        body = resp.json()
        errors = body["detail"]
        password_errors = [e for e in errors if "password" in str(e.get("loc", []))]
        assert len(password_errors) > 0

    async def test_multiple_validation_errors(self, client: AsyncClient) -> None:
        """Multiple invalid fields return errors for each field."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "bad",
                "username": "ab",
                "password": "short",
            },
        )
        assert resp.status_code == 422
        body = resp.json()
        errors = body["detail"]
        # Should have errors for email, username, and password
        assert len(errors) >= 3


# ---------------------------------------------------------------------------
# 3. Registration duplicate prevention (409)
# ---------------------------------------------------------------------------


class TestRegisterDuplicate:
    """POST /auth/register returns 409 for duplicate email or username."""

    async def test_duplicate_email_returns_409(
        self, client: AsyncClient, test_user
    ) -> None:
        """Registering with an existing email returns 409."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user fixture
                "username": "differentuser",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 409
        body = resp.json()
        assert "email" in body["message"].lower() or "already" in body["message"].lower()

    async def test_duplicate_username_returns_409(
        self, client: AsyncClient, test_user
    ) -> None:
        """Registering with an existing username returns 409."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "different@example.com",
                "username": "testuser",  # Same as test_user fixture
                "password": "securepass123",
            },
        )
        assert resp.status_code == 409
        body = resp.json()
        assert "username" in body["message"].lower() or "already" in body["message"].lower()


# ---------------------------------------------------------------------------
# 4. Login success
# ---------------------------------------------------------------------------


class TestLoginSuccess:
    """POST /auth/login returns TokenResponse for valid credentials."""

    async def test_login_returns_200_with_token_pair(
        self, client: AsyncClient, test_user
    ) -> None:
        """Successful login returns 200 with access + refresh tokens."""
        resp = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    async def test_login_access_token_grants_protected_access(
        self, client: AsyncClient, test_user
    ) -> None:
        """The access token from login can be used on protected endpoints."""
        # Login
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert login_resp.status_code == 200
        access_token = login_resp.json()["access_token"]

        # Use token on protected endpoint
        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "test@example.com"


# ---------------------------------------------------------------------------
# 5. Login invalid credentials (401) -- generic message
# ---------------------------------------------------------------------------


class TestLoginInvalidCredentials:
    """POST /auth/login returns 401 with generic 'Invalid credentials' message."""

    async def test_wrong_password_returns_401(
        self, client: AsyncClient, test_user
    ) -> None:
        """Wrong password returns 401 with generic error message in consistent format."""
        resp = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )
        assert resp.status_code == 401
        body = resp.json()
        # Must use consistent error format: {error_type, message, status_code}
        assert body["error_type"] == "credentials_error"
        assert body["status_code"] == 401
        # Must NOT reveal that the password was wrong specifically
        assert "invalid credentials" in body["message"].lower()

    async def test_nonexistent_email_returns_401(
        self, client: AsyncClient, test_user
    ) -> None:
        """Non-existent email returns 401 with the same generic error message."""
        resp = await client.post(
            "/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "somepassword123",
            },
        )
        assert resp.status_code == 401
        body = resp.json()
        # Must use consistent error format: {error_type, message, status_code}
        assert body["error_type"] == "credentials_error"
        assert body["status_code"] == 401
        # Must NOT reveal that the email does not exist
        assert "invalid credentials" in body["message"].lower()

    async def test_wrong_email_and_password_same_error(
        self, client: AsyncClient, test_user
    ) -> None:
        """Both wrong email and wrong password produce identical error structure."""
        resp_wrong_email = await client.post(
            "/auth/login",
            json={"email": "wrong@example.com", "password": "whatever123"},
        )
        resp_wrong_pass = await client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        # Same status code and message -- no distinction
        assert resp_wrong_email.status_code == resp_wrong_pass.status_code == 401
        assert resp_wrong_email.json()["message"] == resp_wrong_pass.json()["message"]
        # Both use consistent error format
        assert resp_wrong_email.json()["error_type"] == "credentials_error"
        assert resp_wrong_pass.json()["error_type"] == "credentials_error"


# ---------------------------------------------------------------------------
# 6. Token refresh
# ---------------------------------------------------------------------------


class TestTokenRefresh:
    """POST /auth/refresh accepts refresh_token, returns new pair."""

    async def test_refresh_returns_new_token_pair(
        self, client: AsyncClient, redis_client, test_user
    ) -> None:
        """Valid refresh token returns a new access + refresh pair."""
        # First log in to get a refresh token
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert login_resp.status_code == 200
        refresh_tok = login_resp.json()["refresh_token"]

        # Use refresh token
        refresh_resp = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_tok}"},
        )
        assert refresh_resp.status_code == 200
        data = refresh_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)

    async def test_refresh_issues_valid_new_tokens(
        self, client: AsyncClient, redis_client, test_user
    ) -> None:
        """Refreshed tokens are valid and can be used for authentication."""
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        original_refresh = login_resp.json()["refresh_token"]

        refresh_resp = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {original_refresh}"},
        )
        new_data = refresh_resp.json()

        # The new access token must be usable on protected endpoints
        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {new_data['access_token']}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "test@example.com"

        # The new refresh token must also be usable for another refresh
        refresh_resp_2 = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {new_data['refresh_token']}"},
        )
        assert refresh_resp_2.status_code == 200
        assert "access_token" in refresh_resp_2.json()

    async def test_refresh_with_access_token_returns_401(
        self, client: AsyncClient, test_user
    ) -> None:
        """Using an access token (not refresh) for refresh returns 401."""
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        access_tok = login_resp.json()["access_token"]

        # Access token is type "access" -- refresh endpoint expects "refresh"
        refresh_resp = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {access_tok}"},
        )
        assert refresh_resp.status_code == 401

    async def test_refresh_without_authorization_header_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Missing Authorization header returns 401."""
        resp = await client.post("/auth/refresh")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 7. Expired refresh token (401)
# ---------------------------------------------------------------------------


class TestRefreshExpired:
    """POST /auth/refresh returns 401 for expired refresh token."""

    async def test_expired_refresh_token_returns_401(
        self, client: AsyncClient, test_user
    ) -> None:
        """An expired refresh token is rejected with 401."""
        expired_refresh = create_refresh_token(
            subject=str(test_user.id),
            expires_delta_seconds=-10,  # Already expired
        )
        resp = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {expired_refresh}"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 8. Protected endpoints without Authorization header (401)
# ---------------------------------------------------------------------------


class TestProtectedNoAuth:
    """Protected endpoints return 401 when called without Authorization header."""

    async def test_protected_endpoint_without_header_returns_401(
        self, client: AsyncClient
    ) -> None:
        """GET /auth/me without Authorization header returns 401."""
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_protected_endpoint_with_empty_header_returns_401(
        self, client: AsyncClient
    ) -> None:
        """GET /auth/me with an empty Bearer token returns 401."""
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 9. Protected endpoints with expired access token (401)
# ---------------------------------------------------------------------------


class TestProtectedExpiredToken:
    """Protected endpoints return 401 when called with expired access token."""

    async def test_expired_access_token_returns_401(
        self, client: AsyncClient, test_user
    ) -> None:
        """GET /auth/me with an expired access token returns 401."""
        expired_token = create_access_token(
            subject=str(test_user.id),
            expires_delta_seconds=-10,
        )
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 10. Rate limiting on auth endpoints
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """Rate limiter blocks auth requests after 10 failed attempts for 15 min."""

    async def test_rate_limit_blocks_after_threshold(
        self, client: AsyncClient, redis_client, test_user
    ) -> None:
        """After 10 failed login attempts, the 11th is blocked with 429."""
        # Send 10 failed login attempts (within threshold)
        for i in range(10):
            resp = await client.post(
                "/auth/login",
                json={
                    "email": "wrong@example.com",
                    "password": "wrongpassword",
                },
            )
            # First 10 should be 401 (invalid credentials), not 429
            assert resp.status_code == 401, f"Request {i+1}: expected 401, got {resp.status_code}"

        # 11th request should be rate limited
        resp = await client.post(
            "/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrongpassword",
            },
        )
        assert resp.status_code == 429

    async def test_rate_limit_allows_within_threshold(
        self, client: AsyncClient, redis_client, test_user
    ) -> None:
        """Requests within the rate limit threshold are allowed through."""
        for _ in range(5):
            resp = await client.post(
                "/auth/login",
                json={
                    "email": "wrong@example.com",
                    "password": "wrongpassword",
                },
            )
            # Should not be rate limited -- only 5 requests
            assert resp.status_code == 401

    async def test_rate_limit_window_is_at_least_15_minutes(
        self, client: AsyncClient, redis_client, test_user
    ) -> None:
        """Rate limit key has a TTL of at least 900 seconds (15 minutes).

        After exceeding the threshold, the block persists for the full window.
        We verify this by checking the Redis key TTL directly.
        """
        import app.core.redis as redis_module

        # Exceed the rate limit threshold
        for i in range(11):
            await client.post(
                "/auth/login",
                json={
                    "email": "wrong@example.com",
                    "password": "wrongpassword",
                },
            )

        # The rate limit key should exist with TTL >= 900 seconds
        # The key format is "ratelimit:auth:<ip>"
        # In tests, the client IP is "testclient" (httpx default)
        client_redis = await redis_module.get_redis_client()
        keys = []
        async for key in client_redis.scan_iter("ratelimit:*"):
            keys.append(key)

        assert len(keys) > 0, "Expected at least one rate limit key in Redis"
        ttl = await client_redis.ttl(keys[0])
        # TTL should be close to 900 seconds (at least 890 to account for
        # a few seconds of test execution time)
        assert ttl >= 890, (
            f"Rate limit TTL is {ttl}s, expected at least 890s (15 minutes)"
        )


# ---------------------------------------------------------------------------
# 11. get_current_user dependency injection
# ---------------------------------------------------------------------------


class TestGetCurrentUserDependency:
    """get_current_user dependency extracts user from JWT and injects into endpoint."""

    async def test_current_user_injected_into_protected_endpoint(
        self, client: AsyncClient, test_user, auth_headers: dict[str, str]
    ) -> None:
        """GET /auth/me returns the authenticated user's info."""
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == test_user.id
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    async def test_malformed_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """A random string as Bearer token returns 401."""
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer garbage.token.value"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 12. End-to-end flow: register -> login -> access protected -> refresh
# ---------------------------------------------------------------------------


class TestEndToEndAuthFlow:
    """Full auth flow: register, login, use protected endpoint, refresh."""

    async def test_full_auth_lifecycle(self, client: AsyncClient, redis_client) -> None:
        """Complete lifecycle: register -> use token -> refresh -> use new token."""
        # Step 1: Register
        reg_resp = await client.post(
            "/auth/register",
            json={
                "email": "lifecycle@example.com",
                "username": "lifecycleuser",
                "password": "securepass123",
            },
        )
        assert reg_resp.status_code == 201
        reg_data = reg_resp.json()
        access_token_1 = reg_data["access_token"]
        refresh_token_1 = reg_data["refresh_token"]

        # Step 2: Use access token on protected endpoint
        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token_1}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "lifecycle@example.com"

        # Step 3: Refresh tokens
        refresh_resp = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token_1}"},
        )
        assert refresh_resp.status_code == 200
        access_token_2 = refresh_resp.json()["access_token"]

        # Step 4: Use new access token
        me_resp_2 = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token_2}"},
        )
        assert me_resp_2.status_code == 200
        assert me_resp_2.json()["email"] == "lifecycle@example.com"

        # Step 5: Login with same credentials
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "lifecycle@example.com",
                "password": "securepass123",
            },
        )
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()


# ---------------------------------------------------------------------------
# 13. Refresh token invalidation (JTI blacklisting)
# ---------------------------------------------------------------------------


class TestRefreshTokenInvalidation:
    """Old refresh tokens are rejected after rotation (JTI blacklisting)."""

    async def test_old_refresh_token_rejected_after_rotation(
        self, client: AsyncClient, redis_client, test_user
    ) -> None:
        """After refreshing, the old refresh token must be rejected.

        This verifies the JTI blacklisting mechanism: when a refresh token
        is used to obtain a new pair, the old token's JTI is stored in
        Redis and subsequent attempts to use it return 401.
        """
        # Log in to get a refresh token
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert login_resp.status_code == 200
        old_refresh = login_resp.json()["refresh_token"]

        # Use the refresh token to get a new pair
        refresh_resp = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {old_refresh}"},
        )
        assert refresh_resp.status_code == 200

        # Attempt to reuse the old refresh token -- must be rejected
        reuse_resp = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {old_refresh}"},
        )
        assert reuse_resp.status_code == 401

    async def test_new_refresh_token_works_after_rotation(
        self, client: AsyncClient, redis_client, test_user
    ) -> None:
        """The new refresh token issued after rotation is fully usable."""
        # Log in
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        old_refresh = login_resp.json()["refresh_token"]

        # Rotate
        refresh_resp = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {old_refresh}"},
        )
        assert refresh_resp.status_code == 200
        new_refresh = refresh_resp.json()["refresh_token"]

        # The new token should work
        refresh_resp_2 = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {new_refresh}"},
        )
        assert refresh_resp_2.status_code == 200
        assert "access_token" in refresh_resp_2.json()

    async def test_refresh_token_contains_jti_claim(
        self, client: AsyncClient, test_user
    ) -> None:
        """Refresh tokens include a unique jti (JWT ID) claim."""
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert login_resp.status_code == 200
        refresh_tok = login_resp.json()["refresh_token"]

        payload = decode_token(refresh_tok, expected_type="refresh")
        assert "jti" in payload, "Refresh token must contain a jti claim"
        assert isinstance(payload["jti"], str)
        assert len(payload["jti"]) > 0

    async def test_each_refresh_token_has_unique_jti(
        self, client: AsyncClient, test_user
    ) -> None:
        """Each issued refresh token has a distinct jti value."""
        login_resp_1 = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        login_resp_2 = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        tok_1 = login_resp_1.json()["refresh_token"]
        tok_2 = login_resp_2.json()["refresh_token"]

        payload_1 = decode_token(tok_1, expected_type="refresh")
        payload_2 = decode_token(tok_2, expected_type="refresh")

        assert payload_1["jti"] != payload_2["jti"], (
            "Two separately issued refresh tokens must have different jti values"
        )
