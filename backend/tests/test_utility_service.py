"""Tests for the utility service functions.

Covers all Step 3 success criteria:
- get_user_stats returns places_count, cities_count, countries_count, total_duration_seconds
- get_user_achievements returns 6 achievements with correct criteria
- get_journal_entries returns paginated journal entries with Visit JOIN Place LEFT JOIN JournalNote
- add_journal_note upserts a JournalNote record
- get_heatmap returns areas with visited flag, boundary GeoJSON, exploration percentage
- get_city_passport returns neighborhood stamps, visited count, badge earned
"""

from __future__ import annotations

import datetime
import json
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password

# All tests must share the session-scoped event loop to work with the
# session-scoped async engine fixture (pytest-asyncio 0.25 pattern).
pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# Helper fixtures and utilities
# ---------------------------------------------------------------------------


def _jsonb_or_none(data: dict | None) -> str | None:
    """Serialize dict to JSON string for JSONB insertion, or None."""
    if data is None:
        return None
    return json.dumps(data)


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
    """Insert a test place using raw SQL with ST_MakePoint for Geography."""
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


async def _seed_area(
    db: AsyncSession,
    *,
    name: str,
    city: str,
    zone_type: str = "neighborhood",
    # WKT polygon: a small square around (lon, lat)
    center_lon: float,
    center_lat: float,
    size: float = 0.01,  # degree offset for the polygon corners
) -> int:
    """Insert a test area using raw SQL with a small polygon boundary."""
    # Create a square polygon around the center
    min_lon = center_lon - size
    max_lon = center_lon + size
    min_lat = center_lat - size
    max_lat = center_lat + size
    wkt = (
        f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, "
        f"{max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
    )
    result = await db.execute(
        text(
            "INSERT INTO areas (name, city, boundary, zone_type) "
            "VALUES (:name, :city, "
            "CAST(ST_SetSRID(ST_GeomFromText(:wkt), 4326) AS geography), "
            ":zone_type) "
            "RETURNING id"
        ),
        {
            "name": name,
            "city": city,
            "wkt": wkt,
            "zone_type": zone_type,
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
    duration_seconds: int = 600,
) -> int:
    """Insert a test visit."""
    if started_at is None:
        started_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    if ended_at is None:
        ended_at = started_at + datetime.timedelta(seconds=duration_seconds)
    result = await db.execute(
        text(
            "INSERT INTO visits (user_id, place_id, area_id, started_at, ended_at, duration_seconds) "
            "VALUES (:uid, :pid, :aid, :sa, :ea, :ds) "
            "RETURNING id"
        ),
        {
            "uid": user_id,
            "pid": place_id,
            "aid": area_id,
            "sa": started_at,
            "ea": ended_at,
            "ds": duration_seconds,
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
    """Insert a test journal note."""
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


async def _create_test_user(db: AsyncSession, *, username: str = "svcuser", email: str = "svc@example.com") -> User:
    """Create a test user for service tests."""
    user = User(
        username=username,
        email=email,
        password_hash=hash_password("testpassword123"),
    )
    db.add(user)
    await db.flush()
    return user


# ---------------------------------------------------------------------------
# Tests: get_user_stats
# ---------------------------------------------------------------------------


class TestGetUserStats:
    """Tests for get_user_stats service function."""

    async def test_returns_zero_stats_with_no_visits(self, db_session: AsyncSession):
        """Should return zero counts when user has no visits."""
        from app.services.utility_service import get_user_stats

        user = await _create_test_user(db_session, username="stats_empty", email="stats_empty@test.com")
        result = await get_user_stats(db_session, user.id)

        assert result["places_count"] == 0
        assert result["cities_count"] == 0
        assert result["countries_count"] == 0
        assert result["total_duration_seconds"] == 0

    async def test_counts_distinct_places_cities_countries(self, db_session: AsyncSession):
        """Should count distinct places, cities, and countries from visits."""
        from app.services.utility_service import get_user_stats

        user = await _create_test_user(db_session, username="stats_multi", email="stats_multi@test.com")

        # Create places in different cities/countries
        p1 = await _seed_place(
            db_session, name="Place Lyon 1", category="cafe", lon=4.8357, lat=45.7640,
            google_place_id="stats_p1", city="Lyon", country="France",
        )
        p2 = await _seed_place(
            db_session, name="Place Lyon 2", category="restaurant", lon=4.8360, lat=45.7645,
            google_place_id="stats_p2", city="Lyon", country="France",
        )
        p3 = await _seed_place(
            db_session, name="Place Paris", category="museum", lon=2.3522, lat=48.8566,
            google_place_id="stats_p3", city="Paris", country="France",
        )
        p4 = await _seed_place(
            db_session, name="Place London", category="park", lon=-0.1278, lat=51.5074,
            google_place_id="stats_p4", city="London", country="UK",
        )

        # Create visits (visit the same place twice to test distinct counting)
        await _seed_visit(db_session, user_id=user.id, place_id=p1, duration_seconds=300)
        await _seed_visit(db_session, user_id=user.id, place_id=p1, duration_seconds=200)
        await _seed_visit(db_session, user_id=user.id, place_id=p2, duration_seconds=400)
        await _seed_visit(db_session, user_id=user.id, place_id=p3, duration_seconds=500)
        await _seed_visit(db_session, user_id=user.id, place_id=p4, duration_seconds=600)

        result = await get_user_stats(db_session, user.id)

        assert result["places_count"] == 4  # 4 distinct places
        assert result["cities_count"] == 3  # Lyon, Paris, London
        assert result["countries_count"] == 2  # France, UK
        assert result["total_duration_seconds"] == 2000  # 300+200+400+500+600

    async def test_handles_null_city_and_country(self, db_session: AsyncSession):
        """Should handle places with null city/country gracefully."""
        from app.services.utility_service import get_user_stats

        user = await _create_test_user(db_session, username="stats_null", email="stats_null@test.com")
        p = await _seed_place(
            db_session, name="No City Place", category="cafe", lon=2.0, lat=48.0,
            google_place_id="stats_null_p1",
        )
        await _seed_visit(db_session, user_id=user.id, place_id=p, duration_seconds=100)

        result = await get_user_stats(db_session, user.id)

        assert result["places_count"] == 1
        assert result["cities_count"] == 0  # null cities not counted
        assert result["countries_count"] == 0  # null countries not counted
        assert result["total_duration_seconds"] == 100


# ---------------------------------------------------------------------------
# Tests: get_user_achievements
# ---------------------------------------------------------------------------


class TestGetUserAchievements:
    """Tests for get_user_achievements service function."""

    async def test_returns_six_achievements(self, db_session: AsyncSession):
        """Should always return exactly 6 achievements."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_six", email="ach_six@test.com")
        result = await get_user_achievements(db_session, user.id)

        assert len(result) == 6
        ids = {a["id"] for a in result}
        assert ids == {"wanderer", "globe_trotter", "night_owl", "early_bird", "foodie", "culture_vulture"}

    async def test_all_zero_progress_with_no_visits(self, db_session: AsyncSession):
        """Should return 0 progress for all achievements with no visits."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_zero", email="ach_zero@test.com")
        result = await get_user_achievements(db_session, user.id)

        for ach in result:
            assert ach["progress"] == 0
            assert ach["earned"] is False
            assert ach["earned_at"] is None

    async def test_wanderer_counts_distinct_areas(self, db_session: AsyncSession):
        """Wanderer: progress = distinct area_ids visited."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_wand", email="ach_wand@test.com")

        # Create 3 areas and places in them
        area1 = await _seed_area(db_session, name="Area1", city="Lyon", center_lon=4.83, center_lat=45.76)
        area2 = await _seed_area(db_session, name="Area2", city="Lyon", center_lon=4.84, center_lat=45.77)
        area3 = await _seed_area(db_session, name="Area3", city="Lyon", center_lon=4.85, center_lat=45.78)

        p1 = await _seed_place(db_session, name="WP1", category="cafe", lon=4.83, lat=45.76, google_place_id="ach_w_p1")
        p2 = await _seed_place(db_session, name="WP2", category="cafe", lon=4.84, lat=45.77, google_place_id="ach_w_p2")
        p3 = await _seed_place(db_session, name="WP3", category="cafe", lon=4.85, lat=45.78, google_place_id="ach_w_p3")

        await _seed_visit(db_session, user_id=user.id, place_id=p1, area_id=area1)
        await _seed_visit(db_session, user_id=user.id, place_id=p2, area_id=area2)
        await _seed_visit(db_session, user_id=user.id, place_id=p3, area_id=area3)
        # Duplicate area visit should not increase progress
        await _seed_visit(db_session, user_id=user.id, place_id=p1, area_id=area1)

        result = await get_user_achievements(db_session, user.id)
        wanderer = next(a for a in result if a["id"] == "wanderer")

        assert wanderer["progress"] == 3
        assert wanderer["threshold"] == 10
        assert wanderer["earned"] is False

    async def test_globe_trotter_counts_distinct_cities(self, db_session: AsyncSession):
        """Globe Trotter: progress = distinct cities visited."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_globe", email="ach_globe@test.com")

        p1 = await _seed_place(db_session, name="GP1", category="cafe", lon=4.83, lat=45.76, google_place_id="ach_g_p1", city="Lyon")
        p2 = await _seed_place(db_session, name="GP2", category="cafe", lon=2.35, lat=48.86, google_place_id="ach_g_p2", city="Paris")
        p3 = await _seed_place(db_session, name="GP3", category="cafe", lon=-0.12, lat=51.50, google_place_id="ach_g_p3", city="London")

        await _seed_visit(db_session, user_id=user.id, place_id=p1)
        await _seed_visit(db_session, user_id=user.id, place_id=p2)
        await _seed_visit(db_session, user_id=user.id, place_id=p3)

        result = await get_user_achievements(db_session, user.id)
        globe = next(a for a in result if a["id"] == "globe_trotter")

        assert globe["progress"] == 3
        assert globe["threshold"] == 5

    async def test_night_owl_counts_visits_after_midnight(self, db_session: AsyncSession):
        """Night Owl: progress = visits where started_at hour is 0-3 (after midnight)."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_night", email="ach_night@test.com")

        p = await _seed_place(db_session, name="NP", category="bar", lon=4.83, lat=45.76, google_place_id="ach_n_p1")

        # Visit at 1 AM (should count)
        await _seed_visit(
            db_session, user_id=user.id, place_id=p,
            started_at=datetime.datetime(2025, 6, 15, 1, 0, tzinfo=datetime.timezone.utc),
        )
        # Visit at 3 AM (should count)
        await _seed_visit(
            db_session, user_id=user.id, place_id=p,
            started_at=datetime.datetime(2025, 6, 16, 3, 30, tzinfo=datetime.timezone.utc),
        )
        # Visit at 8 AM (should NOT count)
        await _seed_visit(
            db_session, user_id=user.id, place_id=p,
            started_at=datetime.datetime(2025, 6, 17, 8, 0, tzinfo=datetime.timezone.utc),
        )

        result = await get_user_achievements(db_session, user.id)
        night_owl = next(a for a in result if a["id"] == "night_owl")

        assert night_owl["progress"] == 2
        assert night_owl["threshold"] == 10

    async def test_early_bird_counts_visits_before_7am(self, db_session: AsyncSession):
        """Early Bird: progress = visits where started_at hour < 7."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_early", email="ach_early@test.com")

        p = await _seed_place(db_session, name="EP", category="cafe", lon=4.83, lat=45.76, google_place_id="ach_e_p1")

        # Visit at 5 AM (should count)
        await _seed_visit(
            db_session, user_id=user.id, place_id=p,
            started_at=datetime.datetime(2025, 6, 15, 5, 0, tzinfo=datetime.timezone.utc),
        )
        # Visit at 6:59 AM (should count)
        await _seed_visit(
            db_session, user_id=user.id, place_id=p,
            started_at=datetime.datetime(2025, 6, 16, 6, 59, tzinfo=datetime.timezone.utc),
        )
        # Visit at 7:00 AM (should NOT count)
        await _seed_visit(
            db_session, user_id=user.id, place_id=p,
            started_at=datetime.datetime(2025, 6, 17, 7, 0, tzinfo=datetime.timezone.utc),
        )

        result = await get_user_achievements(db_session, user.id)
        early_bird = next(a for a in result if a["id"] == "early_bird")

        assert early_bird["progress"] == 2
        assert early_bird["threshold"] == 10

    async def test_foodie_counts_restaurant_visits(self, db_session: AsyncSession):
        """Foodie: progress = total visits to restaurant places."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_food", email="ach_food@test.com")

        rest = await _seed_place(db_session, name="FP Rest", category="restaurant", lon=4.83, lat=45.76, google_place_id="ach_f_p1")
        cafe = await _seed_place(db_session, name="FP Cafe", category="cafe", lon=4.84, lat=45.77, google_place_id="ach_f_p2")

        # 3 restaurant visits + 1 cafe visit
        await _seed_visit(db_session, user_id=user.id, place_id=rest)
        await _seed_visit(db_session, user_id=user.id, place_id=rest)
        await _seed_visit(db_session, user_id=user.id, place_id=rest)
        await _seed_visit(db_session, user_id=user.id, place_id=cafe)

        result = await get_user_achievements(db_session, user.id)
        foodie = next(a for a in result if a["id"] == "foodie")

        assert foodie["progress"] == 3
        assert foodie["threshold"] == 50

    async def test_culture_vulture_counts_museum_visits(self, db_session: AsyncSession):
        """Culture Vulture: progress = total visits to museum places."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_cult", email="ach_cult@test.com")

        museum = await _seed_place(db_session, name="CV Museum", category="museum", lon=4.83, lat=45.76, google_place_id="ach_c_p1")
        park = await _seed_place(db_session, name="CV Park", category="park", lon=4.84, lat=45.77, google_place_id="ach_c_p2")

        await _seed_visit(db_session, user_id=user.id, place_id=museum)
        await _seed_visit(db_session, user_id=user.id, place_id=museum)
        await _seed_visit(db_session, user_id=user.id, place_id=park)

        result = await get_user_achievements(db_session, user.id)
        culture = next(a for a in result if a["id"] == "culture_vulture")

        assert culture["progress"] == 2
        assert culture["threshold"] == 20

    async def test_achievement_earned_when_threshold_met(self, db_session: AsyncSession):
        """Achievement should be marked as earned when progress >= threshold."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_earned", email="ach_earned@test.com")

        # Create 5 cities for Globe Trotter (threshold=5)
        cities = ["CityA", "CityB", "CityC", "CityD", "CityE"]
        for i, city_name in enumerate(cities):
            p = await _seed_place(
                db_session, name=f"Earn Place {i}", category="cafe",
                lon=4.83 + i * 0.01, lat=45.76 + i * 0.01,
                google_place_id=f"ach_earn_p{i}", city=city_name,
            )
            await _seed_visit(db_session, user_id=user.id, place_id=p)

        result = await get_user_achievements(db_session, user.id)
        globe = next(a for a in result if a["id"] == "globe_trotter")

        assert globe["progress"] == 5
        assert globe["earned"] is True
        assert globe["earned_at"] is not None

    async def test_achievement_categories_are_correct(self, db_session: AsyncSession):
        """Each achievement should have the correct category."""
        from app.services.utility_service import get_user_achievements

        user = await _create_test_user(db_session, username="ach_cat", email="ach_cat@test.com")
        result = await get_user_achievements(db_session, user.id)

        expected_categories = {
            "wanderer": "explorer",
            "globe_trotter": "explorer",
            "night_owl": "habits",
            "early_bird": "habits",
            "foodie": "categories",
            "culture_vulture": "categories",
        }
        for ach in result:
            assert ach["category"] == expected_categories[ach["id"]], (
                f"Achievement {ach['id']} should have category '{expected_categories[ach['id']]}', "
                f"got '{ach['category']}'"
            )


# ---------------------------------------------------------------------------
# Tests: get_journal_entries
# ---------------------------------------------------------------------------


class TestGetJournalEntries:
    """Tests for get_journal_entries service function."""

    async def test_returns_empty_list_with_no_visits(self, db_session: AsyncSession):
        """Should return empty list when user has no visits."""
        from app.services.utility_service import get_journal_entries

        user = await _create_test_user(db_session, username="jrn_empty", email="jrn_empty@test.com")
        result = await get_journal_entries(db_session, user.id, limit=20, offset=0)

        assert result == []

    async def test_returns_entries_ordered_by_started_at_desc(self, db_session: AsyncSession):
        """Entries should be ordered by started_at descending (most recent first)."""
        from app.services.utility_service import get_journal_entries

        user = await _create_test_user(db_session, username="jrn_order", email="jrn_order@test.com")
        p = await _seed_place(db_session, name="JO Place", category="cafe", lon=4.83, lat=45.76, google_place_id="jrn_o_p1", city="Lyon")

        old_time = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
        mid_time = datetime.datetime(2025, 6, 15, 10, 0, tzinfo=datetime.timezone.utc)
        new_time = datetime.datetime(2025, 12, 1, 10, 0, tzinfo=datetime.timezone.utc)

        await _seed_visit(db_session, user_id=user.id, place_id=p, started_at=old_time)
        await _seed_visit(db_session, user_id=user.id, place_id=p, started_at=new_time)
        await _seed_visit(db_session, user_id=user.id, place_id=p, started_at=mid_time)

        result = await get_journal_entries(db_session, user.id, limit=20, offset=0)

        assert len(result) == 3
        # Most recent first
        assert result[0]["started_at"] >= result[1]["started_at"]
        assert result[1]["started_at"] >= result[2]["started_at"]

    async def test_includes_place_details(self, db_session: AsyncSession):
        """Entries should include place_id, place_name, city from joined Place."""
        from app.services.utility_service import get_journal_entries

        user = await _create_test_user(db_session, username="jrn_place", email="jrn_place@test.com")
        p = await _seed_place(
            db_session, name="JournalPlace", category="museum", lon=4.83, lat=45.76,
            google_place_id="jrn_pl_p1", city="Lyon",
        )
        await _seed_visit(db_session, user_id=user.id, place_id=p, duration_seconds=500)

        result = await get_journal_entries(db_session, user.id, limit=20, offset=0)

        assert len(result) == 1
        entry = result[0]
        assert entry["place_id"] == p
        assert entry["place_name"] == "JournalPlace"
        assert entry["city"] == "Lyon"
        assert entry["duration_seconds"] == 500

    async def test_includes_journal_note_when_present(self, db_session: AsyncSession):
        """Entries should include note text and photo_url when a JournalNote exists."""
        from app.services.utility_service import get_journal_entries

        user = await _create_test_user(db_session, username="jrn_note", email="jrn_note@test.com")
        p = await _seed_place(db_session, name="JN Place", category="cafe", lon=4.83, lat=45.76, google_place_id="jrn_n_p1", city="Lyon")
        v = await _seed_visit(db_session, user_id=user.id, place_id=p)
        await _seed_journal_note(db_session, visit_id=v, user_id=user.id, note_text="Great coffee!", photo_url="photo.jpg")

        result = await get_journal_entries(db_session, user.id, limit=20, offset=0)

        assert len(result) == 1
        entry = result[0]
        assert entry["note"] == "Great coffee!"
        assert entry["photo_url"] == "photo.jpg"

    async def test_note_null_when_no_journal_note(self, db_session: AsyncSession):
        """Entries should have null note/photo_url when no JournalNote exists."""
        from app.services.utility_service import get_journal_entries

        user = await _create_test_user(db_session, username="jrn_nonote", email="jrn_nonote@test.com")
        p = await _seed_place(db_session, name="JNN Place", category="cafe", lon=4.83, lat=45.76, google_place_id="jrn_nn_p1")
        await _seed_visit(db_session, user_id=user.id, place_id=p)

        result = await get_journal_entries(db_session, user.id, limit=20, offset=0)

        assert len(result) == 1
        assert result[0]["note"] is None
        assert result[0]["photo_url"] is None

    async def test_pagination_limit_and_offset(self, db_session: AsyncSession):
        """Should respect limit and offset for pagination."""
        from app.services.utility_service import get_journal_entries

        user = await _create_test_user(db_session, username="jrn_page", email="jrn_page@test.com")
        p = await _seed_place(db_session, name="JP Place", category="cafe", lon=4.83, lat=45.76, google_place_id="jrn_pg_p1")

        for i in range(5):
            await _seed_visit(
                db_session, user_id=user.id, place_id=p,
                started_at=datetime.datetime(2025, 6, 15 + i, 10, 0, tzinfo=datetime.timezone.utc),
            )

        # First page
        page1 = await get_journal_entries(db_session, user.id, limit=2, offset=0)
        assert len(page1) == 2

        # Second page
        page2 = await get_journal_entries(db_session, user.id, limit=2, offset=2)
        assert len(page2) == 2

        # Third page (only 1 remaining)
        page3 = await get_journal_entries(db_session, user.id, limit=2, offset=4)
        assert len(page3) == 1

        # All visit_ids should be unique across pages
        all_ids = [e["visit_id"] for e in page1 + page2 + page3]
        assert len(set(all_ids)) == 5


# ---------------------------------------------------------------------------
# Tests: add_journal_note
# ---------------------------------------------------------------------------


class TestAddJournalNote:
    """Tests for add_journal_note service function."""

    async def test_creates_new_note(self, db_session: AsyncSession):
        """Should create a new JournalNote when none exists for the visit."""
        from app.services.utility_service import add_journal_note

        user = await _create_test_user(db_session, username="jn_create", email="jn_create@test.com")
        p = await _seed_place(db_session, name="JNC Place", category="cafe", lon=4.83, lat=45.76, google_place_id="jn_c_p1", city="Lyon")
        v = await _seed_visit(db_session, user_id=user.id, place_id=p)

        result = await add_journal_note(db_session, user.id, v, "My first note", None)

        assert result["visit_id"] == v
        assert result["note"] == "My first note"
        assert result["photo_url"] is None
        assert result["place_name"] == "JNC Place"

    async def test_updates_existing_note(self, db_session: AsyncSession):
        """Should update the existing JournalNote for the same visit+user (upsert)."""
        from app.services.utility_service import add_journal_note

        user = await _create_test_user(db_session, username="jn_upsert", email="jn_upsert@test.com")
        p = await _seed_place(db_session, name="JNU Place", category="cafe", lon=4.83, lat=45.76, google_place_id="jn_u_p1", city="Lyon")
        v = await _seed_visit(db_session, user_id=user.id, place_id=p)

        # Create initial note
        await add_journal_note(db_session, user.id, v, "Initial note", None)

        # Upsert with new text and photo
        result = await add_journal_note(db_session, user.id, v, "Updated note", "photo.jpg")

        assert result["note"] == "Updated note"
        assert result["photo_url"] == "photo.jpg"

    async def test_raises_for_nonexistent_visit(self, db_session: AsyncSession):
        """Should raise an error when the visit_id does not exist or belongs to another user."""
        from app.services.utility_service import add_journal_note
        from app.core.exceptions import EntityNotFoundException

        user = await _create_test_user(db_session, username="jn_novisit", email="jn_novisit@test.com")

        with pytest.raises(EntityNotFoundException):
            await add_journal_note(db_session, user.id, 99999, "note", None)


# ---------------------------------------------------------------------------
# Tests: get_heatmap
# ---------------------------------------------------------------------------


class TestGetHeatmap:
    """Tests for get_heatmap service function."""

    async def test_returns_areas_with_visited_flag(self, db_session: AsyncSession):
        """Should return areas with correct visited flag based on user's visits."""
        from app.services.utility_service import get_heatmap

        user = await _create_test_user(db_session, username="hm_basic", email="hm_basic@test.com")

        area1 = await _seed_area(db_session, name="HM Area 1", city="Lyon", center_lon=4.83, center_lat=45.76)
        area2 = await _seed_area(db_session, name="HM Area 2", city="Lyon", center_lon=4.85, center_lat=45.78)

        p = await _seed_place(db_session, name="HM Place", category="cafe", lon=4.83, lat=45.76, google_place_id="hm_p1")
        await _seed_visit(db_session, user_id=user.id, place_id=p, area_id=area1)

        result = await get_heatmap(db_session, user.id, city="Lyon")

        assert result["total_areas"] == 2
        assert result["visited_areas"] == 1

        areas_by_id = {a["id"]: a for a in result["areas"]}
        assert areas_by_id[area1]["visited"] is True
        assert areas_by_id[area2]["visited"] is False

    async def test_returns_boundary_geojson(self, db_session: AsyncSession):
        """Should return boundary_geojson for each area."""
        from app.services.utility_service import get_heatmap

        user = await _create_test_user(db_session, username="hm_geojson", email="hm_geojson@test.com")
        await _seed_area(db_session, name="HM GJ Area", city="Lyon", center_lon=4.83, center_lat=45.76)

        result = await get_heatmap(db_session, user.id, city="Lyon")

        assert len(result["areas"]) >= 1
        area = result["areas"][0]
        assert area["boundary_geojson"] is not None
        # GeoJSON should be a dict with type "Polygon"
        geojson = area["boundary_geojson"]
        if isinstance(geojson, str):
            geojson = json.loads(geojson)
        assert geojson["type"] == "Polygon"

    async def test_explored_percentage(self, db_session: AsyncSession):
        """Should calculate correct exploration percentage."""
        from app.services.utility_service import get_heatmap

        user = await _create_test_user(db_session, username="hm_pct", email="hm_pct@test.com")

        area1 = await _seed_area(db_session, name="HM Pct 1", city="TestCity", center_lon=4.83, center_lat=45.76)
        area2 = await _seed_area(db_session, name="HM Pct 2", city="TestCity", center_lon=4.85, center_lat=45.78)
        area3 = await _seed_area(db_session, name="HM Pct 3", city="TestCity", center_lon=4.87, center_lat=45.80)
        area4 = await _seed_area(db_session, name="HM Pct 4", city="TestCity", center_lon=4.89, center_lat=45.82)

        p = await _seed_place(db_session, name="HM Pct P", category="cafe", lon=4.83, lat=45.76, google_place_id="hm_pct_p1")
        await _seed_visit(db_session, user_id=user.id, place_id=p, area_id=area1)

        result = await get_heatmap(db_session, user.id, city="TestCity")

        assert result["total_areas"] == 4
        assert result["visited_areas"] == 1
        assert result["explored_pct"] == 25.0

    async def test_city_filter(self, db_session: AsyncSession):
        """Should only return areas for the specified city."""
        from app.services.utility_service import get_heatmap

        user = await _create_test_user(db_session, username="hm_city", email="hm_city@test.com")

        await _seed_area(db_session, name="HM Lyon Area", city="LyonHM", center_lon=4.83, center_lat=45.76)
        await _seed_area(db_session, name="HM Paris Area", city="ParisHM", center_lon=2.35, center_lat=48.86)

        result = await get_heatmap(db_session, user.id, city="LyonHM")

        assert result["total_areas"] == 1
        assert result["areas"][0]["city"] == "LyonHM"

    async def test_no_city_returns_all_areas(self, db_session: AsyncSession):
        """Should return all areas when no city filter is provided."""
        from app.services.utility_service import get_heatmap

        user = await _create_test_user(db_session, username="hm_all", email="hm_all@test.com")

        await _seed_area(db_session, name="HM All 1", city="CityAll1", center_lon=4.83, center_lat=45.76)
        await _seed_area(db_session, name="HM All 2", city="CityAll2", center_lon=2.35, center_lat=48.86)

        result = await get_heatmap(db_session, user.id, city=None)

        # Should include at least these 2 areas (may include more from other tests)
        assert result["total_areas"] >= 2


