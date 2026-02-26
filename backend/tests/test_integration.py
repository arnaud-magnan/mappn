"""End-to-end integration tests for the Mappn backend.

Exercises the complete primary user flow:
    1. Register a new user account
    2. Login with the new credentials
    3. Search for nearby places
    4. Send GPS pings near a place
    5. Verify the visit is auto-confirmed after repeated pings spanning 5+ minutes

Also verifies:
- All error responses follow consistent format: {error_type, message, status_code}
- Health endpoint returns 200 without authentication
- The real app (app.main:app) is used (not the test_app fixture from conftest)

Uses conftest.py fixtures for PostGIS testcontainers and fakeredis.
"""

from __future__ import annotations

import datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# All tests must share the session-scoped event loop to work with the
# session-scoped async engine fixture (pytest-asyncio 0.25 pattern).
pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# Fixtures specific to integration tests
# ---------------------------------------------------------------------------

# Counter for unique user credentials across tests
_integration_user_counter = 0


def _unique_credentials() -> dict[str, str]:
    """Generate unique registration credentials for each test invocation."""
    global _integration_user_counter
    _integration_user_counter += 1
    return {
        "email": f"integ_{_integration_user_counter}@test.com",
        "username": f"integ_user_{_integration_user_counter}",
        "password": "securepassword123",
    }


async def _seed_place_for_integration(
    db: AsyncSession,
    *,
    name: str,
    category: str,
    lon: float,
    lat: float,
    google_place_id: str,
    address: str | None = None,
    city: str | None = None,
    country: str | None = None,
) -> int:
    """Insert a test place using raw SQL with ST_MakePoint for Geography.

    Returns the place ID.
    """
    result = await db.execute(
        text(
            "INSERT INTO places (google_place_id, name, category, coordinates, "
            "address, city, country) "
            "VALUES (:gid, :name, :cat, "
            "CAST(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geography), "
            ":addr, :city, :country) "
            "RETURNING id"
        ),
        {
            "gid": google_place_id,
            "name": name,
            "cat": category,
            "lon": lon,
            "lat": lat,
            "addr": address,
            "city": city,
            "country": country,
        },
    )
    place_id = result.scalar_one()
    await db.flush()
    return place_id


# ---------------------------------------------------------------------------
# Helper: create an integration client using the real app from main.py
# ---------------------------------------------------------------------------


def _create_integration_app(db_session: AsyncSession, redis_client: Any):
    """Create the real FastAPI app with dependency overrides for testing.

    Uses ``app.main.app`` to test the actual application entry point,
    but overrides get_db to use the rollback-protected test session and
    patches Redis to use fakeredis.
    """
    from app.api.deps import get_db
    from app.main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    return app


# ---------------------------------------------------------------------------
# Tests: Health Check
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Verify the /health endpoint works without authentication."""

    async def test_health_returns_ok(self, db_session: AsyncSession, redis_client: Any):
        """GET /health returns 200 with {status: ok} without any auth headers."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                response = await ac.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data == {"status": "ok"}
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests: Error Response Consistency
# ---------------------------------------------------------------------------


