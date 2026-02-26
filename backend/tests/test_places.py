"""Tests for the Places service, forecast service, and API endpoints.

Covers all Step 7 acceptance criteria:
- GET /places/nearby returns places within radius using PostGIS ST_DWithin
- GET /places/nearby accepts optional category filter
- GET /places/nearby results include current_busyness and busyness_stale
- GET /places/nearby results are ordered by distance
- GET /places/{id} returns full place detail with busyness_data
- GET /places/{id} returns busyness fields as null when no busyness data
- GET /places/{id} includes busyness_stale=true when data > 7 days old
- GET /places/{id}/forecast returns predicted_busyness
- GET /places/{id}/forecast returns 404 for non-existent place
- Nearby search performance target (< 2s for 500m radius)
"""

from __future__ import annotations

import datetime
import time
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.place import Place
from app.services.forecast_service import predict_busyness
from app.services.places_service import (
    _extract_current_busyness,
    _is_busyness_stale,
    get_nearby_places,
    get_place_detail,
)

# All tests must share the session-scoped event loop to work with the
# session-scoped async engine fixture (pytest-asyncio 0.25 pattern).
pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# Sample busyness data for test fixtures
# ---------------------------------------------------------------------------

SAMPLE_BUSYNESS_DATA: dict[str, Any] = {
    "popular_times": [
        {"day": 0, "hours": [0, 0, 0, 5, 10, 25, 45, 60, 75, 80, 70, 55, 40, 35, 30, 40, 55, 70, 80, 65, 45, 25, 10, 0]},
        {"day": 1, "hours": [0, 0, 0, 5, 10, 20, 40, 55, 70, 75, 65, 50, 35, 30, 25, 35, 50, 65, 75, 60, 40, 20, 10, 0]},
        {"day": 2, "hours": [0, 0, 0, 5, 10, 20, 40, 55, 70, 75, 65, 50, 35, 30, 25, 35, 50, 65, 75, 60, 40, 20, 10, 0]},
        {"day": 3, "hours": [0, 0, 0, 5, 10, 20, 40, 55, 70, 75, 65, 50, 35, 30, 25, 35, 50, 65, 75, 60, 40, 20, 10, 0]},
        {"day": 4, "hours": [0, 0, 0, 5, 15, 30, 50, 65, 80, 85, 75, 60, 45, 40, 35, 45, 60, 75, 85, 70, 50, 30, 15, 0]},
        {"day": 5, "hours": [0, 0, 0, 0, 5, 15, 35, 50, 65, 70, 60, 45, 30, 25, 20, 30, 45, 60, 70, 55, 35, 15, 5, 0]},
        {"day": 6, "hours": [0, 0, 0, 0, 5, 10, 25, 40, 55, 60, 50, 35, 20, 15, 10, 20, 35, 50, 60, 45, 25, 10, 5, 0]},
    ],
    "current_popularity": 65,
    "time_spent": [15, 30],
}


# ---------------------------------------------------------------------------
# Helper to seed test places with PostGIS coordinates
# ---------------------------------------------------------------------------


async def _seed_place(
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
    busyness_data: dict | None = None,
    busyness_updated_at: datetime.datetime | None = None,
) -> int:
    """Insert a test place using raw SQL with ST_MakePoint for Geography.

    Returns the place ID.
    """
    result = await db.execute(
        text(
            "INSERT INTO places (google_place_id, name, category, coordinates, "
            "address, city, country, busyness_data, busyness_updated_at) "
            "VALUES (:gid, :name, :cat, "
            "CAST(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geography), "
            ":addr, :city, :country, "
            "CAST(:bd AS jsonb), :bua) "
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
            "bd": _jsonb_or_none(busyness_data),
            "bua": busyness_updated_at,
        },
    )
    place_id = result.scalar_one()
    await db.flush()
    return place_id


