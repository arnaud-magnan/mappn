"""Places service for spatial queries and busyness data.

Provides PostGIS-backed nearby places search using ST_DWithin with Geography
type for meter-accurate distance calculations, place detail retrieval, and
busyness data staleness detection.

All spatial queries use the Geography type (SRID 4326) which measures
distances in meters automatically, avoiding manual unit conversion.
"""

from __future__ import annotations

import datetime
from typing import Any, Optional

from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_X, ST_Y
from geoalchemy2.types import Geography, Geometry
from sqlalchemy import cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.place import Place

# Busyness data is considered stale after 7 days
STALENESS_THRESHOLD_DAYS = 7


def _is_busyness_stale(busyness_updated_at: Optional[datetime.datetime]) -> bool:
    """Check whether busyness data is stale (older than 7 days).

    Returns True if:
    - busyness_updated_at is None (no data ever collected)
    - busyness_updated_at is older than STALENESS_THRESHOLD_DAYS

    Returns False if busyness data was updated within the threshold.
    """
    if busyness_updated_at is None:
        return False
    now = datetime.datetime.now(datetime.timezone.utc)
    threshold = now - datetime.timedelta(days=STALENESS_THRESHOLD_DAYS)
    return busyness_updated_at < threshold


def _extract_current_busyness(busyness_data: Optional[dict]) -> Optional[int]:
    """Extract current_popularity from busyness_data JSONB.

    Returns None if busyness_data is None or does not contain
    current_popularity.
    """
    if busyness_data is None:
        return None
    return busyness_data.get("current_popularity")


async def get_nearby_places(
    db: AsyncSession,
    lat: float,
    lon: float,
    radius_m: float = 500,
    category: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Find places within a given radius from the user's coordinates.

    Uses PostGIS ST_DWithin with Geography type for meter-accurate distance
    calculations. Results are ordered by distance from the user's location.

    Args:
        db: Async database session.
        lat: Latitude of the search center.
        lon: Longitude of the search center.
        radius_m: Search radius in meters (default 500).
        category: Optional category filter (e.g., "restaurant").

    Returns:
        List of place dicts with id, name, category, lat, lon, address,
        current_busyness, busyness_stale, busyness_updated_at fields.
    """
    user_point = cast(ST_MakePoint(lon, lat), Geography)

    # Cast Geography to Geometry for ST_X/ST_Y coordinate extraction
    geom_coords = cast(Place.coordinates, Geometry)

    # Build base query with ST_DWithin filter and distance ordering
    stmt = (
        select(
            Place,
            ST_X(geom_coords).label("lon"),
            ST_Y(geom_coords).label("lat"),
            ST_Distance(Place.coordinates, user_point).label("distance_m"),
        )
        .where(ST_DWithin(Place.coordinates, user_point, radius_m))
        .order_by(ST_Distance(Place.coordinates, user_point))
    )

    # Add optional category filter
    if category is not None:
        stmt = stmt.where(Place.category == category)

    result = await db.execute(stmt)
    rows = result.all()

    places = []
    for row in rows:
        place = row[0]
        place_lon = row[1]
        place_lat = row[2]
        distance_m = row[3]

        places.append(
            {
                "id": place.id,
                "name": place.name,
                "category": place.category,
                "lat": place_lat,
                "lon": place_lon,
                "address": place.address,
                "current_busyness": _extract_current_busyness(place.busyness_data),
                "busyness_stale": _is_busyness_stale(place.busyness_updated_at),
                "busyness_updated_at": place.busyness_updated_at,
                "distance_m": distance_m,
            }
        )

    return places


async def get_place_detail(
    db: AsyncSession,
    place_id: int,
) -> Optional[dict[str, Any]]:
    """Retrieve full place detail including busyness data.

    Args:
        db: Async database session.
        place_id: Primary key of the place to retrieve.

    Returns:
        Place dict with full detail including busyness_data, or None if
        the place does not exist.
    """
    # Cast Geography to Geometry for ST_X/ST_Y coordinate extraction
    geom_coords = cast(Place.coordinates, Geometry)

    stmt = select(
        Place,
        ST_X(geom_coords).label("lon"),
        ST_Y(geom_coords).label("lat"),
    ).where(Place.id == place_id)

    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        return None

    place = row[0]
    place_lon = row[1]
    place_lat = row[2]

    return {
        "id": place.id,
        "name": place.name,
        "category": place.category,
        "lat": place_lat,
        "lon": place_lon,
        "address": place.address,
        "city": place.city,
        "country": place.country,
        "busyness_data": place.busyness_data,
        "busyness_updated_at": place.busyness_updated_at,
        "busyness_stale": _is_busyness_stale(place.busyness_updated_at),
    }
