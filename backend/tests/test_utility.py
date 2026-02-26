"""Tests for the Utility API router endpoints.

Covers all Step 4 acceptance criteria:
- GET /users/me/stats returns aggregate visit statistics
- GET /users/me/stats returns zero counts for user with no visits
- GET /users/me/achievements returns 6 achievements with progress
- GET /users/me/achievements tracks progress at various levels
- GET /journal returns paginated journal entries
- GET /journal supports limit and offset pagination
- POST /journal/{visit_id}/note creates a journal note
- POST /journal/{visit_id}/note updates an existing note (upsert)
- POST /journal/{visit_id}/note returns 404 for non-existent visit
- GET /explore/heatmap returns areas with visited status
- GET /explore/heatmap filters by city when provided
- GET /passports returns city passport with stamps
- GET /passports returns partial and full completion
- All endpoints require authentication
"""

from __future__ import annotations

import datetime
import json
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

# All tests must share the session-scoped event loop to work with the
# session-scoped async engine fixture (pytest-asyncio 0.25 pattern).
pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# Helper to seed test data
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


async def _seed_area(
    db: AsyncSession,
    *,
    name: str,
    city: str,
    lon: float = 2.35,
    lat: float = 48.85,
    size: float = 0.01,
) -> int:
    """Insert a test area with a square polygon boundary.

    The polygon is a small square around (lon, lat) of the given size in degrees.
    Returns the area ID.
    """
    # Create a square polygon around the center point
    min_lon = lon - size / 2
    max_lon = lon + size / 2
    min_lat = lat - size / 2
    max_lat = lat + size / 2

    wkt = (
        f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, "
        f"{max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
    )

    result = await db.execute(
        text(
            "INSERT INTO areas (name, city, boundary) "
            "VALUES (:name, :city, "
            "CAST(ST_SetSRID(ST_GeomFromText(:wkt), 4326) AS geography)) "
            "RETURNING id"
        ),
        {
            "name": name,
            "city": city,
            "wkt": wkt,
        },
    )
    area_id = result.scalar_one()
    await db.flush()
    return area_id


async def _seed_visit(
    db: AsyncSession,
    *,
    user_id: int,
    place_id: int,
    area_id: int | None = None,
    started_at: datetime.datetime | None = None,
    ended_at: datetime.datetime | None = None,
    duration_seconds: int | None = 600,
) -> int:
    """Insert a test visit record.

    Returns the visit ID.
    """
    if started_at is None:
        started_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    if ended_at is None:
        ended_at = started_at + datetime.timedelta(seconds=duration_seconds or 600)

    result = await db.execute(
        text(
            "INSERT INTO visits (user_id, place_id, area_id, started_at, ended_at, duration_seconds) "
            "VALUES (:uid, :pid, :aid, :start, :end, :dur) "
            "RETURNING id"
        ),
        {
            "uid": user_id,
            "pid": place_id,
            "aid": area_id,
            "start": started_at,
            "end": ended_at,
            "dur": duration_seconds,
        },
    )
    visit_id = result.scalar_one()
    await db.flush()
    return visit_id


async def _seed_journal_note(
    db: AsyncSession,
    *,
    visit_id: int,
    user_id: int,
    note_text: str | None = None,
    photo_url: str | None = None,
) -> int:
    """Insert a test journal note.

    Returns the journal note ID.
    """
    result = await db.execute(
        text(
            "INSERT INTO journal_notes (visit_id, user_id, text, photo_url) "
            "VALUES (:vid, :uid, :txt, :purl) "
            "RETURNING id"
        ),
        {
            "vid": visit_id,
            "uid": user_id,
            "txt": note_text,
            "purl": photo_url,
        },
    )
    note_id = result.scalar_one()
    await db.flush()
    return note_id


# ---------------------------------------------------------------------------
# GET /users/me/stats
# ---------------------------------------------------------------------------