class TestErrorResponseFormat:
    """Verify all error responses follow the consistent format."""

    async def test_duplicate_registration_error_format(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """DuplicateEntityException returns {error_type, message, status_code}."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                creds = _unique_credentials()

                # Register first user
                resp1 = await ac.post("/auth/register", json=creds)
                assert resp1.status_code == 201

                # Attempt duplicate registration
                resp2 = await ac.post("/auth/register", json=creds)
                assert resp2.status_code == 409

                error = resp2.json()
                assert "error_type" in error
                assert "message" in error
                assert "status_code" in error
                assert error["error_type"] == "duplicate_entity"
                assert error["status_code"] == 409
        finally:
            app.dependency_overrides.clear()

    async def test_invalid_credentials_error_format(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Login with wrong credentials returns consistent {error_type, message, status_code}."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.post(
                    "/auth/login",
                    json={"email": "nonexistent@example.com", "password": "wrongpassword"},
                )
                assert resp.status_code == 401

                error = resp.json()
                assert "error_type" in error, f"Missing 'error_type' in error response: {error}"
                assert "message" in error, f"Missing 'message' in error response: {error}"
                assert "status_code" in error, f"Missing 'status_code' in error response: {error}"
                assert error["error_type"] == "credentials_error"
                assert error["status_code"] == 401
        finally:
            app.dependency_overrides.clear()

    async def test_gps_accuracy_error_format(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """GPS accuracy error returns consistent {error_type, message, status_code}."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                # Register and login
                creds = _unique_credentials()
                reg_resp = await ac.post("/auth/register", json=creds)
                assert reg_resp.status_code == 201
                token = reg_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # Send ping with bad accuracy
                resp = await ac.post(
                    "/visits/ping",
                    json={
                        "lat": 48.8566,
                        "lon": 2.3522,
                        "accuracy": 150.0,
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    },
                    headers=headers,
                )
                assert resp.status_code == 422

                error = resp.json()
                assert "error_type" in error
                assert "message" in error
                assert "status_code" in error
                assert error["error_type"] == "gps_accuracy_error"
                assert error["status_code"] == 422
        finally:
            app.dependency_overrides.clear()

    async def test_unauthenticated_access_returns_401(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Accessing protected endpoint without auth returns 401 with consistent format."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.get(
                    "/places/nearby",
                    params={"lat": 48.8566, "lon": 2.3522},
                )
                assert resp.status_code == 401

                error = resp.json()
                assert "error_type" in error, f"Missing 'error_type' in error response: {error}"
                assert "message" in error, f"Missing 'message' in error response: {error}"
                assert "status_code" in error, f"Missing 'status_code' in error response: {error}"
                assert error["error_type"] == "credentials_error"
                assert error["status_code"] == 401
        finally:
            app.dependency_overrides.clear()

    async def test_refresh_token_error_format(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Refresh with invalid token returns consistent {error_type, message, status_code}."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.post(
                    "/auth/refresh",
                    headers={"Authorization": "Bearer invalid-token-here"},
                )
                assert resp.status_code == 401

                error = resp.json()
                assert "error_type" in error, f"Missing 'error_type' in error response: {error}"
                assert "message" in error, f"Missing 'message' in error response: {error}"
                assert "status_code" in error, f"Missing 'status_code' in error response: {error}"
                assert error["error_type"] == "credentials_error"
                assert error["status_code"] == 401
        finally:
            app.dependency_overrides.clear()

    async def test_refresh_missing_auth_header_error_format(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Refresh without Authorization header returns consistent error format."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.post("/auth/refresh")
                assert resp.status_code == 401

                error = resp.json()
                assert "error_type" in error, f"Missing 'error_type' in error response: {error}"
                assert "message" in error, f"Missing 'message' in error response: {error}"
                assert "status_code" in error, f"Missing 'status_code' in error response: {error}"
                assert error["error_type"] == "credentials_error"
                assert error["status_code"] == 401
        finally:
            app.dependency_overrides.clear()

    async def test_place_not_found_error_format(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """GET /places/99999 returns consistent {error_type, message, status_code} format."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                # Register and get token
                creds = _unique_credentials()
                reg_resp = await ac.post("/auth/register", json=creds)
                assert reg_resp.status_code == 201
                token = reg_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # Request a non-existent place
                resp = await ac.get("/places/99999", headers=headers)
                assert resp.status_code == 404

                error = resp.json()
                assert "error_type" in error, f"Missing 'error_type' in error response: {error}"
                assert "message" in error, f"Missing 'message' in error response: {error}"
                assert "status_code" in error, f"Missing 'status_code' in error response: {error}"
                assert error["error_type"] == "not_found"
                assert error["status_code"] == 404
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests: Primary E2E Flow
# ---------------------------------------------------------------------------


class TestPrimaryFlow:
    """End-to-end test of the primary user flow.

    Exercises: register -> login -> search nearby places -> ping GPS near
    a place -> verify visit auto-confirmed after repeated pings.
    """

    async def test_full_primary_flow(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Complete primary flow: register, login, search, ping, auto-confirm."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)

            # Known location: a cafe in Paris near the Eiffel Tower
            # Place coordinates: lat=48.8584, lon=2.2945
            place_lat = 48.8584
            place_lon = 2.2945

            # Seed a place near the known location
            place_id = await _seed_place_for_integration(
                db_session,
                name="Cafe Near Tower",
                category="cafe",
                lon=place_lon,
                lat=place_lat,
                google_place_id="integration_test_place_001",
                address="1 Avenue Gustave Eiffel",
                city="Paris",
                country="France",
            )

            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                # -----------------------------------------------------------
                # Step 1: Register a new user
                # -----------------------------------------------------------
                creds = _unique_credentials()
                reg_resp = await ac.post("/auth/register", json=creds)
                assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"

                reg_data = reg_resp.json()
                assert "access_token" in reg_data
                assert "refresh_token" in reg_data
                assert reg_data["token_type"] == "bearer"
                assert reg_data["expires_in"] > 0

                # -----------------------------------------------------------
                # Step 2: Login with the same credentials
                # -----------------------------------------------------------
                login_resp = await ac.post(
                    "/auth/login",
                    json={"email": creds["email"], "password": creds["password"]},
                )
                assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"

                login_data = login_resp.json()
                assert "access_token" in login_data
                assert "refresh_token" in login_data

                access_token = login_data["access_token"]
                auth_headers = {"Authorization": f"Bearer {access_token}"}

                # -----------------------------------------------------------
                # Step 3: Search for nearby places
                # -----------------------------------------------------------
                # User is 20m from the cafe (well within 500m search radius
                # and within the 75m geofence radius)
                user_lat = 48.8586
                user_lon = 2.2947

                nearby_resp = await ac.get(
                    "/places/nearby",
                    params={"lat": user_lat, "lon": user_lon, "radius_m": 500},
                    headers=auth_headers,
                )
                assert nearby_resp.status_code == 200, f"Nearby search failed: {nearby_resp.text}"

                nearby_data = nearby_resp.json()
                assert isinstance(nearby_data, list)
                assert len(nearby_data) >= 1

                # Verify our seeded place is in the results
                place_ids_in_results = [p["id"] for p in nearby_data]
                assert place_id in place_ids_in_results

                found_place = next(p for p in nearby_data if p["id"] == place_id)
                assert found_place["name"] == "Cafe Near Tower"
                assert found_place["category"] == "cafe"

                # -----------------------------------------------------------
                # Step 4: Send GPS pings near the place
                # -----------------------------------------------------------
                # We need to simulate multiple pings over 5+ minutes to trigger
                # auto-confirmation. The visit service requires:
                #   - dwell_seconds >= visit_min_duration_seconds (300 = 5 min)
                #   - reading_count >= visit_min_readings (3)
                #
                # We'll send 4 pings with timestamps spaced over 6 minutes.

                base_time = datetime.datetime.now(datetime.timezone.utc)

                # Ping 1: First sighting (t=0)
                ping1_resp = await ac.post(
                    "/visits/ping",
                    json={
                        "lat": user_lat,
                        "lon": user_lon,
                        "accuracy": 10.0,
                        "timestamp": base_time.isoformat(),
                    },
                    headers=auth_headers,
                )
                assert ping1_resp.status_code == 200, f"Ping 1 failed: {ping1_resp.text}"
                ping1_data = ping1_resp.json()
                assert len(ping1_data["nearby_places"]) >= 1
                assert ping1_data["rejected"] is False
                # First ping should not confirm any visits yet
                assert len(ping1_data["confirmed_visits"]) == 0

                # Ping 2: 2 minutes later (t=2min)
                ping2_time = base_time + datetime.timedelta(minutes=2)
                ping2_resp = await ac.post(
                    "/visits/ping",
                    json={
                        "lat": user_lat,
                        "lon": user_lon,
                        "accuracy": 15.0,
                        "timestamp": ping2_time.isoformat(),
                    },
                    headers=auth_headers,
                )
                assert ping2_resp.status_code == 200
                ping2_data = ping2_resp.json()
                # Still not enough time or readings
                assert len(ping2_data["confirmed_visits"]) == 0

                # Ping 3: 4 minutes later (t=4min) -- 3 readings but only 4 min dwell
                ping3_time = base_time + datetime.timedelta(minutes=4)
                ping3_resp = await ac.post(
                    "/visits/ping",
                    json={
                        "lat": user_lat,
                        "lon": user_lon,
                        "accuracy": 12.0,
                        "timestamp": ping3_time.isoformat(),
                    },
                    headers=auth_headers,
                )
                assert ping3_resp.status_code == 200
                ping3_data = ping3_resp.json()
                # 3 readings but only 4 minutes dwell -- not enough
                assert len(ping3_data["confirmed_visits"]) == 0

                # Ping 4: 6 minutes later (t=6min) -- 4 readings and 6 min dwell
                # This should trigger auto-confirmation!
                ping4_time = base_time + datetime.timedelta(minutes=6)
                ping4_resp = await ac.post(
                    "/visits/ping",
                    json={
                        "lat": user_lat,
                        "lon": user_lon,
                        "accuracy": 8.0,
                        "timestamp": ping4_time.isoformat(),
                    },
                    headers=auth_headers,
                )
                assert ping4_resp.status_code == 200, f"Ping 4 failed: {ping4_resp.text}"
                ping4_data = ping4_resp.json()

                # The visit should now be auto-confirmed!
                assert len(ping4_data["confirmed_visits"]) == 1
                confirmed = ping4_data["confirmed_visits"][0]
                assert confirmed["place_id"] == place_id
                assert confirmed["duration_seconds"] >= 300  # >= 5 minutes

                # -----------------------------------------------------------
                # Step 5: Verify visit appears in history
                # -----------------------------------------------------------
                history_resp = await ac.get(
                    "/visits/history",
                    headers=auth_headers,
                )
                assert history_resp.status_code == 200, f"History failed: {history_resp.text}"

                history_data = history_resp.json()
                assert isinstance(history_data, list)
                assert len(history_data) >= 1

                # Find our confirmed visit in history
                our_visit = next(
                    (v for v in history_data if v["place_id"] == place_id),
                    None,
                )
                assert our_visit is not None, "Confirmed visit not found in history"
                assert our_visit["place_name"] == "Cafe Near Tower"
                assert our_visit["duration_seconds"] >= 300

        finally:
            app.dependency_overrides.clear()

    async def test_register_login_search_with_category_filter(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Register, login, and search with category filter returns filtered results."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)

            # Seed two places: a restaurant and a park at the same location
            place_lat = 40.7128
            place_lon = -74.0060

            await _seed_place_for_integration(
                db_session,
                name="NYC Restaurant",
                category="restaurant",
                lon=place_lon,
                lat=place_lat,
                google_place_id="integ_nyc_restaurant",
                city="New York",
            )

            await _seed_place_for_integration(
                db_session,
                name="NYC Park",
                category="park",
                lon=place_lon + 0.0001,  # Very close by
                lat=place_lat,
                google_place_id="integ_nyc_park",
                city="New York",
            )

            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                # Register and get token
                creds = _unique_credentials()
                reg_resp = await ac.post("/auth/register", json=creds)
                assert reg_resp.status_code == 201
                token = reg_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # Search without filter -- should find both
                resp_all = await ac.get(
                    "/places/nearby",
                    params={"lat": place_lat, "lon": place_lon, "radius_m": 500},
                    headers=headers,
                )
                assert resp_all.status_code == 200
                all_places = resp_all.json()
                categories = {p["category"] for p in all_places}
                assert "restaurant" in categories
                assert "park" in categories

                # Search with category filter -- should find only restaurants
                resp_filtered = await ac.get(
                    "/places/nearby",
                    params={
                        "lat": place_lat,
                        "lon": place_lon,
                        "radius_m": 500,
                        "category": "restaurant",
                    },
                    headers=headers,
                )
                assert resp_filtered.status_code == 200
                filtered_places = resp_filtered.json()
                assert len(filtered_places) >= 1
                assert all(p["category"] == "restaurant" for p in filtered_places)

        finally:
            app.dependency_overrides.clear()

    async def test_refresh_token_flow(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Register, login, refresh token, and use new tokens to access protected endpoint."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                # -----------------------------------------------------------
                # Step 1: Register a new user
                # -----------------------------------------------------------
                creds = _unique_credentials()
                reg_resp = await ac.post("/auth/register", json=creds)
                assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"

                reg_data = reg_resp.json()
                assert "access_token" in reg_data
                assert "refresh_token" in reg_data
                original_refresh = reg_data["refresh_token"]

                # -----------------------------------------------------------
                # Step 2: Refresh the token
                # -----------------------------------------------------------
                refresh_resp = await ac.post(
                    "/auth/refresh",
                    headers={"Authorization": f"Bearer {original_refresh}"},
                )
                assert refresh_resp.status_code == 200, f"Refresh failed: {refresh_resp.text}"

                refresh_data = refresh_resp.json()
                assert "access_token" in refresh_data
                assert "refresh_token" in refresh_data
                assert refresh_data["token_type"] == "bearer"
                assert refresh_data["expires_in"] > 0

                # New refresh token must differ (each has a unique jti)
                new_access = refresh_data["access_token"]
                new_refresh = refresh_data["refresh_token"]
                assert new_refresh != original_refresh, (
                    "Refresh token should differ after rotation (unique jti)"
                )

                # -----------------------------------------------------------
                # Step 3: Use new access token to hit a protected endpoint
                # -----------------------------------------------------------
                me_resp = await ac.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {new_access}"},
                )
                assert me_resp.status_code == 200, f"/auth/me failed: {me_resp.text}"
                me_data = me_resp.json()
                assert me_data["email"] == creds["email"]
                assert me_data["username"] == creds["username"]

                # -----------------------------------------------------------
                # Step 4: Old refresh token should be revoked (JTI blacklisted)
                # -----------------------------------------------------------
                reuse_resp = await ac.post(
                    "/auth/refresh",
                    headers={"Authorization": f"Bearer {original_refresh}"},
                )
                assert reuse_resp.status_code == 401, (
                    f"Old refresh token should be rejected, got: {reuse_resp.status_code}"
                )
                reuse_error = reuse_resp.json()
                assert reuse_error["error_type"] == "credentials_error"

        finally:
            app.dependency_overrides.clear()

    async def test_concurrent_place_proximity_visit_tracking(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """User near two places simultaneously gets separate visits tracked."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)

            # Two places very close together (within 75m of a single user position)
            base_lat = 51.5074
            base_lon = -0.1278

            place_id_1 = await _seed_place_for_integration(
                db_session,
                name="London Cafe A",
                category="cafe",
                lon=base_lon,
                lat=base_lat,
                google_place_id="integ_london_cafe_a",
                city="London",
            )

            # Second place ~30m away (within 75m geofence)
            place_id_2 = await _seed_place_for_integration(
                db_session,
                name="London Cafe B",
                category="cafe",
                lon=base_lon + 0.0003,
                lat=base_lat,
                google_place_id="integ_london_cafe_b",
                city="London",
            )

            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                # Register and get token
                creds = _unique_credentials()
                reg_resp = await ac.post("/auth/register", json=creds)
                assert reg_resp.status_code == 201
                token = reg_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # User position between the two places
                user_lat = base_lat
                user_lon = base_lon + 0.00015

                base_time = datetime.datetime.now(datetime.timezone.utc)

                # Send 4 pings over 6+ minutes to trigger auto-confirmation
                for i, minutes in enumerate([0, 2, 4, 6]):
                    ping_time = base_time + datetime.timedelta(minutes=minutes)
                    resp = await ac.post(
                        "/visits/ping",
                        json={
                            "lat": user_lat,
                            "lon": user_lon,
                            "accuracy": 10.0,
                            "timestamp": ping_time.isoformat(),
                        },
                        headers=headers,
                    )
                    assert resp.status_code == 200, f"Ping {i+1} failed: {resp.text}"

                    data = resp.json()
                    # Should detect both places nearby
                    assert len(data["nearby_places"]) >= 2

                    if i == 3:  # Last ping should confirm visits
                        # Both places should be confirmed
                        confirmed_place_ids = {
                            v["place_id"] for v in data["confirmed_visits"]
                        }
                        assert place_id_1 in confirmed_place_ids, (
                            f"Place {place_id_1} not confirmed. "
                            f"Confirmed: {confirmed_place_ids}"
                        )
                        assert place_id_2 in confirmed_place_ids, (
                            f"Place {place_id_2} not confirmed. "
                            f"Confirmed: {confirmed_place_ids}"
                        )

        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests: API Documentation Availability
# ---------------------------------------------------------------------------


class TestAPIDocumentation:
    """Verify API documentation endpoints are accessible."""

    async def test_swagger_ui_accessible(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """GET /docs returns 200 (Swagger UI)."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.get("/docs")
                assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    async def test_redoc_accessible(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """GET /redoc returns 200 (ReDoc)."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.get("/redoc")
                assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    async def test_openapi_schema_accessible(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """GET /openapi.json returns the OpenAPI schema."""
        app = _create_integration_app(db_session, redis_client)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.get("/openapi.json")
                assert resp.status_code == 200
                schema = resp.json()
                # Verify routers are registered
                paths = schema.get("paths", {})
                assert "/auth/register" in paths
                assert "/auth/login" in paths
                assert "/places/nearby" in paths
                assert "/visits/ping" in paths
                assert "/health" in paths
        finally:
            app.dependency_overrides.clear()