def _jsonb_or_none(data: dict | None) -> str | None:
    """Serialize dict to JSON string for JSONB insertion, or None."""
    if data is None:
        return None
    import json

    return json.dumps(data)


# ---------------------------------------------------------------------------
# Unit tests: forecast_service.predict_busyness
# ---------------------------------------------------------------------------


class TestPredictBusyness:
    """Unit tests for the forecast service's predict_busyness function."""

    def test_returns_predicted_value_for_valid_day_hour(self):
        """Should return the hourly value from the histogram."""
        # Day 0, hour 9 should return 80 (from SAMPLE_BUSYNESS_DATA)
        result = predict_busyness(SAMPLE_BUSYNESS_DATA, day=0, hour=9)
        assert result == 80

    def test_returns_predicted_value_for_different_day(self):
        """Should return the correct value for a different day."""
        # Day 4, hour 9 should return 85
        result = predict_busyness(SAMPLE_BUSYNESS_DATA, day=4, hour=9)
        assert result == 85

    def test_returns_none_for_no_busyness_data(self):
        """Should return None when busyness_data is None."""
        result = predict_busyness(None, day=0, hour=9)
        assert result is None

    def test_returns_none_for_missing_popular_times(self):
        """Should return None when popular_times key is missing."""
        result = predict_busyness({"current_popularity": 65}, day=0, hour=9)
        assert result is None

    def test_returns_none_for_empty_popular_times(self):
        """Should return None when popular_times is an empty list."""
        result = predict_busyness({"popular_times": []}, day=0, hour=9)
        assert result is None

    def test_returns_none_for_invalid_day(self):
        """Should return None when the requested day is not in the data."""
        result = predict_busyness(SAMPLE_BUSYNESS_DATA, day=7, hour=9)
        assert result is None

    def test_returns_none_for_invalid_hour(self):
        """Should return None when hour is out of bounds."""
        result = predict_busyness(SAMPLE_BUSYNESS_DATA, day=0, hour=25)
        assert result is None

    def test_returns_value_for_midnight(self):
        """Should return the value for hour 0 (midnight)."""
        result = predict_busyness(SAMPLE_BUSYNESS_DATA, day=0, hour=0)
        assert result == 0

    def test_returns_value_for_last_hour(self):
        """Should return the value for hour 23."""
        result = predict_busyness(SAMPLE_BUSYNESS_DATA, day=0, hour=23)
        assert result == 0


# ---------------------------------------------------------------------------
# Unit tests: places_service helpers
# ---------------------------------------------------------------------------


class TestStalenessDetection:
    """Unit tests for _is_busyness_stale helper."""

    def test_not_stale_when_updated_recently(self):
        """Data updated within 7 days should not be stale."""
        recent = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)
        assert _is_busyness_stale(recent) is False

    def test_stale_when_updated_over_7_days_ago(self):
        """Data updated over 7 days ago should be stale."""
        old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
        assert _is_busyness_stale(old) is True

    def test_not_stale_when_none(self):
        """None busyness_updated_at should not be considered stale (no data exists)."""
        assert _is_busyness_stale(None) is False

    def test_stale_at_exactly_7_days(self):
        """Data exactly at the 7-day boundary should be stale (< threshold)."""
        boundary = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7, seconds=1)
        assert _is_busyness_stale(boundary) is True


class TestExtractCurrentBusyness:
    """Unit tests for _extract_current_busyness helper."""

    def test_returns_value_when_present(self):
        """Should return current_popularity from busyness_data."""
        assert _extract_current_busyness(SAMPLE_BUSYNESS_DATA) == 65

    def test_returns_none_when_no_data(self):
        """Should return None when busyness_data is None."""
        assert _extract_current_busyness(None) is None

    def test_returns_none_when_key_missing(self):
        """Should return None when current_popularity key is absent."""
        assert _extract_current_busyness({"popular_times": []}) is None


# ---------------------------------------------------------------------------
# Integration tests: places_service with PostGIS database
# ---------------------------------------------------------------------------