class TestUserStatsEndpoint:
    """API tests for GET /users/me/stats."""

    async def test_stats_with_no_visits(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return zero counts when user has no visits."""
        response = await client.get("/users/me/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["places_count"] == 0
        assert data["cities_count"] == 0
        assert data["countries_count"] == 0
        assert data["total_duration_seconds"] == 0

    async def test_stats_with_multiple_visits(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return correct aggregate counts with multiple visits."""
        # Seed places in different cities/countries
        place1_id = await _seed_place(
            db_session,
            name="Stats Restaurant Paris",
            category="restaurant",
            lon=2.35,
            lat=48.85,
            google_place_id="stats_p1",
            city="Paris",
            country="France",
        )
        place2_id = await _seed_place(
            db_session,
            name="Stats Cafe Lyon",
            category="cafe",
            lon=4.83,
            lat=45.76,
            google_place_id="stats_p2",
            city="Lyon",
            country="France",
        )
        place3_id = await _seed_place(
            db_session,
            name="Stats Pub London",
            category="bar",
            lon=-0.13,
            lat=51.51,
            google_place_id="stats_p3",
            city="London",
            country="UK",
        )

        # Seed visits
        await _seed_visit(db_session, user_id=test_user.id, place_id=place1_id, duration_seconds=300)
        await _seed_visit(db_session, user_id=test_user.id, place_id=place2_id, duration_seconds=600)
        await _seed_visit(db_session, user_id=test_user.id, place_id=place3_id, duration_seconds=900)

        response = await client.get("/users/me/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["places_count"] == 3
        assert data["cities_count"] == 3
        assert data["countries_count"] == 2  # France + UK
        assert data["total_duration_seconds"] == 1800  # 300 + 600 + 900

    async def test_stats_requires_auth(self, client: AsyncClient):
        """Should require authentication."""
        response = await client.get("/users/me/stats")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/me/achievements
# ---------------------------------------------------------------------------


class TestUserAchievementsEndpoint:
    """API tests for GET /users/me/achievements."""

    async def test_achievements_with_no_visits(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return 6 achievements all with progress 0 and earned False."""
        response = await client.get("/users/me/achievements", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 6

        # All should have progress 0 and not earned
        for ach in data:
            assert ach["progress"] == 0
            assert ach["earned"] is False
            assert ach["earned_at"] is None

        # Verify all 6 achievements are present
        ids = {a["id"] for a in data}
        expected_ids = {"wanderer", "globe_trotter", "night_owl", "early_bird", "foodie", "culture_vulture"}
        assert ids == expected_ids

    async def test_achievements_with_partial_progress(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should show progress toward achievements without earning them."""
        # Create 3 restaurants for foodie progress (threshold: 50)
        for i in range(3):
            place_id = await _seed_place(
                db_session,
                name=f"Ach Restaurant {i}",
                category="restaurant",
                lon=2.35 + i * 0.001,
                lat=48.85,
                google_place_id=f"ach_rest_{i}",
                city="Paris",
                country="France",
            )
            await _seed_visit(db_session, user_id=test_user.id, place_id=place_id)

        response = await client.get("/users/me/achievements", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Check foodie progress
        foodie = next(a for a in data if a["id"] == "foodie")
        assert foodie["progress"] == 3
        assert foodie["threshold"] == 50
        assert foodie["earned"] is False

        # Check globe_trotter progress (1 city: Paris)
        globe = next(a for a in data if a["id"] == "globe_trotter")
        assert globe["progress"] == 1
        assert globe["threshold"] == 5
        assert globe["earned"] is False

    async def test_achievements_with_earned_achievement(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should mark achievement as earned when threshold is met."""
        # Create visits in 5 different cities to earn Globe Trotter
        cities = ["Paris", "Lyon", "Marseille", "Nice", "Bordeaux"]
        for i, city_name in enumerate(cities):
            place_id = await _seed_place(
                db_session,
                name=f"Ach Place {city_name}",
                category="cafe",
                lon=2.35 + i * 0.1,
                lat=48.85 + i * 0.1,
                google_place_id=f"ach_globe_{i}",
                city=city_name,
                country="France",
            )
            await _seed_visit(db_session, user_id=test_user.id, place_id=place_id)

        response = await client.get("/users/me/achievements", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        globe = next(a for a in data if a["id"] == "globe_trotter")
        assert globe["progress"] >= 5
        assert globe["earned"] is True
        assert globe["earned_at"] is not None

    async def test_achievements_early_bird(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should track early bird achievement for visits before 7am."""
        place_id = await _seed_place(
            db_session,
            name="Early Place",
            category="cafe",
            lon=2.36,
            lat=48.86,
            google_place_id="ach_early_1",
            city="Paris",
            country="France",
        )
        # Visit at 5am
        early_time = datetime.datetime(2024, 6, 15, 5, 0, 0, tzinfo=datetime.timezone.utc)
        await _seed_visit(
            db_session,
            user_id=test_user.id,
            place_id=place_id,
            started_at=early_time,
        )

        response = await client.get("/users/me/achievements", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        early_bird = next(a for a in data if a["id"] == "early_bird")
        assert early_bird["progress"] >= 1

    async def test_achievements_night_owl(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should track night owl achievement for visits after midnight."""
        place_id = await _seed_place(
            db_session,
            name="Night Place",
            category="bar",
            lon=2.37,
            lat=48.87,
            google_place_id="ach_night_1",
            city="Paris",
            country="France",
        )
        # Visit at 2am
        night_time = datetime.datetime(2024, 6, 15, 2, 0, 0, tzinfo=datetime.timezone.utc)
        await _seed_visit(
            db_session,
            user_id=test_user.id,
            place_id=place_id,
            started_at=night_time,
        )

        response = await client.get("/users/me/achievements", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        night_owl = next(a for a in data if a["id"] == "night_owl")
        assert night_owl["progress"] >= 1

    async def test_achievements_requires_auth(self, client: AsyncClient):
        """Should require authentication."""
        response = await client.get("/users/me/achievements")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /journal
# ---------------------------------------------------------------------------


class TestJournalEndpoint:
    """API tests for GET /journal."""

    async def test_journal_empty(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return empty list when user has no visits."""
        response = await client.get("/journal", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_journal_returns_entries(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return journal entries with visit and place data."""
        place_id = await _seed_place(
            db_session,
            name="Journal Place",
            category="restaurant",
            lon=2.35,
            lat=48.85,
            google_place_id="journal_p1",
            city="Paris",
            country="France",
        )
        visit_id = await _seed_visit(
            db_session,
            user_id=test_user.id,
            place_id=place_id,
            duration_seconds=600,
        )

        response = await client.get("/journal", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        entry = next((e for e in data if e["visit_id"] == visit_id), None)
        assert entry is not None
        assert entry["place_id"] == place_id
        assert entry["place_name"] == "Journal Place"
        assert entry["city"] == "Paris"
        assert entry["duration_seconds"] == 600
        assert entry["note"] is None
        assert entry["photo_url"] is None

    async def test_journal_includes_notes(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should include journal notes when they exist."""
        place_id = await _seed_place(
            db_session,
            name="Noted Place",
            category="cafe",
            lon=2.36,
            lat=48.86,
            google_place_id="journal_noted_p1",
            city="Paris",
            country="France",
        )
        visit_id = await _seed_visit(
            db_session,
            user_id=test_user.id,
            place_id=place_id,
        )
        await _seed_journal_note(
            db_session,
            visit_id=visit_id,
            user_id=test_user.id,
            note_text="Great food!",
            photo_url="file:///photos/123.jpg",
        )

        response = await client.get("/journal", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        entry = next((e for e in data if e["visit_id"] == visit_id), None)
        assert entry is not None
        assert entry["note"] == "Great food!"
        assert entry["photo_url"] == "file:///photos/123.jpg"

    async def test_journal_pagination_limit(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should respect limit parameter for pagination."""
        place_id = await _seed_place(
            db_session,
            name="Paginated Place",
            category="cafe",
            lon=2.37,
            lat=48.87,
            google_place_id="journal_pag_p1",
            city="Paris",
            country="France",
        )
        # Create 5 visits
        for i in range(5):
            start = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=i + 1)
            await _seed_visit(
                db_session,
                user_id=test_user.id,
                place_id=place_id,
                started_at=start,
                duration_seconds=300,
            )

        response = await client.get("/journal", params={"limit": 3}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    async def test_journal_pagination_offset(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should respect offset parameter for pagination."""
        place_id = await _seed_place(
            db_session,
            name="Offset Place",
            category="cafe",
            lon=2.38,
            lat=48.88,
            google_place_id="journal_off_p1",
            city="Paris",
            country="France",
        )
        # Create 3 visits with distinct times
        visit_ids = []
        for i in range(3):
            start = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=i + 1)
            vid = await _seed_visit(
                db_session,
                user_id=test_user.id,
                place_id=place_id,
                started_at=start,
                duration_seconds=300,
            )
            visit_ids.append(vid)

        # Get all entries
        all_response = await client.get("/journal", params={"limit": 100}, headers=auth_headers)
        all_data = all_response.json()

        # Get entries with offset=2
        offset_response = await client.get(
            "/journal", params={"limit": 100, "offset": 2}, headers=auth_headers
        )
        offset_data = offset_response.json()

        # offset results should be a subset, skipping the first 2
        assert len(offset_data) <= len(all_data) - 2

    async def test_journal_requires_auth(self, client: AsyncClient):
        """Should require authentication."""
        response = await client.get("/journal")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /journal/{visit_id}/note
# ---------------------------------------------------------------------------


class TestJournalNoteEndpoint:
    """API tests for POST /journal/{visit_id}/note."""

    async def test_create_note(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should create a journal note for a visit."""
        place_id = await _seed_place(
            db_session,
            name="Note Create Place",
            category="restaurant",
            lon=2.35,
            lat=48.85,
            google_place_id="note_create_p1",
            city="Paris",
            country="France",
        )
        visit_id = await _seed_visit(
            db_session,
            user_id=test_user.id,
            place_id=place_id,
        )

        response = await client.post(
            f"/journal/{visit_id}/note",
            json={"text": "Amazing experience!", "photo_url": "file:///photos/abc.jpg"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["visit_id"] == visit_id
        assert data["place_name"] == "Note Create Place"
        assert data["note"] == "Amazing experience!"
        assert data["photo_url"] == "file:///photos/abc.jpg"

    async def test_update_existing_note(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should update an existing journal note (upsert)."""
        place_id = await _seed_place(
            db_session,
            name="Note Update Place",
            category="cafe",
            lon=2.36,
            lat=48.86,
            google_place_id="note_update_p1",
            city="Paris",
            country="France",
        )
        visit_id = await _seed_visit(
            db_session,
            user_id=test_user.id,
            place_id=place_id,
        )
        # Create initial note
        await _seed_journal_note(
            db_session,
            visit_id=visit_id,
            user_id=test_user.id,
            note_text="First draft",
        )

        # Update it
        response = await client.post(
            f"/journal/{visit_id}/note",
            json={"text": "Updated note"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["note"] == "Updated note"

    async def test_create_note_with_text_only(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should create a note with text only (no photo)."""
        place_id = await _seed_place(
            db_session,
            name="Text Only Place",
            category="restaurant",
            lon=2.37,
            lat=48.87,
            google_place_id="note_text_p1",
            city="Paris",
            country="France",
        )
        visit_id = await _seed_visit(
            db_session,
            user_id=test_user.id,
            place_id=place_id,
        )

        response = await client.post(
            f"/journal/{visit_id}/note",
            json={"text": "Just text"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["note"] == "Just text"
        assert data["photo_url"] is None

    async def test_create_note_nonexistent_visit(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return 404 for a non-existent visit ID."""
        response = await client.post(
            "/journal/99999/note",
            json={"text": "Won't work"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        error = response.json()
        assert error["error_type"] == "not_found"
        assert "message" in error
        assert error["status_code"] == 404

    async def test_create_note_requires_auth(self, client: AsyncClient):
        """Should require authentication."""
        response = await client.post(
            "/journal/1/note",
            json={"text": "No auth"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /explore/heatmap
# ---------------------------------------------------------------------------


class TestHeatmapEndpoint:
    """API tests for GET /explore/heatmap."""

    async def test_heatmap_empty(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return empty heatmap when no areas exist."""
        response = await client.get("/explore/heatmap", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_areas"] >= 0
        assert data["explored_pct"] >= 0.0
        assert isinstance(data["areas"], list)

    async def test_heatmap_with_visited_areas(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should show areas with visited status based on user visits."""
        # Create areas
        area1_id = await _seed_area(
            db_session, name="Heatmap District A", city="Paris", lon=2.35, lat=48.85
        )
        area2_id = await _seed_area(
            db_session, name="Heatmap District B", city="Paris", lon=2.37, lat=48.87
        )

        # Create a place and visit in area1 only
        place_id = await _seed_place(
            db_session,
            name="Heatmap Place",
            category="cafe",
            lon=2.35,
            lat=48.85,
            google_place_id="heatmap_p1",
            city="Paris",
            country="France",
        )
        await _seed_visit(
            db_session,
            user_id=test_user.id,
            place_id=place_id,
            area_id=area1_id,
        )

        response = await client.get(
            "/explore/heatmap", params={"city": "Paris"}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["total_areas"] >= 2
        assert data["visited_areas"] >= 1

        # Verify visited status
        area_a = next((a for a in data["areas"] if a["id"] == area1_id), None)
        assert area_a is not None
        assert area_a["visited"] is True
        assert area_a["visited_at"] is not None
        assert area_a["boundary_geojson"] is not None

        area_b = next((a for a in data["areas"] if a["id"] == area2_id), None)
        assert area_b is not None
        assert area_b["visited"] is False
        assert area_b["visited_at"] is None

    async def test_heatmap_without_city_filter(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return all areas when no city filter is provided."""
        # Create areas in different cities
        await _seed_area(
            db_session, name="Heatmap No-Filter A", city="Paris", lon=2.40, lat=48.90
        )
        await _seed_area(
            db_session, name="Heatmap No-Filter B", city="Lyon", lon=4.83, lat=45.76
        )

        response = await client.get("/explore/heatmap", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Should return areas from multiple cities
        cities = {a["city"] for a in data["areas"]}
        assert len(cities) >= 2

    async def test_heatmap_with_city_filter(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return only areas from the specified city."""
        await _seed_area(
            db_session, name="Heatmap Filter Paris", city="Paris", lon=2.41, lat=48.91
        )
        await _seed_area(
            db_session, name="Heatmap Filter Lyon", city="Lyon", lon=4.84, lat=45.77
        )

        response = await client.get(
            "/explore/heatmap", params={"city": "Lyon"}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        # All returned areas should be in Lyon
        for area in data["areas"]:
            assert area["city"] == "Lyon"

    async def test_heatmap_explored_percentage(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should calculate correct exploration percentage."""
        # Create 4 areas in a city
        area_ids = []
        for i in range(4):
            aid = await _seed_area(
                db_session,
                name=f"Pct District {i}",
                city="Marseille",
                lon=5.37 + i * 0.02,
                lat=43.30 + i * 0.02,
            )
            area_ids.append(aid)

        # Visit 2 of 4 areas
        for i in range(2):
            place_id = await _seed_place(
                db_session,
                name=f"Pct Place {i}",
                category="cafe",
                lon=5.37 + i * 0.02,
                lat=43.30 + i * 0.02,
                google_place_id=f"pct_place_{i}",
                city="Marseille",
                country="France",
            )
            await _seed_visit(
                db_session,
                user_id=test_user.id,
                place_id=place_id,
                area_id=area_ids[i],
            )

        response = await client.get(
            "/explore/heatmap", params={"city": "Marseille"}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["total_areas"] == 4
        assert data["visited_areas"] == 2
        assert abs(data["explored_pct"] - 50.0) < 0.01

    async def test_heatmap_requires_auth(self, client: AsyncClient):
        """Should require authentication."""
        response = await client.get("/explore/heatmap")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /passports
# ---------------------------------------------------------------------------


class TestPassportEndpoint:
    """API tests for GET /passports."""

    async def test_passport_empty_city(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return passport with no stamps for a city with no areas."""
        response = await client.get(
            "/passports", params={"city": "EmptyCity"}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "EmptyCity"
        assert data["total_neighborhoods"] == 0
        assert data["visited_count"] == 0
        assert data["stamps"] == []
        assert data["badge_earned"] is False
        assert data["explored_pct"] == 0.0

    async def test_passport_partial_completion(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should show partial completion with some stamps earned."""
        # Create 3 areas in Toulouse
        area_ids = []
        for i in range(3):
            aid = await _seed_area(
                db_session,
                name=f"Toulouse District {i}",
                city="Toulouse",
                lon=1.44 + i * 0.02,
                lat=43.60 + i * 0.02,
            )
            area_ids.append(aid)

        # Visit only 1 of 3 areas
        place_id = await _seed_place(
            db_session,
            name="Passport Place Toulouse",
            category="cafe",
            lon=1.44,
            lat=43.60,
            google_place_id="passport_partial_p1",
            city="Toulouse",
            country="France",
        )
        await _seed_visit(
            db_session,
            user_id=test_user.id,
            place_id=place_id,
            area_id=area_ids[0],
        )

        response = await client.get(
            "/passports", params={"city": "Toulouse"}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["city"] == "Toulouse"
        assert data["total_neighborhoods"] == 3
        assert data["visited_count"] == 1
        assert data["badge_earned"] is False
        assert abs(data["explored_pct"] - (1 / 3 * 100.0)) < 0.1

        # Verify stamps
        assert len(data["stamps"]) == 3
        visited_stamps = [s for s in data["stamps"] if s["visited"]]
        unvisited_stamps = [s for s in data["stamps"] if not s["visited"]]
        assert len(visited_stamps) == 1
        assert len(unvisited_stamps) == 2
        assert visited_stamps[0]["area_id"] == area_ids[0]
        assert visited_stamps[0]["visited_at"] is not None

    async def test_passport_full_completion(
        self, db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should show full completion with badge earned when all areas visited."""
        # Create 2 areas in Nantes
        area_ids = []
        for i in range(2):
            aid = await _seed_area(
                db_session,
                name=f"Nantes District {i}",
                city="Nantes",
                lon=-1.55 + i * 0.02,
                lat=47.22 + i * 0.02,
            )
            area_ids.append(aid)

        # Visit all areas
        for i in range(2):
            place_id = await _seed_place(
                db_session,
                name=f"Passport Full Place {i}",
                category="cafe",
                lon=-1.55 + i * 0.02,
                lat=47.22 + i * 0.02,
                google_place_id=f"passport_full_p{i}",
                city="Nantes",
                country="France",
            )
            await _seed_visit(
                db_session,
                user_id=test_user.id,
                place_id=place_id,
                area_id=area_ids[i],
            )

        response = await client.get(
            "/passports", params={"city": "Nantes"}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["city"] == "Nantes"
        assert data["total_neighborhoods"] == 2
        assert data["visited_count"] == 2
        assert data["badge_earned"] is True
        assert abs(data["explored_pct"] - 100.0) < 0.01

        # All stamps should be visited
        for stamp in data["stamps"]:
            assert stamp["visited"] is True
            assert stamp["visited_at"] is not None

    async def test_passport_requires_city_param(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Should return 422 when city parameter is missing."""
        response = await client.get("/passports", headers=auth_headers)
        assert response.status_code == 422

    async def test_passport_requires_auth(self, client: AsyncClient):
        """Should require authentication."""
        response = await client.get("/passports", params={"city": "Paris"})
        assert response.status_code == 401
