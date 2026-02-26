"""Visit tracking service with GPS-based geofence confirmation.

Implements the UserPresence state machine in Redis for tracking user dwell
time near places. When a user remains within the geofence radius for the
minimum required duration with sufficient GPS readings, a Visit record is
automatically created in the database.

State transitions:
    [None] -- GPS within radius --> [Tracking] -- dwell >= 5min & reads >= 3 --> [Confirmed]
                                        |                                            |
                                        | N consecutive out-of-range                 v
                                        v                                      [Visit Record]
                                   [Cleared]                                   [Presence Deleted]
"""

from __future__ import annotations

import datetime
import json
import logging
from typing import Any, Optional

from geoalchemy2.functions import ST_Contains
from geoalchemy2.types import Geometry
from sqlalchemy import cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AppException, GPSAccuracyException
from app.core.redis import (
    delete_user_presence,
    get_redis_client,
    get_user_presence,
    set_user_presence,
)
from app.models.area import Area
from app.models.place import Place
from app.models.visit import Visit
from app.services.places_service import get_nearby_places

logger = logging.getLogger(__name__)

# Number of consecutive out-of-range pings required before clearing
# UserPresence (GPS jitter protection).
OUT_OF_RANGE_THRESHOLD = 3

# Session window for duplicate visit prevention: if a Visit exists for the
# same user+place within this many seconds, no new Visit is created.
DUPLICATE_VISIT_WINDOW_SECONDS = 7200  # 2 hours


async def process_gps_ping(
    db: AsyncSession,
    user_id: int,
    lat: float,
    lon: float,
    accuracy: float,
    timestamp: datetime.datetime,
) -> dict[str, Any]:
    """Process a GPS ping from a user for visit tracking.

    1. Validate GPS accuracy (reject if > 100m).
    2. Find all places within the configured geofence radius.
    3. For each nearby place, create or update UserPresence in Redis.
    4. Check auto-confirm conditions for each presence.
    5. Handle out-of-range tracking for previously tracked places.

    Args:
        db: Async database session.
        user_id: The authenticated user's ID.
        lat: Latitude from the GPS reading.
        lon: Longitude from the GPS reading.
        accuracy: GPS accuracy in meters (lower is better).
        timestamp: When the GPS reading was taken.

    Returns:
        Dict with nearby_places, confirmed_visits, rejected, rejection_reason.

    Raises:
        GPSAccuracyException: When GPS accuracy exceeds 100m threshold (HTTP 422).
    """
    settings = get_settings()

    # Step 1: GPS accuracy validation
    if accuracy > 100:
        raise GPSAccuracyException("GPS accuracy insufficient")

    # Step 2: Find nearby places within geofence radius
    nearby = await get_nearby_places(
        db=db,
        lat=lat,
        lon=lon,
        radius_m=settings.geofence_radius_m,
    )

    nearby_place_infos: list[dict[str, Any]] = []
    confirmed_visits: list[dict[str, Any]] = []
    nearby_place_ids: set[int] = set()

    # Step 3: Process each nearby place
    for place_data in nearby:
        place_id = place_data["id"]
        nearby_place_ids.add(place_id)

        nearby_place_infos.append({
            "place_id": place_id,
            "name": place_data["name"],
            "distance_m": place_data.get("distance_m", 0.0),
        })

        # Get or create UserPresence -- wrapped in try/except so that
        # transient Redis failures do not cause unhandled 500 errors.
        try:
            presence = await get_user_presence(user_id, place_id)
        except AppException:
            logger.warning(
                "Redis unavailable when reading presence: user=%d place=%d; skipping tracking",
                user_id,
                place_id,
            )
            continue

        if presence is None:
            # First sighting: create new presence
            presence_data = {
                "first_seen": timestamp.isoformat(),
                "last_seen": timestamp.isoformat(),
                "reading_count": 1,
                "consecutive_misses": 0,
            }
            try:
                await set_user_presence(user_id, place_id, presence_data)
            except AppException:
                logger.warning(
                    "Redis unavailable when creating presence: user=%d place=%d; skipping",
                    user_id,
                    place_id,
                )
        else:
            # Update existing presence
            presence["last_seen"] = timestamp.isoformat()
            presence["reading_count"] = presence.get("reading_count", 0) + 1
            presence["consecutive_misses"] = 0

            # Step 4: Check auto-confirm conditions
            first_seen = datetime.datetime.fromisoformat(presence["first_seen"])
            last_seen = datetime.datetime.fromisoformat(presence["last_seen"])
            dwell_seconds = (last_seen - first_seen).total_seconds()
            reading_count = presence["reading_count"]

            if (
                dwell_seconds >= settings.visit_min_duration_seconds
                and reading_count >= settings.visit_min_readings
            ):
                # Auto-confirm visit
                confirmed = await auto_confirm_visit(
                    db=db,
                    user_id=user_id,
                    place_id=place_id,
                    first_seen=first_seen,
                    last_seen=last_seen,
                    dwell_seconds=int(dwell_seconds),
                )
                if confirmed is not None:
                    confirmed_visits.append(confirmed)
            else:
                # Update presence in Redis (not yet confirmed)
                try:
                    await set_user_presence(user_id, place_id, presence)
                except AppException:
                    logger.warning(
                        "Redis unavailable when updating presence: user=%d place=%d; skipping",
                        user_id,
                        place_id,
                    )

    # Step 5: Handle out-of-range tracking for previously tracked places
    await _handle_out_of_range(user_id, nearby_place_ids)

    return {
        "nearby_places": nearby_place_infos,
        "confirmed_visits": confirmed_visits,
        "rejected": False,
        "rejection_reason": None,
    }


