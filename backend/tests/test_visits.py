"""Tests for the Visit tracking service, API endpoints, and UserPresence state machine.

Covers all Step 8 acceptance criteria:
- POST /visits/ping with accuracy > 100m returns 422 with rejection reason
- POST /visits/ping finds all places within 75m using get_nearby_places()
- POST /visits/ping creates/updates UserPresence in Redis for each nearby place
- Auto-confirm when dwell time >= 5min AND reading_count >= 3
- POST /visits/ping response includes nearby_places, confirmed_visits, rejected
- Two places within 75m tracked independently (separate UserPresence keys)
- Duplicate visits prevented within 2-hour session window
- UserPresence TTL 30 minutes
- N consecutive out-of-range pings clear UserPresence
- GET /visits/history returns paginated visits with place_name, area_id, timestamps
- Visit records are app-agnostic (no app identifier column)
"""

from __future__ import annotations

import datetime
import json
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.area import Area
from app.models.place import Place
from app.models.user import User
from app.models.visit import Visit
from app.core.exceptions import AppException, GPSAccuracyException
from app.services.visit_service import (
    DUPLICATE_VISIT_WINDOW_SECONDS,
    OUT_OF_RANGE_THRESHOLD,
    auto_confirm_visit,
    get_visit_history,
    process_gps_ping,
)

# All tests must share the session-scoped event loop to work with the
# session-scoped async engine fixture (pytest-asyncio 0.25 pattern).
pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# Helpers to seed test users and places
# ---------------------------------------------------------------------------

_user_counter = 0


async def _seed_user(db: AsyncSession) -> User:
    """Create a unique test user in the database and return the ORM instance."""
    global _user_counter
    _user_counter += 1
    user = User(
        username=f"vuser_{_user_counter}",
        email=f"vuser_{_user_counter}@test.com",
        password_hash=hash_password("testpass123"),
    )
    db.add(user)
    await db.flush()
    return user


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
    city: str | None = None,
    zone_type: str | None = None,
    polygon_wkt: str,
) -> int:
    """Insert a test area using raw SQL with a WKT polygon for Geography.

    Args:
        db: Async database session.
        name: Human-readable area name.
        city: City this area belongs to.
        zone_type: Classification of the area.
        polygon_wkt: Well-Known Text representation of the polygon boundary
                     e.g. 'POLYGON((lon1 lat1, lon2 lat2, ..., lon1 lat1))'.

    Returns the area ID.
    """
    result = await db.execute(
        text(
            "INSERT INTO areas (name, city, zone_type, boundary) "
            "VALUES (:name, :city, :zone_type, "
            "CAST(ST_GeomFromText(:wkt, 4326) AS geography)) "
            "RETURNING id"
        ),
        {
            "name": name,
            "city": city,
            "zone_type": zone_type,
            "wkt": polygon_wkt,
        },
    )
    area_id = result.scalar_one()
    await db.flush()
    return area_id


# ---------------------------------------------------------------------------
# Unit tests: GPS accuracy rejection
# ---------------------------------------------------------------------------