class TestGetNearbyPlaces:
    """Integration tests for get_nearby_places with real PostGIS."""

    async def test_returns_places_within_radius(self, db_session: AsyncSession):
        """Places within the search radius should be returned."""
        # Seed a place at a known location (Paris center: 48.8566, 2.3522)
        await _seed_place(
            db_session,
            name="Cafe Paris",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="place_nearby_1",
            address="1 Rue de Rivoli",
        )
        # Search from a point very close (within 200m)
        results = await get_nearby_places(
            db_session, lat=48.8570, lon=2.3525, radius_m=500
        )
        assert len(results) >= 1
        names = [r["name"] for r in results]
        assert "Cafe Paris" in names

    async def test_excludes_places_outside_radius(self, db_session: AsyncSession):
        """Places outside the search radius should not be returned."""
        # Place at Paris
        await _seed_place(
            db_session,
            name="Far Away Place",
            category="restaurant",
            lon=2.3522,
            lat=48.8566,
            google_place_id="place_far_1",
        )
        # Search from a point far away (London: 51.5074, -0.1278)
        results = await get_nearby_places(
            db_session, lat=51.5074, lon=-0.1278, radius_m=500
        )
        names = [r["name"] for r in results]
        assert "Far Away Place" not in names

    async def test_category_filter(self, db_session: AsyncSession):
        """Category filter should return only matching places."""
        await _seed_place(
            db_session,
            name="Paris Restaurant",
            category="restaurant",
            lon=2.3500,
            lat=48.8560,
            google_place_id="place_cat_rest",
        )
        await _seed_place(
            db_session,
            name="Paris Cafe",
            category="cafe",
            lon=2.3510,
            lat=48.8560,
            google_place_id="place_cat_cafe",
        )
        # Filter by category=restaurant
        results = await get_nearby_places(
            db_session, lat=48.8560, lon=2.3505, radius_m=2000, category="restaurant"
        )
        categories = [r["category"] for r in results]
        assert all(c == "restaurant" for c in categories)
        names = [r["name"] for r in results]
        assert "Paris Restaurant" in names
        assert "Paris Cafe" not in names

    async def test_results_ordered_by_distance(self, db_session: AsyncSession):
        """Results should be ordered by ascending distance from user."""
        # Place A: closer to search point
        await _seed_place(
            db_session,
            name="Close Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="place_ord_close",
        )
        # Place B: further from search point (same category)
        await _seed_place(
            db_session,
            name="Further Place",
            category="cafe",
            lon=2.3560,
            lat=48.8580,
            google_place_id="place_ord_far",
        )
        # Search from a point closest to Place A
        results = await get_nearby_places(
            db_session, lat=48.8566, lon=2.3522, radius_m=2000
        )
        # Find indices of our two places
        names = [r["name"] for r in results]
        if "Close Place" in names and "Further Place" in names:
            close_idx = names.index("Close Place")
            far_idx = names.index("Further Place")
            assert close_idx < far_idx, "Closer place should appear before further place"

    async def test_includes_busyness_fields(self, db_session: AsyncSession):
        """Results should include current_busyness and busyness_stale."""
        await _seed_place(
            db_session,
            name="Busy Place",
            category="restaurant",
            lon=2.3530,
            lat=48.8570,
            google_place_id="place_busy_1",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        results = await get_nearby_places(
            db_session, lat=48.8570, lon=2.3530, radius_m=500
        )
        busy_place = next((r for r in results if r["name"] == "Busy Place"), None)
        assert busy_place is not None
        assert busy_place["current_busyness"] == 65
        assert busy_place["busyness_stale"] is False

    async def test_busyness_null_when_no_data(self, db_session: AsyncSession):
        """current_busyness should be null when no busyness data exists."""
        await _seed_place(
            db_session,
            name="No Busyness Place",
            category="park",
            lon=2.3540,
            lat=48.8575,
            google_place_id="place_nobusy_1",
        )
        results = await get_nearby_places(
            db_session, lat=48.8575, lon=2.3540, radius_m=500
        )
        place = next((r for r in results if r["name"] == "No Busyness Place"), None)
        assert place is not None
        assert place["current_busyness"] is None

    async def test_busyness_stale_when_old_data(self, db_session: AsyncSession):
        """busyness_stale should be True when data is older than 7 days."""
        old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)
        await _seed_place(
            db_session,
            name="Stale Data Place",
            category="bar",
            lon=2.3545,
            lat=48.8572,
            google_place_id="place_stale_1",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=old_time,
        )
        results = await get_nearby_places(
            db_session, lat=48.8572, lon=2.3545, radius_m=500
        )
        stale_place = next((r for r in results if r["name"] == "Stale Data Place"), None)
        assert stale_place is not None
        assert stale_place["busyness_stale"] is True