# ---------------------------------------------------------------------------
# Tests: get_city_passport
# ---------------------------------------------------------------------------


class TestGetCityPassport:
    """Tests for get_city_passport service function."""

    async def test_returns_stamps_for_city(self, db_session: AsyncSession):
        """Should return neighborhood stamps for the given city."""
        from app.services.utility_service import get_city_passport

        user = await _create_test_user(db_session, username="cp_basic", email="cp_basic@test.com")

        area1 = await _seed_area(db_session, name="CP Neigh 1", city="PassCity", center_lon=4.83, center_lat=45.76)
        area2 = await _seed_area(db_session, name="CP Neigh 2", city="PassCity", center_lon=4.85, center_lat=45.78)
        area3 = await _seed_area(db_session, name="CP Neigh 3", city="PassCity", center_lon=4.87, center_lat=45.80)

        p = await _seed_place(db_session, name="CP Place", category="cafe", lon=4.83, lat=45.76, google_place_id="cp_p1")
        await _seed_visit(db_session, user_id=user.id, place_id=p, area_id=area1)

        result = await get_city_passport(db_session, user.id, "PassCity")

        assert result["city"] == "PassCity"
        assert result["total_neighborhoods"] == 3
        assert result["visited_count"] == 1
        assert len(result["stamps"]) == 3
        assert result["badge_earned"] is False
        assert result["explored_pct"] == pytest.approx(100.0 / 3.0, rel=0.1)

    async def test_badge_earned_when_all_visited(self, db_session: AsyncSession):
        """Badge should be earned when all neighborhoods are visited."""
        from app.services.utility_service import get_city_passport

        user = await _create_test_user(db_session, username="cp_badge", email="cp_badge@test.com")

        area1 = await _seed_area(db_session, name="Badge Neigh 1", city="BadgeCity", center_lon=4.83, center_lat=45.76)
        area2 = await _seed_area(db_session, name="Badge Neigh 2", city="BadgeCity", center_lon=4.85, center_lat=45.78)

        p1 = await _seed_place(db_session, name="Badge P1", category="cafe", lon=4.83, lat=45.76, google_place_id="cp_badge_p1")
        p2 = await _seed_place(db_session, name="Badge P2", category="cafe", lon=4.85, lat=45.78, google_place_id="cp_badge_p2")

        await _seed_visit(db_session, user_id=user.id, place_id=p1, area_id=area1)
        await _seed_visit(db_session, user_id=user.id, place_id=p2, area_id=area2)

        result = await get_city_passport(db_session, user.id, "BadgeCity")

        assert result["badge_earned"] is True
        assert result["visited_count"] == 2
        assert result["total_neighborhoods"] == 2
        assert result["explored_pct"] == 100.0

    async def test_stamps_include_visited_status(self, db_session: AsyncSession):
        """Each stamp should have visited flag and visited_at."""
        from app.services.utility_service import get_city_passport

        user = await _create_test_user(db_session, username="cp_stamp", email="cp_stamp@test.com")

        area1 = await _seed_area(db_session, name="Stamp Neigh 1", city="StampCity", center_lon=4.83, center_lat=45.76)
        area2 = await _seed_area(db_session, name="Stamp Neigh 2", city="StampCity", center_lon=4.85, center_lat=45.78)

        p = await _seed_place(db_session, name="Stamp P", category="cafe", lon=4.83, lat=45.76, google_place_id="cp_st_p1")
        await _seed_visit(db_session, user_id=user.id, place_id=p, area_id=area1)

        result = await get_city_passport(db_session, user.id, "StampCity")

        stamps_by_area = {s["area_id"]: s for s in result["stamps"]}
        assert stamps_by_area[area1]["visited"] is True
        assert stamps_by_area[area1]["visited_at"] is not None
        assert stamps_by_area[area2]["visited"] is False
        assert stamps_by_area[area2]["visited_at"] is None

    async def test_empty_city_returns_zero(self, db_session: AsyncSession):
        """Should return zero stamps for a city with no areas."""
        from app.services.utility_service import get_city_passport

        user = await _create_test_user(db_session, username="cp_none", email="cp_none@test.com")

        result = await get_city_passport(db_session, user.id, "NonexistentCity")

        assert result["city"] == "NonexistentCity"
        assert result["total_neighborhoods"] == 0
        assert result["visited_count"] == 0
        assert result["stamps"] == []
        assert result["badge_earned"] is False
        assert result["explored_pct"] == 0.0