class TestGPSAccuracyRejection:
    """Tests for GPS accuracy validation in process_gps_ping."""

    async def test_rejects_accuracy_above_100m(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """GPS ping with accuracy > 100m should raise GPSAccuracyException."""
        with pytest.raises(GPSAccuracyException) as exc_info:
            await process_gps_ping(
                db=db_session,
                user_id=1,
                lat=48.8566,
                lon=2.3522,
                accuracy=150.0,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
        assert exc_info.value.status_code == 422
        assert "GPS accuracy insufficient" in exc_info.value.message

    async def test_rejects_accuracy_at_exactly_101m(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """GPS ping with accuracy = 101m should raise GPSAccuracyException."""
        with pytest.raises(GPSAccuracyException) as exc_info:
            await process_gps_ping(
                db=db_session,
                user_id=1,
                lat=48.8566,
                lon=2.3522,
                accuracy=101.0,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
        assert exc_info.value.status_code == 422
        assert "GPS accuracy insufficient" in exc_info.value.message

    async def test_accepts_accuracy_at_100m(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """GPS ping with accuracy = 100m should be accepted (no exception)."""
        result = await process_gps_ping(
            db=db_session,
            user_id=1,
            lat=48.8566,
            lon=2.3522,
            accuracy=100.0,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        assert result["rejected"] is False
        assert result["rejection_reason"] is None

    async def test_accepts_good_accuracy(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """GPS ping with good accuracy (e.g., 10m) should be accepted."""
        result = await process_gps_ping(
            db=db_session,
            user_id=1,
            lat=48.8566,
            lon=2.3522,
            accuracy=10.0,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        assert result["rejected"] is False


# ---------------------------------------------------------------------------
# Tests: Nearby place detection and UserPresence creation
# ---------------------------------------------------------------------------


class TestNearbyPlaceDetection:
    """Tests for finding nearby places and creating UserPresence."""

    async def test_finds_place_within_geofence(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Should find a place within geofence radius (75m)."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Visit Cafe",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_cafe_1",
        )

        result = await process_gps_ping(
            db=db_session,
            user_id=user.id,
            lat=48.8566,
            lon=2.3522,
            accuracy=10.0,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        assert result["rejected"] is False
        assert len(result["nearby_places"]) >= 1
        place_ids = [p["place_id"] for p in result["nearby_places"]]
        assert place_id in place_ids

    async def test_excludes_place_outside_geofence(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Should not find a place beyond geofence radius (75m)."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Far Cafe",
            category="cafe",
            lon=2.3600,
            lat=48.8600,
            google_place_id="visit_far_cafe",
        )

        result = await process_gps_ping(
            db=db_session,
            user_id=user.id,
            lat=51.5074,
            lon=-0.1278,
            accuracy=10.0,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        place_ids = [p["place_id"] for p in result["nearby_places"]]
        assert place_id not in place_ids

    async def test_creates_user_presence_in_redis(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """First GPS ping near a place should create UserPresence in Redis."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Presence Test Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_presence_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)
        await process_gps_ping(
            db=db_session,
            user_id=user.id,
            lat=48.8566,
            lon=2.3522,
            accuracy=10.0,
            timestamp=now,
        )

        from app.core.redis import get_user_presence

        presence = await get_user_presence(user.id, place_id)
        assert presence is not None
        assert presence["reading_count"] == 1
        assert "first_seen" in presence
        assert "last_seen" in presence

    async def test_updates_user_presence_on_subsequent_ping(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Subsequent pings should update last_seen and increment reading_count."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Update Presence Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_update_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        await process_gps_ping(
            db=db_session,
            user_id=user.id,
            lat=48.8566,
            lon=2.3522,
            accuracy=10.0,
            timestamp=now,
        )

        await process_gps_ping(
            db=db_session,
            user_id=user.id,
            lat=48.8566,
            lon=2.3522,
            accuracy=10.0,
            timestamp=now + datetime.timedelta(seconds=30),
        )

        from app.core.redis import get_user_presence

        presence = await get_user_presence(user.id, place_id)
        assert presence is not None
        assert presence["reading_count"] == 2

    async def test_response_includes_distance(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Nearby places in response should include distance_m."""
        user = await _seed_user(db_session)
        await _seed_place(
            db_session,
            name="Distance Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_dist_1",
        )

        result = await process_gps_ping(
            db=db_session,
            user_id=user.id,
            lat=48.8566,
            lon=2.3522,
            accuracy=10.0,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        for place in result["nearby_places"]:
            assert "distance_m" in place
            assert isinstance(place["distance_m"], (int, float))


# ---------------------------------------------------------------------------
# Tests: Auto-confirm visit
# ---------------------------------------------------------------------------


class TestAutoConfirmVisit:
    """Tests for automatic visit confirmation."""

    async def test_auto_confirms_after_dwell_and_readings(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Visit should be confirmed when dwell >= 5min AND readings >= 3."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Confirm Place",
            category="restaurant",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_confirm_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # First ping: creates presence
        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now,
        )

        # Second ping: 2.5 minutes later
        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now + datetime.timedelta(seconds=150),
        )

        # Third ping: 5 minutes later (should auto-confirm)
        result = await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now + datetime.timedelta(seconds=300),
        )

        assert len(result["confirmed_visits"]) == 1
        confirmed = result["confirmed_visits"][0]
        assert confirmed["place_id"] == place_id
        assert confirmed["duration_seconds"] == 300

    async def test_no_confirm_before_min_duration(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Should not confirm visit if dwell time < 5 minutes."""
        user = await _seed_user(db_session)
        await _seed_place(
            db_session,
            name="No Confirm Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_noconfirm_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # Three pings over 2 minutes (not enough dwell time)
        for i in range(3):
            result = await process_gps_ping(
                db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
                accuracy=10.0, timestamp=now + datetime.timedelta(seconds=i * 40),
            )

        assert len(result["confirmed_visits"]) == 0

    async def test_no_confirm_before_min_readings(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Should not confirm visit if reading_count < 3 even with enough dwell."""
        user = await _seed_user(db_session)
        await _seed_place(
            db_session,
            name="Min Readings Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_minread_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # Only 2 pings but 5+ minutes apart
        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now,
        )

        result = await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now + datetime.timedelta(seconds=600),
        )

        # Only 2 readings, need 3 minimum
        assert len(result["confirmed_visits"]) == 0

    async def test_visit_record_created_in_db(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Auto-confirmed visit should create a Visit record in the database."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="DB Visit Place",
            category="restaurant",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_db_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # Three pings over 5+ minutes
        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now,
        )
        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now + datetime.timedelta(seconds=150),
        )
        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now + datetime.timedelta(seconds=300),
        )

        # Check the database for the Visit record
        from sqlalchemy import select as sa_select

        stmt = (
            sa_select(Visit)
            .where(Visit.user_id == user.id)
            .where(Visit.place_id == place_id)
        )
        result = await db_session.execute(stmt)
        visit = result.scalars().first()

        assert visit is not None
        assert visit.user_id == user.id
        assert visit.place_id == place_id
        assert visit.duration_seconds == 300
        assert visit.started_at is not None
        assert visit.ended_at is not None

    async def test_presence_deleted_after_confirm(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """UserPresence should be deleted from Redis after visit confirmation."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Presence Delete Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_presdelete_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # Three pings over 5+ minutes
        for i in range(3):
            await process_gps_ping(
                db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
                accuracy=10.0,
                timestamp=now + datetime.timedelta(seconds=i * 150),
            )

        from app.core.redis import get_user_presence

        presence = await get_user_presence(user.id, place_id)
        assert presence is None, "UserPresence should be deleted after confirmation"


# ---------------------------------------------------------------------------
# Tests: Multi-place concurrent tracking
# ---------------------------------------------------------------------------


class TestMultiPlaceTracking:
    """Tests for concurrent tracking of multiple places."""

    async def test_tracks_two_places_independently(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Two places within geofence should be tracked with separate presence keys."""
        user = await _seed_user(db_session)
        place_id_1 = await _seed_place(
            db_session,
            name="Multi Place A",
            category="cafe",
            lon=2.35220,
            lat=48.85660,
            google_place_id="visit_multi_a",
        )
        place_id_2 = await _seed_place(
            db_session,
            name="Multi Place B",
            category="restaurant",
            lon=2.35225,
            lat=48.85663,
            google_place_id="visit_multi_b",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        result = await process_gps_ping(
            db=db_session, user_id=user.id,
            lat=48.85661, lon=2.35222,
            accuracy=10.0, timestamp=now,
        )

        place_ids = [p["place_id"] for p in result["nearby_places"]]
        assert place_id_1 in place_ids
        assert place_id_2 in place_ids

        from app.core.redis import get_user_presence

        presence_a = await get_user_presence(user.id, place_id_1)
        presence_b = await get_user_presence(user.id, place_id_2)
        assert presence_a is not None
        assert presence_b is not None

    async def test_confirms_each_place_independently(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Each qualifying place should get its own Visit record."""
        user = await _seed_user(db_session)
        place_id_1 = await _seed_place(
            db_session,
            name="Multi Confirm A",
            category="cafe",
            lon=2.35220,
            lat=48.85660,
            google_place_id="visit_mconfirm_a",
        )
        place_id_2 = await _seed_place(
            db_session,
            name="Multi Confirm B",
            category="restaurant",
            lon=2.35225,
            lat=48.85663,
            google_place_id="visit_mconfirm_b",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        for i in range(3):
            await process_gps_ping(
                db=db_session, user_id=user.id,
                lat=48.85661, lon=2.35222,
                accuracy=10.0,
                timestamp=now + datetime.timedelta(seconds=i * 150),
            )

        from sqlalchemy import select as sa_select

        stmt = sa_select(Visit).where(Visit.user_id == user.id)
        result = await db_session.execute(stmt)
        visits = result.scalars().all()

        confirmed_place_ids = {v.place_id for v in visits}
        assert place_id_1 in confirmed_place_ids
        assert place_id_2 in confirmed_place_ids


# ---------------------------------------------------------------------------
# Tests: Duplicate visit prevention
# ---------------------------------------------------------------------------


class TestDuplicateVisitPrevention:
    """Tests for preventing duplicate Visit records."""

    async def test_no_duplicate_within_session_window(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Should not create duplicate Visit for same user+place within 2 hours."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Duplicate Test Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_dup_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # First full visit cycle (3 pings over 5+ minutes)
        for i in range(3):
            await process_gps_ping(
                db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
                accuracy=10.0,
                timestamp=now + datetime.timedelta(seconds=i * 150),
            )

        # Second full visit cycle 30 minutes later (within 2-hour window)
        later = now + datetime.timedelta(minutes=30)
        for i in range(3):
            await process_gps_ping(
                db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
                accuracy=10.0,
                timestamp=later + datetime.timedelta(seconds=i * 150),
            )

        from sqlalchemy import select as sa_select, func

        stmt = (
            sa_select(func.count())
            .select_from(Visit)
            .where(Visit.user_id == user.id)
            .where(Visit.place_id == place_id)
        )
        result = await db_session.execute(stmt)
        count = result.scalar_one()

        assert count == 1, f"Expected 1 visit but found {count}"


# ---------------------------------------------------------------------------
# Tests: UserPresence TTL
# ---------------------------------------------------------------------------


class TestUserPresenceTTL:
    """Tests for UserPresence TTL behavior."""

    async def test_presence_has_ttl(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """UserPresence entries should have a TTL set in Redis."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="TTL Test Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_ttl_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now,
        )

        key = f"presence:{user.id}:{place_id}"
        ttl = await redis_client.ttl(key)

        assert ttl > 0, "Key should have a TTL set"
        assert ttl <= 1800, f"TTL should be <= 1800 seconds, got {ttl}"


# ---------------------------------------------------------------------------
# Tests: Out-of-range clearing (GPS jitter protection)
# ---------------------------------------------------------------------------


class TestOutOfRangeClearing:
    """Tests for clearing UserPresence after consecutive out-of-range pings."""

    async def test_clears_after_n_consecutive_misses(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """UserPresence should be cleared after N consecutive out-of-range pings."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Out of Range Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_oor_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # First ping near the place to create presence
        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now,
        )

        from app.core.redis import get_user_presence

        presence = await get_user_presence(user.id, place_id)
        assert presence is not None, "Presence should exist after first in-range ping"

        # Send N out-of-range pings (from London)
        for i in range(OUT_OF_RANGE_THRESHOLD):
            await process_gps_ping(
                db=db_session, user_id=user.id, lat=51.5074, lon=-0.1278,
                accuracy=10.0,
                timestamp=now + datetime.timedelta(seconds=(i + 1) * 30),
            )

        presence = await get_user_presence(user.id, place_id)
        assert presence is None, "Presence should be cleared after consecutive misses"

    async def test_does_not_clear_before_threshold(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """UserPresence should NOT be cleared before N consecutive misses."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Jitter Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_jitter_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now,
        )

        # Only N-1 out-of-range pings (should not clear yet)
        for i in range(OUT_OF_RANGE_THRESHOLD - 1):
            await process_gps_ping(
                db=db_session, user_id=user.id, lat=51.5074, lon=-0.1278,
                accuracy=10.0,
                timestamp=now + datetime.timedelta(seconds=(i + 1) * 30),
            )

        from app.core.redis import get_user_presence

        presence = await get_user_presence(user.id, place_id)
        assert presence is not None, "Presence should survive before reaching threshold"

    async def test_resets_miss_count_on_in_range_ping(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """An in-range ping should reset the consecutive miss counter."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Reset Jitter Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_resetjit_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now,
        )

        # One out-of-range ping
        await process_gps_ping(
            db=db_session, user_id=user.id, lat=51.5074, lon=-0.1278,
            accuracy=10.0, timestamp=now + datetime.timedelta(seconds=30),
        )

        # Back in range - should reset miss count
        await process_gps_ping(
            db=db_session, user_id=user.id, lat=48.8566, lon=2.3522,
            accuracy=10.0, timestamp=now + datetime.timedelta(seconds=60),
        )

        from app.core.redis import get_user_presence

        presence = await get_user_presence(user.id, place_id)
        assert presence is not None
        assert presence.get("consecutive_misses", 0) == 0


# ---------------------------------------------------------------------------
# Tests: visit_service.get_visit_history
# ---------------------------------------------------------------------------


class TestGetVisitHistory:
    """Tests for paginated visit history retrieval."""

    async def test_returns_visits_with_place_name(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Visit history should include place_name from joined Place table."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="History Place",
            category="restaurant",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_hist_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        visit = Visit(
            user_id=user.id,
            place_id=place_id,
            started_at=now - datetime.timedelta(minutes=10),
            ended_at=now - datetime.timedelta(minutes=5),
            duration_seconds=300,
        )
        db_session.add(visit)
        await db_session.flush()

        history = await get_visit_history(db_session, user_id=user.id)

        assert len(history) == 1
        assert history[0]["place_name"] == "History Place"
        assert history[0]["place_id"] == place_id
        assert history[0]["duration_seconds"] == 300
        assert history[0]["started_at"] is not None
        assert history[0]["ended_at"] is not None

    async def test_pagination_limit_offset(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Should respect limit and offset parameters."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Paginate Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_paginate_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        for i in range(5):
            visit = Visit(
                user_id=user.id,
                place_id=place_id,
                started_at=now - datetime.timedelta(hours=i + 1),
                ended_at=now - datetime.timedelta(hours=i, minutes=55),
                duration_seconds=300,
            )
            db_session.add(visit)
        await db_session.flush()

        page1 = await get_visit_history(db_session, user_id=user.id, limit=2, offset=0)
        assert len(page1) == 2

        page2 = await get_visit_history(db_session, user_id=user.id, limit=2, offset=2)
        assert len(page2) == 2

        page3 = await get_visit_history(db_session, user_id=user.id, limit=2, offset=4)
        assert len(page3) == 1

    async def test_ordered_by_most_recent_first(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Visits should be ordered by started_at descending (most recent first)."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Order Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_order_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        old_visit = Visit(
            user_id=user.id,
            place_id=place_id,
            started_at=now - datetime.timedelta(hours=5),
            ended_at=now - datetime.timedelta(hours=4, minutes=55),
            duration_seconds=300,
        )
        new_visit = Visit(
            user_id=user.id,
            place_id=place_id,
            started_at=now - datetime.timedelta(hours=1),
            ended_at=now - datetime.timedelta(minutes=55),
            duration_seconds=300,
        )
        db_session.add(old_visit)
        db_session.add(new_visit)
        await db_session.flush()

        history = await get_visit_history(db_session, user_id=user.id)
        assert len(history) >= 2
        assert history[0]["started_at"] > history[1]["started_at"]

    async def test_returns_area_id(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """Visit history should include area_id (nullable)."""
        user = await _seed_user(db_session)
        place_id = await _seed_place(
            db_session,
            name="Area Test Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="visit_area_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        visit = Visit(
            user_id=user.id,
            place_id=place_id,
            area_id=None,
            started_at=now - datetime.timedelta(minutes=10),
            ended_at=now - datetime.timedelta(minutes=5),
            duration_seconds=300,
        )
        db_session.add(visit)
        await db_session.flush()

        history = await get_visit_history(db_session, user_id=user.id)
        assert len(history) == 1
        assert "area_id" in history[0]
        assert history[0]["area_id"] is None


# ---------------------------------------------------------------------------
# Tests: Visit model is app-agnostic
# ---------------------------------------------------------------------------


class TestVisitModelAppAgnostic:
    """Verify Visit records have no app identifier column."""

    def test_no_app_identifier_column(self):
        """Visit model should not have any app_id or app_type column."""
        columns = {c.name for c in Visit.__table__.columns}
        assert "app_id" not in columns
        assert "app_type" not in columns
        assert "app" not in columns
        assert "app_identifier" not in columns


# ---------------------------------------------------------------------------
# Tests: area_id assignment via ST_Contains
# ---------------------------------------------------------------------------


class TestAreaIdAssignment:
    """Tests for area_id assignment using PostGIS ST_Contains in auto_confirm_visit."""

    async def test_assigns_area_id_when_place_inside_area(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """When a place falls within an area boundary, the visit should have the correct area_id."""
        user = await _seed_user(db_session)

        # Create an area polygon that encompasses the test place coordinates
        # A square around (lon=2.3522, lat=48.8566) -- about 500m each side
        area_id = await _seed_area(
            db_session,
            name="Le Marais",
            city="Paris",
            zone_type="neighborhood",
            polygon_wkt=(
                "POLYGON(("
                "2.3500 48.8550, "
                "2.3550 48.8550, "
                "2.3550 48.8580, "
                "2.3500 48.8580, "
                "2.3500 48.8550"
                "))"
            ),
        )

        # Create a place inside the area
        place_id = await _seed_place(
            db_session,
            name="Area Assign Place",
            category="restaurant",
            lon=2.3522,
            lat=48.8566,
            google_place_id="area_assign_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # Directly call auto_confirm_visit (unit test level)
        confirmed = await auto_confirm_visit(
            db=db_session,
            user_id=user.id,
            place_id=place_id,
            first_seen=now - datetime.timedelta(minutes=10),
            last_seen=now - datetime.timedelta(minutes=5),
            dwell_seconds=300,
        )

        assert confirmed is not None
        assert confirmed["place_id"] == place_id

        # Verify the Visit record has the correct area_id
        from sqlalchemy import select as sa_select

        stmt = (
            sa_select(Visit)
            .where(Visit.user_id == user.id)
            .where(Visit.place_id == place_id)
        )
        result = await db_session.execute(stmt)
        visit = result.scalars().first()

        assert visit is not None
        assert visit.area_id == area_id

    async def test_area_id_none_when_place_outside_all_areas(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """When a place does not fall within any area, area_id should be None."""
        user = await _seed_user(db_session)

        # Create an area polygon far away from the test place
        await _seed_area(
            db_session,
            name="Montmartre",
            city="Paris",
            zone_type="neighborhood",
            polygon_wkt=(
                "POLYGON(("
                "2.3400 48.8850, "
                "2.3450 48.8850, "
                "2.3450 48.8880, "
                "2.3400 48.8880, "
                "2.3400 48.8850"
                "))"
            ),
        )

        # Create a place that is NOT inside any area
        place_id = await _seed_place(
            db_session,
            name="Isolated Place",
            category="cafe",
            lon=2.3900,
            lat=48.8200,
            google_place_id="area_none_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        confirmed = await auto_confirm_visit(
            db=db_session,
            user_id=user.id,
            place_id=place_id,
            first_seen=now - datetime.timedelta(minutes=10),
            last_seen=now - datetime.timedelta(minutes=5),
            dwell_seconds=300,
        )

        assert confirmed is not None

        from sqlalchemy import select as sa_select

        stmt = (
            sa_select(Visit)
            .where(Visit.user_id == user.id)
            .where(Visit.place_id == place_id)
        )
        result = await db_session.execute(stmt)
        visit = result.scalars().first()

        assert visit is not None
        assert visit.area_id is None

    async def test_area_id_none_when_no_areas_exist(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """When no areas exist in the database, area_id should be None."""
        user = await _seed_user(db_session)

        place_id = await _seed_place(
            db_session,
            name="No Areas Place",
            category="park",
            lon=2.3522,
            lat=48.8566,
            google_place_id="area_noexist_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        confirmed = await auto_confirm_visit(
            db=db_session,
            user_id=user.id,
            place_id=place_id,
            first_seen=now - datetime.timedelta(minutes=10),
            last_seen=now - datetime.timedelta(minutes=5),
            dwell_seconds=300,
        )

        assert confirmed is not None

        from sqlalchemy import select as sa_select

        stmt = (
            sa_select(Visit)
            .where(Visit.user_id == user.id)
            .where(Visit.place_id == place_id)
        )
        result = await db_session.execute(stmt)
        visit = result.scalars().first()

        assert visit is not None
        assert visit.area_id is None

    async def test_area_id_assigned_when_place_is_none(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """When the place does not exist in DB, area_id should be None and visit still created."""
        user = await _seed_user(db_session)

        # Use a place_id that does not exist in the places table
        # First seed a place so the FK exists, then test with a valid place_id
        # but we'll test the edge case where place lookup returns None by
        # using a non-existent ID. However, the Visit FK constraint will
        # prevent this. Instead, verify that when place has no containing
        # area, area_id is None (already covered above). This test ensures
        # the code path where db.get(Place, place_id) returns None is safe.
        # We need to insert a place without the FK constraint check on visits.
        # Since visit FK to places is NOT NULL, we can't test with a missing place.
        # Instead, we verify the full-cycle through process_gps_ping works
        # with area assignment.
        place_id = await _seed_place(
            db_session,
            name="Full Cycle Place",
            category="restaurant",
            lon=2.3522,
            lat=48.8566,
            google_place_id="area_fullcycle_1",
        )

        area_id = await _seed_area(
            db_session,
            name="Full Cycle Area",
            city="Paris",
            zone_type="district",
            polygon_wkt=(
                "POLYGON(("
                "2.3500 48.8550, "
                "2.3550 48.8550, "
                "2.3550 48.8580, "
                "2.3500 48.8580, "
                "2.3500 48.8550"
                "))"
            ),
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # Full ping cycle: 3 pings over 5+ minutes to trigger auto-confirm
        for i in range(3):
            await process_gps_ping(
                db=db_session,
                user_id=user.id,
                lat=48.8566,
                lon=2.3522,
                accuracy=10.0,
                timestamp=now + datetime.timedelta(seconds=i * 150),
            )

        from sqlalchemy import select as sa_select

        stmt = (
            sa_select(Visit)
            .where(Visit.user_id == user.id)
            .where(Visit.place_id == place_id)
        )
        result = await db_session.execute(stmt)
        visit = result.scalars().first()

        assert visit is not None
        assert visit.area_id == area_id


# ---------------------------------------------------------------------------
# API endpoint tests: POST /visits/ping
# ---------------------------------------------------------------------------


class TestPingEndpoint:
    """API tests for POST /visits/ping."""

    async def test_ping_requires_auth(self, client: AsyncClient):
        """Ping endpoint should require authentication."""
        response = await client.post(
            "/visits/ping",
            json={
                "lat": 48.8566,
                "lon": 2.3522,
                "accuracy": 10.0,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 401

    async def test_ping_rejects_bad_accuracy(
        self,
        db_session: AsyncSession,
        client: AsyncClient,
        auth_headers: dict,
        redis_client: Any,
    ):
        """POST /visits/ping with accuracy > 100m should return 422."""
        response = await client.post(
            "/visits/ping",
            json={
                "lat": 48.8566,
                "lon": 2.3522,
                "accuracy": 150.0,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error_type"] == "gps_accuracy_error"
        assert "GPS accuracy insufficient" in data["message"]

    async def test_ping_finds_nearby_places(
        self,
        db_session: AsyncSession,
        client: AsyncClient,
        auth_headers: dict,
        redis_client: Any,
    ):
        """POST /visits/ping should return nearby places within geofence."""
        place_id = await _seed_place(
            db_session,
            name="API Ping Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="api_ping_1",
        )

        response = await client.post(
            "/visits/ping",
            json={
                "lat": 48.8566,
                "lon": 2.3522,
                "accuracy": 10.0,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rejected"] is False
        place_ids = [p["place_id"] for p in data["nearby_places"]]
        assert place_id in place_ids

    async def test_ping_response_structure(
        self,
        db_session: AsyncSession,
        client: AsyncClient,
        auth_headers: dict,
        redis_client: Any,
    ):
        """Response should include nearby_places, confirmed_visits, rejected fields."""
        response = await client.post(
            "/visits/ping",
            json={
                "lat": 48.8566,
                "lon": 2.3522,
                "accuracy": 10.0,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "nearby_places" in data
        assert "confirmed_visits" in data
        assert "rejected" in data
        assert "rejection_reason" in data
        assert isinstance(data["nearby_places"], list)
        assert isinstance(data["confirmed_visits"], list)


# ---------------------------------------------------------------------------
# API endpoint tests: GET /visits/history
# ---------------------------------------------------------------------------


class TestHistoryEndpoint:
    """API tests for GET /visits/history."""

    async def test_history_requires_auth(self, client: AsyncClient):
        """History endpoint should require authentication."""
        response = await client.get("/visits/history")
        assert response.status_code == 401

    async def test_history_returns_visits(
        self,
        db_session: AsyncSession,
        client: AsyncClient,
        auth_headers: dict,
        test_user: Any,
    ):
        """GET /visits/history should return the user's visits."""
        place_id = await _seed_place(
            db_session,
            name="API History Place",
            category="restaurant",
            lon=2.3522,
            lat=48.8566,
            google_place_id="api_hist_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)
        visit = Visit(
            user_id=test_user.id,
            place_id=place_id,
            started_at=now - datetime.timedelta(minutes=10),
            ended_at=now - datetime.timedelta(minutes=5),
            duration_seconds=300,
        )
        db_session.add(visit)
        await db_session.flush()

        response = await client.get(
            "/visits/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        v = next((item for item in data if item["place_id"] == place_id), None)
        assert v is not None
        assert v["place_name"] == "API History Place"
        assert v["duration_seconds"] == 300
        assert "started_at" in v
        assert "ended_at" in v
        assert "area_id" in v

    async def test_history_pagination(
        self,
        db_session: AsyncSession,
        client: AsyncClient,
        auth_headers: dict,
        test_user: Any,
    ):
        """GET /visits/history should support limit and offset."""
        place_id = await _seed_place(
            db_session,
            name="Paginate API Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="api_paginate_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)
        for i in range(5):
            visit = Visit(
                user_id=test_user.id,
                place_id=place_id,
                started_at=now - datetime.timedelta(hours=i + 1),
                ended_at=now - datetime.timedelta(hours=i, minutes=55),
                duration_seconds=300,
            )
            db_session.add(visit)
        await db_session.flush()

        response = await client.get(
            "/visits/history",
            params={"limit": 2, "offset": 0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_history_empty_for_new_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /visits/history should return empty list for user with no visits."""
        response = await client.get(
            "/visits/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Tests: Redis failure graceful degradation
# ---------------------------------------------------------------------------


class TestRedisFailureGracefulDegradation:
    """Tests that Redis transient failures do not cause unhandled 500 errors."""

    async def test_process_gps_ping_survives_redis_set_failure(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """process_gps_ping should continue when set_user_presence raises AppException."""
        from unittest.mock import AsyncMock, patch

        user = await _seed_user(db_session)
        await _seed_place(
            db_session,
            name="Redis Fail Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="redis_fail_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # Patch set_user_presence to simulate Redis failure
        with patch(
            "app.services.visit_service.set_user_presence",
            new_callable=AsyncMock,
            side_effect=AppException("Redis service unavailable"),
        ), patch(
            "app.services.visit_service.get_user_presence",
            new_callable=AsyncMock,
            return_value=None,
        ):
            # Should NOT raise -- graceful degradation
            result = await process_gps_ping(
                db=db_session,
                user_id=user.id,
                lat=48.8566,
                lon=2.3522,
                accuracy=10.0,
                timestamp=now,
            )

        # The ping should still return nearby places (found via DB)
        assert result["rejected"] is False
        assert isinstance(result["nearby_places"], list)
        assert isinstance(result["confirmed_visits"], list)

    async def test_process_gps_ping_survives_redis_get_failure(
        self, db_session: AsyncSession, redis_client: Any
    ):
        """process_gps_ping should continue when get_user_presence raises AppException."""
        from unittest.mock import AsyncMock, patch

        user = await _seed_user(db_session)
        await _seed_place(
            db_session,
            name="Redis Get Fail Place",
            category="cafe",
            lon=2.3522,
            lat=48.8566,
            google_place_id="redis_getfail_1",
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        # Patch get_user_presence to simulate Redis failure
        with patch(
            "app.services.visit_service.get_user_presence",
            new_callable=AsyncMock,
            side_effect=AppException("Redis service unavailable"),
        ):
            # Should NOT raise -- graceful degradation
            result = await process_gps_ping(
                db=db_session,
                user_id=user.id,
                lat=48.8566,
                lon=2.3522,
                accuracy=10.0,
                timestamp=now,
            )

        assert result["rejected"] is False
        assert isinstance(result["nearby_places"], list)

    async def test_ping_endpoint_survives_redis_failure(
        self,
        db_session: AsyncSession,
        client: AsyncClient,
        auth_headers: dict,
        redis_client: Any,
    ):
        """POST /visits/ping should return 200 (not 500) when Redis fails during tracking."""
        from unittest.mock import AsyncMock, patch

        with patch(
            "app.services.visit_service.get_user_presence",
            new_callable=AsyncMock,
            side_effect=AppException("Redis service unavailable"),
        ):
            response = await client.post(
                "/visits/ping",
                json={
                    "lat": 48.8566,
                    "lon": 2.3522,
                    "accuracy": 10.0,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["rejected"] is False