# ---------------------------------------------------------------------------
# Integration tests: get_place_detail
# ---------------------------------------------------------------------------


class TestGetPlaceDetail:
    """Integration tests for get_place_detail."""

    async def test_returns_full_detail(self, db_session: AsyncSession):
        """Should return full place detail including busyness_data."""
        place_id = await _seed_place(
            db_session,
            name="Detail Place",
            category="restaurant",
            lon=2.3600,
            lat=48.8600,
            google_place_id="place_detail_1",
            address="10 Avenue des Champs-Elysees",
            city="Paris",
            country="France",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        result = await get_place_detail(db_session, place_id)
        assert result is not None
        assert result["name"] == "Detail Place"
        assert result["category"] == "restaurant"
        assert result["city"] == "Paris"
        assert result["country"] == "France"
        assert result["busyness_data"] is not None
        assert "popular_times" in result["busyness_data"]
        assert result["busyness_data"]["current_popularity"] == 65
        assert result["busyness_stale"] is False

    async def test_returns_none_for_nonexistent_place(self, db_session: AsyncSession):
        """Should return None for a non-existent place ID."""
        result = await get_place_detail(db_session, 99999)
        assert result is None

    async def test_busyness_null_when_no_data(self, db_session: AsyncSession):
        """Should return busyness fields as null when no data exists."""
        place_id = await _seed_place(
            db_session,
            name="No Data Detail",
            category="park",
            lon=2.3610,
            lat=48.8610,
            google_place_id="place_nodata_detail",
        )
        result = await get_place_detail(db_session, place_id)
        assert result is not None
        assert result["busyness_data"] is None
        assert result["busyness_updated_at"] is None
        assert result["busyness_stale"] is False

    async def test_stale_data_flagged(self, db_session: AsyncSession):
        """Should flag busyness_stale=True when data is older than 7 days."""
        old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)
        place_id = await _seed_place(
            db_session,
            name="Stale Detail Place",
            category="museum",
            lon=2.3620,
            lat=48.8620,
            google_place_id="place_stale_detail",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=old_time,
        )
        result = await get_place_detail(db_session, place_id)
        assert result is not None
        assert result["busyness_stale"] is True
        assert result["busyness_updated_at"] is not None


# ---------------------------------------------------------------------------
# API endpoint tests: GET /places/nearby
# ---------------------------------------------------------------------------