async def auto_confirm_visit(
    db: AsyncSession,
    user_id: int,
    place_id: int,
    first_seen: datetime.datetime,
    last_seen: datetime.datetime,
    dwell_seconds: int,
) -> Optional[dict[str, Any]]:
    """Create a Visit record in DB and delete UserPresence from Redis.

    Checks for duplicate visits before creating: if a Visit already exists
    for the same user+place within the last 2 hours, no new Visit is created.

    Args:
        db: Async database session.
        user_id: User ID.
        place_id: Place ID.
        first_seen: When the user was first detected near the place.
        last_seen: When the user was last detected near the place.
        dwell_seconds: Total dwell time in seconds.

    Returns:
        Dict with visit_id, place_id, duration_seconds if created, None if
        duplicate.
    """
    # Check for duplicate visits in the current session window
    cutoff = last_seen - datetime.timedelta(seconds=DUPLICATE_VISIT_WINDOW_SECONDS)
    stmt = (
        select(Visit)
        .where(Visit.user_id == user_id)
        .where(Visit.place_id == place_id)
        .where(Visit.started_at >= cutoff)
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing is not None:
        # Duplicate visit: delete presence but do not create new visit
        try:
            await delete_user_presence(user_id, place_id)
        except AppException:
            logger.warning(
                "Redis unavailable when deleting duplicate presence: user=%d place=%d",
                user_id,
                place_id,
            )
        return None

    # Look up the area containing this place via PostGIS ST_Contains.
    # Both Area.boundary (Geography POLYGON) and Place.coordinates
    # (Geography POINT) must be cast to Geometry for ST_Contains.
    # The Place.coordinates column is referenced as a subquery to keep
    # the spatial operation entirely in SQL (avoids Python-side WKB binding).
    place_point = (
        select(cast(Place.coordinates, Geometry))
        .where(Place.id == place_id)
        .correlate(None)
        .scalar_subquery()
    )
    area_stmt = (
        select(Area.id)
        .where(ST_Contains(cast(Area.boundary, Geometry), place_point))
        .limit(1)
    )
    area_result = await db.execute(area_stmt)
    area_id = area_result.scalar_one_or_none()

    # Create the Visit record
    visit = Visit(
        user_id=user_id,
        place_id=place_id,
        area_id=area_id,
        started_at=first_seen,
        ended_at=last_seen,
        duration_seconds=dwell_seconds,
    )
    db.add(visit)
    await db.flush()
    await db.commit()

    # Delete UserPresence from Redis (best-effort: TTL will expire it if this fails)
    try:
        await delete_user_presence(user_id, place_id)
    except AppException:
        logger.warning(
            "Redis unavailable when deleting presence after confirm: user=%d place=%d",
            user_id,
            place_id,
        )

    logger.info(
        "Visit confirmed: user=%d place=%d duration=%ds",
        user_id,
        place_id,
        dwell_seconds,
    )

    return {
        "visit_id": visit.id,
        "place_id": place_id,
        "duration_seconds": dwell_seconds,
    }


async def get_visit_history(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Retrieve paginated visit history for a user with place details.

    Joins the Visit table with Place to include the place_name in the
    response without requiring a separate query.

    Args:
        db: Async database session.
        user_id: User ID whose visits to retrieve.
        limit: Maximum number of results (default 20).
        offset: Number of results to skip (default 0).

    Returns:
        List of visit dicts with id, place_id, place_name, area_id,
        started_at, ended_at, duration_seconds.
    """
    stmt = (
        select(Visit, Place.name.label("place_name"))
        .join(Place, Visit.place_id == Place.id)
        .where(Visit.user_id == user_id)
        .order_by(Visit.started_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    rows = result.all()

    visits = []
    for row in rows:
        visit = row[0]
        place_name = row[1]
        visits.append({
            "id": visit.id,
            "place_id": visit.place_id,
            "place_name": place_name,
            "area_id": visit.area_id,
            "started_at": visit.started_at,
            "ended_at": visit.ended_at,
            "duration_seconds": visit.duration_seconds,
        })

    return visits


async def _handle_out_of_range(
    user_id: int,
    current_nearby_place_ids: set[int],
) -> None:
    """Track out-of-range pings for previously tracked places.

    For each place the user was previously tracking (has a UserPresence key)
    that is NOT in the current nearby set, increment consecutive_misses.
    After OUT_OF_RANGE_THRESHOLD consecutive misses, delete the
    UserPresence (GPS jitter protection).

    This function scans Redis for all presence keys belonging to the user.
    """
    try:
        client = await get_redis_client()
        # Scan for all presence keys for this user
        prefix = f"presence:{user_id}:"
        keys = []
        async for key in client.scan_iter(match=f"{prefix}*"):
            keys.append(key)

        for key in keys:
            # Extract place_id from key: "presence:{user_id}:{place_id}"
            parts = key.split(":")
            if len(parts) != 3:
                continue
            try:
                place_id = int(parts[2])
            except (ValueError, IndexError):
                continue

            if place_id not in current_nearby_place_ids:
                # User is out of range for this place
                raw = await client.get(key)
                if raw is None:
                    continue

                presence = json.loads(raw)
                misses = presence.get("consecutive_misses", 0) + 1

                if misses >= OUT_OF_RANGE_THRESHOLD:
                    # Clear presence after N consecutive misses
                    await delete_user_presence(user_id, place_id)
                    logger.info(
                        "UserPresence cleared after %d consecutive out-of-range pings: "
                        "user=%d place=%d",
                        misses,
                        user_id,
                        place_id,
                    )
                else:
                    # Update consecutive misses count
                    presence["consecutive_misses"] = misses
                    await set_user_presence(user_id, place_id, presence)
    except Exception:
        logger.exception("Error handling out-of-range tracking for user=%d", user_id)