class TestNearbyEndpoint:
    """API tests for GET /places/nearby."""

    async def test_nearby_returns_places(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Authenticated nearby search should return places within radius."""
        await _seed_place(
            db_session,
            name="API Nearby Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="api_nearby_1",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        response = await client.get(
            "/places/nearby",
            params={"lat": 48.8566, "lon": 2.3522, "radius_m": 500},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        place = next((p for p in data if p["name"] == "API Nearby Place"), None)
        assert place is not None
        assert "current_busyness" in place
        assert "busyness_stale" in place
        assert place["current_busyness"] == 65
        assert place["busyness_stale"] is False

    async def test_nearby_category_filter(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Category parameter should filter results."""
        await _seed_place(
            db_session,
            name="API Rest",
            category="restaurant",
            lon=2.3550,
            lat=48.8555,
            google_place_id="api_cat_rest",
        )
        await _seed_place(
            db_session,
            name="API Park",
            category="park",
            lon=2.3551,
            lat=48.8555,
            google_place_id="api_cat_park",
        )
        response = await client.get(
            "/places/nearby",
            params={"lat": 48.8555, "lon": 2.3550, "radius_m": 2000, "category": "restaurant"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for place in data:
            assert place["category"] == "restaurant"

    async def test_nearby_requires_auth(self, client: AsyncClient):
        """Nearby endpoint should require authentication."""
        response = await client.get(
            "/places/nearby",
            params={"lat": 48.8566, "lon": 2.3522, "radius_m": 500},
        )
        assert response.status_code == 401

    async def test_nearby_returns_empty_list_for_no_matches(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Should return empty list when no places are within radius."""
        # Search in the middle of the ocean
        response = await client.get(
            "/places/nearby",
            params={"lat": 0.0, "lon": 0.0, "radius_m": 100},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_nearby_performance(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Nearby search should complete within 2 seconds."""
        # Seed a place to have at least something to query
        await _seed_place(
            db_session,
            name="Perf Test Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="perf_test_1",
        )
        start = time.monotonic()
        response = await client.get(
            "/places/nearby",
            params={"lat": 48.8566, "lon": 2.3522, "radius_m": 500},
            headers=auth_headers,
        )
        elapsed = time.monotonic() - start
        assert response.status_code == 200
        assert elapsed < 2.0, f"Nearby search took {elapsed:.2f}s, exceeding 2s target"


# ---------------------------------------------------------------------------
# API endpoint tests: GET /places/{id}
# ---------------------------------------------------------------------------


class TestPlaceDetailEndpoint:
    """API tests for GET /places/{id}."""

    async def test_returns_full_detail(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Should return full place detail with busyness_data."""
        place_id = await _seed_place(
            db_session,
            name="API Detail Place",
            category="restaurant",
            lon=2.3600,
            lat=48.8600,
            google_place_id="api_detail_1",
            address="5 Rue de la Paix",
            city="Paris",
            country="France",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        response = await client.get(
            f"/places/{place_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == place_id
        assert data["name"] == "API Detail Place"
        assert data["category"] == "restaurant"
        assert data["city"] == "Paris"
        assert data["busyness_data"] is not None
        assert "popular_times" in data["busyness_data"]
        assert data["busyness_data"]["current_popularity"] == 65
        assert data["busyness_stale"] is False

    async def test_returns_404_for_nonexistent(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Should return 404 with consistent error format for non-existent place ID."""
        response = await client.get(
            "/places/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404
        error = response.json()
        assert error["error_type"] == "not_found"
        assert "message" in error
        assert error["status_code"] == 404

    async def test_busyness_null_when_no_data(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Should return busyness fields as null when no busyness data exists."""
        place_id = await _seed_place(
            db_session,
            name="API No Busyness",
            category="park",
            lon=2.3610,
            lat=48.8610,
            google_place_id="api_nobusy_1",
        )
        response = await client.get(
            f"/places/{place_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["busyness_data"] is None
        assert data["busyness_updated_at"] is None
        assert data["busyness_stale"] is False

    async def test_stale_data_flagged(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Should include busyness_stale=true when data > 7 days old."""
        old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)
        place_id = await _seed_place(
            db_session,
            name="API Stale Place",
            category="museum",
            lon=2.3620,
            lat=48.8620,
            google_place_id="api_stale_1",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=old_time,
        )
        response = await client.get(
            f"/places/{place_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["busyness_stale"] is True
        assert data["busyness_updated_at"] is not None

    async def test_requires_auth(self, db_session: AsyncSession, client: AsyncClient):
        """Should require authentication."""
        place_id = await _seed_place(
            db_session,
            name="Auth Required Place",
            category="cafe",
            lon=2.3630,
            lat=48.8630,
            google_place_id="api_auth_req",
        )
        response = await client.get(f"/places/{place_id}")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# API endpoint tests: GET /places/{id}/forecast
# ---------------------------------------------------------------------------


class TestForecastEndpoint:
    """API tests for GET /places/{id}/forecast."""

    async def test_returns_predicted_busyness(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Should return predicted busyness for given day and hour."""
        place_id = await _seed_place(
            db_session,
            name="Forecast Place",
            category="restaurant",
            lon=2.3700,
            lat=48.8700,
            google_place_id="api_forecast_1",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        response = await client.get(
            f"/places/{place_id}/forecast",
            params={"day": 0, "hour": 9},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["place_id"] == place_id
        assert data["day"] == 0
        assert data["hour"] == 9
        assert data["predicted_busyness"] == 80
        assert data["data_stale"] is False

    async def test_returns_404_for_nonexistent_place(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Should return 404 with consistent error format for non-existent place."""
        response = await client.get(
            "/places/99999/forecast",
            params={"day": 0, "hour": 9},
            headers=auth_headers,
        )
        assert response.status_code == 404
        error = response.json()
        assert error["error_type"] == "not_found"
        assert "message" in error
        assert error["status_code"] == 404

    async def test_returns_404_for_no_busyness_data(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Should return 404 with consistent error format when place has no busyness data."""
        place_id = await _seed_place(
            db_session,
            name="No Forecast Data",
            category="park",
            lon=2.3710,
            lat=48.8710,
            google_place_id="api_noforecast_1",
        )
        response = await client.get(
            f"/places/{place_id}/forecast",
            params={"day": 0, "hour": 9},
            headers=auth_headers,
        )
        assert response.status_code == 404
        error = response.json()
        assert error["error_type"] == "not_found"
        assert "message" in error
        assert error["status_code"] == 404

    async def test_stale_data_flagged(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Should flag data_stale=true when busyness data > 7 days old."""
        old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)
        place_id = await _seed_place(
            db_session,
            name="Stale Forecast Place",
            category="bar",
            lon=2.3720,
            lat=48.8720,
            google_place_id="api_stale_forecast",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=old_time,
        )
        response = await client.get(
            f"/places/{place_id}/forecast",
            params={"day": 0, "hour": 9},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data_stale"] is True

    async def test_requires_auth(self, db_session: AsyncSession, client: AsyncClient):
        """Should require authentication."""
        place_id = await _seed_place(
            db_session,
            name="Auth Forecast Place",
            category="cafe",
            lon=2.3730,
            lat=48.8730,
            google_place_id="api_auth_forecast",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        response = await client.get(
            f"/places/{place_id}/forecast",
            params={"day": 0, "hour": 9},
        )
        assert response.status_code == 401

    async def test_validates_day_range(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Should reject invalid day values (outside 0-6)."""
        place_id = await _seed_place(
            db_session,
            name="Day Validation Place",
            category="cafe",
            lon=2.3740,
            lat=48.8740,
            google_place_id="api_day_validation",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        response = await client.get(
            f"/places/{place_id}/forecast",
            params={"day": 8, "hour": 9},
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error

    async def test_validates_hour_range(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict
    ):
        """Should reject invalid hour values (outside 0-23)."""
        place_id = await _seed_place(
            db_session,
            name="Hour Validation Place",
            category="cafe",
            lon=2.3750,
            lat=48.8750,
            google_place_id="api_hour_validation",
            busyness_data=SAMPLE_BUSYNESS_DATA,
            busyness_updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        response = await client.get(
            f"/places/{place_id}/forecast",
            params={"day": 0, "hour": 25},
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error
