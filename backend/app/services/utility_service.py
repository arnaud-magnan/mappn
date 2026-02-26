"""Utility service functions for stats, achievements, journal, heatmap, and passports.

Provides six async service functions that implement the business logic for the
utility app's exploration and gamification features. Each function queries the
database using async SQLAlchemy and returns structured dicts consumed by the
API router.

Functions:
    get_user_stats: Aggregate visit statistics (distinct places, cities, countries).
    get_user_achievements: Six themed achievements with progress tracking.
    get_journal_entries: Paginated visit journal with optional user notes.
    add_journal_note: Create or update a journal note for a visit.
    get_heatmap: Area exploration map with visited status and GeoJSON boundaries.
    get_city_passport: City-specific neighborhood stamps and completion badge.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from geoalchemy2.functions import ST_AsGeoJSON
from sqlalchemy import cast, distinct, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.exceptions import EntityNotFoundException
from app.models.area import Area
from app.models.journal import JournalNote
from app.models.place import Place
from app.models.visit import Visit

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Achievement definitions
# ---------------------------------------------------------------------------

ACHIEVEMENT_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "wanderer",
        "name": "Wanderer",
        "description": "Visit 10 distinct neighborhoods",
        "category": "explorer",
        "threshold": 10,
    },
    {
        "id": "globe_trotter",
        "name": "Globe Trotter",
        "description": "Visit places in 5 distinct cities",
        "category": "explorer",
        "threshold": 5,
    },
    {
        "id": "night_owl",
        "name": "Night Owl",
        "description": "Visit 10 places after midnight",
        "category": "habits",
        "threshold": 10,
    },
    {
        "id": "early_bird",
        "name": "Early Bird",
        "description": "Visit 10 places before 7am",
        "category": "habits",
        "threshold": 10,
    },
    {
        "id": "foodie",
        "name": "Foodie",
        "description": "Visit 50 restaurants",
        "category": "categories",
        "threshold": 50,
    },
    {
        "id": "culture_vulture",
        "name": "Culture Vulture",
        "description": "Visit 20 museums",
        "category": "categories",
        "threshold": 20,
    },
]


# ---------------------------------------------------------------------------
# get_user_stats
# ---------------------------------------------------------------------------


async def get_user_stats(
    db: AsyncSession,
    user_id: int,
) -> dict[str, Any]:
    """Return aggregate visit statistics for a user.

    Queries Visit JOIN Place to compute:
    - places_count: number of distinct places visited
    - cities_count: number of distinct cities visited (excludes NULL)
    - countries_count: number of distinct countries visited (excludes NULL)
    - total_duration_seconds: sum of all visit durations

    Args:
        db: Async database session.
        user_id: The user's ID.

    Returns:
        Dict with places_count, cities_count, countries_count,
        total_duration_seconds.
    """
    stmt = (
        select(
            func.count(distinct(Visit.place_id)).label("places_count"),
            func.count(distinct(Place.city)).label("cities_count"),
            func.count(distinct(Place.country)).label("countries_count"),
            func.coalesce(func.sum(Visit.duration_seconds), 0).label("total_duration_seconds"),
        )
        .join(Place, Visit.place_id == Place.id)
        .where(Visit.user_id == user_id)
    )

    result = await db.execute(stmt)
    row = result.one()

    return {
        "places_count": row.places_count,
        "cities_count": row.cities_count,
        "countries_count": row.countries_count,
        "total_duration_seconds": row.total_duration_seconds,
    }


# ---------------------------------------------------------------------------
# get_user_achievements
# ---------------------------------------------------------------------------


async def get_user_achievements(
    db: AsyncSession,
    user_id: int,
) -> list[dict[str, Any]]:
    """Return all 6 achievements with current progress for a user.

    Achievement criteria:
    - Wanderer: 10 distinct area_ids in visits
    - Globe Trotter: 5 distinct cities in visited places
    - Night Owl: 10 visits started after midnight (hour 0-3)
    - Early Bird: 10 visits started before 7am (hour < 7)
    - Foodie: 50 visits to restaurant places
    - Culture Vulture: 20 visits to museum places

    Args:
        db: Async database session.
        user_id: The user's ID.

    Returns:
        List of 6 achievement dicts, each with id, name, description,
        category, progress, threshold, earned, earned_at.
    """
    # Compute all progress counts in parallel queries for clarity

    # Wanderer: distinct area_ids (excluding NULL)
    wanderer_stmt = (
        select(func.count(distinct(Visit.area_id)))
        .where(Visit.user_id == user_id)
        .where(Visit.area_id.isnot(None))
    )
    wanderer_result = await db.execute(wanderer_stmt)
    wanderer_progress = wanderer_result.scalar_one()

    # Globe Trotter: distinct cities from visited places
    globe_stmt = (
        select(func.count(distinct(Place.city)))
        .join(Visit, Visit.place_id == Place.id)
        .where(Visit.user_id == user_id)
        .where(Place.city.isnot(None))
    )
    globe_result = await db.execute(globe_stmt)
    globe_progress = globe_result.scalar_one()

    # Night Owl: visits started between midnight and 4am (hour 0, 1, 2, 3)
    night_owl_stmt = (
        select(func.count())
        .select_from(Visit)
        .where(Visit.user_id == user_id)
        .where(extract("hour", Visit.started_at) < 4)
    )
    night_owl_result = await db.execute(night_owl_stmt)
    night_owl_progress = night_owl_result.scalar_one()

    # Early Bird: visits started before 7am (hour < 7)
    early_bird_stmt = (
        select(func.count())
        .select_from(Visit)
        .where(Visit.user_id == user_id)
        .where(extract("hour", Visit.started_at) < 7)
    )
    early_bird_result = await db.execute(early_bird_stmt)
    early_bird_progress = early_bird_result.scalar_one()

    # Foodie: visits to restaurants
    foodie_stmt = (
        select(func.count())
        .select_from(Visit)
        .join(Place, Visit.place_id == Place.id)
        .where(Visit.user_id == user_id)
        .where(Place.category == "restaurant")
    )
    foodie_result = await db.execute(foodie_stmt)
    foodie_progress = foodie_result.scalar_one()

    # Culture Vulture: visits to museums
    culture_stmt = (
        select(func.count())
        .select_from(Visit)
        .join(Place, Visit.place_id == Place.id)
        .where(Visit.user_id == user_id)
        .where(Place.category == "museum")
    )
    culture_result = await db.execute(culture_stmt)
    culture_progress = culture_result.scalar_one()

    # Get the earliest visit started_at for earned_at computation
    # (the visit that tipped the threshold)
    progress_map: dict[str, int] = {
        "wanderer": wanderer_progress,
        "globe_trotter": globe_progress,
        "night_owl": night_owl_progress,
        "early_bird": early_bird_progress,
        "foodie": foodie_progress,
        "culture_vulture": culture_progress,
    }

    # For earned_at, use the most recent visit timestamp as a proxy
    # (the visit that tipped the achievement over the threshold).
    # We use the latest visit started_at for the user if earned.
    latest_visit_stmt = (
        select(func.max(Visit.started_at))
        .where(Visit.user_id == user_id)
    )
    latest_visit_result = await db.execute(latest_visit_stmt)
    latest_visit_at = latest_visit_result.scalar_one_or_none()

    achievements = []
    for defn in ACHIEVEMENT_DEFINITIONS:
        ach_id = defn["id"]
        progress = progress_map[ach_id]
        threshold = defn["threshold"]
        earned = progress >= threshold

        achievements.append({
            "id": ach_id,
            "name": defn["name"],
            "description": defn["description"],
            "category": defn["category"],
            "progress": progress,
            "threshold": threshold,
            "earned": earned,
            "earned_at": latest_visit_at if earned else None,
        })

    return achievements


# ---------------------------------------------------------------------------
# get_journal_entries
# ---------------------------------------------------------------------------


async def get_journal_entries(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Return paginated journal entries for a user.

    Joins Visit with Place and LEFT JOINs JournalNote to include optional
    user-authored notes and photos. Results are ordered by started_at
    descending (most recent first).

    Args:
        db: Async database session.
        user_id: The user's ID.
        limit: Maximum number of entries to return (default 20).
        offset: Number of entries to skip (default 0).

    Returns:
        List of journal entry dicts with visit_id, place_id, place_name,
        area_id, city, started_at, duration_seconds, note, photo_url.
    """
    stmt = (
        select(
            Visit.id.label("visit_id"),
            Visit.place_id,
            Place.name.label("place_name"),
            Visit.area_id,
            Place.city,
            Visit.started_at,
            Visit.duration_seconds,
            JournalNote.text.label("note"),
            JournalNote.photo_url,
        )
        .join(Place, Visit.place_id == Place.id)
        .outerjoin(
            JournalNote,
            (JournalNote.visit_id == Visit.id) & (JournalNote.user_id == user_id),
        )
        .where(Visit.user_id == user_id)
        .order_by(Visit.started_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    rows = result.all()

    entries = []
    for row in rows:
        entries.append({
            "visit_id": row.visit_id,
            "place_id": row.place_id,
            "place_name": row.place_name,
            "area_id": row.area_id,
            "city": row.city,
            "started_at": row.started_at,
            "duration_seconds": row.duration_seconds,
            "note": row.note,
            "photo_url": row.photo_url,
        })

    return entries


# ---------------------------------------------------------------------------
# add_journal_note
# ---------------------------------------------------------------------------


async def add_journal_note(
    db: AsyncSession,
    user_id: int,
    visit_id: int,
    text: Optional[str],
    photo_url: Optional[str],
) -> dict[str, Any]:
    """Create or update a journal note for a visit.

    Performs an upsert: if a JournalNote already exists for the given
    visit_id + user_id combination, it updates the text and photo_url;
    otherwise it creates a new record.

    After upserting, returns the full journal entry (visit + place + note).

    Args:
        db: Async database session.
        user_id: The user's ID.
        visit_id: The visit to attach the note to.
        text: Optional note text (max 1000 characters).
        photo_url: Optional URL/path to a photo.

    Returns:
        Journal entry dict with visit_id, place_id, place_name, area_id,
        city, started_at, duration_seconds, note, photo_url.

    Raises:
        EntityNotFoundException: When the visit_id does not exist or
            does not belong to the user.
    """
    # Verify the visit exists and belongs to this user
    visit_stmt = (
        select(Visit)
        .where(Visit.id == visit_id)
        .where(Visit.user_id == user_id)
    )
    visit_result = await db.execute(visit_stmt)
    visit = visit_result.scalars().first()

    if visit is None:
        raise EntityNotFoundException("Visit not found")

    # Check for existing journal note (upsert)
    note_stmt = (
        select(JournalNote)
        .where(JournalNote.visit_id == visit_id)
        .where(JournalNote.user_id == user_id)
    )
    note_result = await db.execute(note_stmt)
    existing_note = note_result.scalars().first()

    if existing_note is not None:
        # Update existing note
        existing_note.text = text
        existing_note.photo_url = photo_url
        db.add(existing_note)
    else:
        # Create new note
        new_note = JournalNote(
            visit_id=visit_id,
            user_id=user_id,
            text=text,
            photo_url=photo_url,
        )
        db.add(new_note)

    await db.flush()

    # Fetch the full journal entry to return
    entry_stmt = (
        select(
            Visit.id.label("visit_id"),
            Visit.place_id,
            Place.name.label("place_name"),
            Visit.area_id,
            Place.city,
            Visit.started_at,
            Visit.duration_seconds,
        )
        .join(Place, Visit.place_id == Place.id)
        .where(Visit.id == visit_id)
    )
    entry_result = await db.execute(entry_stmt)
    entry_row = entry_result.one()

    return {
        "visit_id": entry_row.visit_id,
        "place_id": entry_row.place_id,
        "place_name": entry_row.place_name,
        "area_id": entry_row.area_id,
        "city": entry_row.city,
        "started_at": entry_row.started_at,
        "duration_seconds": entry_row.duration_seconds,
        "note": text,
        "photo_url": photo_url,
    }


# ---------------------------------------------------------------------------
# get_heatmap
# ---------------------------------------------------------------------------


async def get_heatmap(
    db: AsyncSession,
    user_id: int,
    city: Optional[str] = None,
) -> dict[str, Any]:
    """Return exploration heatmap data for a user.

    Queries all areas (optionally filtered by city) and LEFT JOINs with
    the user's visits to determine which areas have been visited. Returns
    boundary GeoJSON via ST_AsGeoJSON for map rendering.

    Args:
        db: Async database session.
        user_id: The user's ID.
        city: Optional city filter. When None, returns all areas.

    Returns:
        Dict with areas (list of area dicts), total_areas, visited_areas,
        explored_pct.
    """
    # Subquery: distinct area_ids visited by this user
    visited_subquery = (
        select(
            Visit.area_id,
            func.min(Visit.started_at).label("visited_at"),
        )
        .where(Visit.user_id == user_id)
        .where(Visit.area_id.isnot(None))
        .group_by(Visit.area_id)
        .subquery()
    )

    # Main query: all areas LEFT JOIN visited subquery
    stmt = (
        select(
            Area.id,
            Area.name,
            Area.city,
            ST_AsGeoJSON(Area.boundary).label("boundary_geojson"),
            visited_subquery.c.visited_at,
        )
        .outerjoin(visited_subquery, Area.id == visited_subquery.c.area_id)
    )

    if city is not None:
        stmt = stmt.where(Area.city == city)

    stmt = stmt.order_by(Area.name)

    result = await db.execute(stmt)
    rows = result.all()

    areas = []
    visited_count = 0
    for row in rows:
        is_visited = row.visited_at is not None
        if is_visited:
            visited_count += 1

        # Parse boundary_geojson from string to dict
        boundary = row.boundary_geojson
        if isinstance(boundary, str):
            boundary = json.loads(boundary)

        areas.append({
            "id": row.id,
            "name": row.name,
            "city": row.city,
            "boundary_geojson": boundary,
            "visited": is_visited,
            "visited_at": row.visited_at,
        })

    total_areas = len(areas)
    explored_pct = (visited_count / total_areas * 100.0) if total_areas > 0 else 0.0

    return {
        "areas": areas,
        "total_areas": total_areas,
        "visited_areas": visited_count,
        "explored_pct": explored_pct,
    }


# ---------------------------------------------------------------------------
# get_city_passport
# ---------------------------------------------------------------------------


async def get_city_passport(
    db: AsyncSession,
    user_id: int,
    city: str,
) -> dict[str, Any]:
    """Return city passport data with neighborhood stamps.

    Queries all areas in the given city and LEFT JOINs with the user's
    visits to determine which neighborhoods have been stamped. The city
    badge is earned when all neighborhoods have been visited.

    Args:
        db: Async database session.
        user_id: The user's ID.
        city: The city to generate a passport for.

    Returns:
        Dict with city, total_neighborhoods, visited_count, stamps,
        badge_earned, explored_pct.
    """
    # Subquery: distinct area_ids visited by this user
    visited_subquery = (
        select(
            Visit.area_id,
            func.min(Visit.started_at).label("visited_at"),
        )
        .where(Visit.user_id == user_id)
        .where(Visit.area_id.isnot(None))
        .group_by(Visit.area_id)
        .subquery()
    )

    # All areas in the city LEFT JOIN visited subquery
    stmt = (
        select(
            Area.id.label("area_id"),
            Area.name,
            visited_subquery.c.visited_at,
        )
        .outerjoin(visited_subquery, Area.id == visited_subquery.c.area_id)
        .where(Area.city == city)
        .order_by(Area.name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    stamps = []
    visited_count = 0
    for row in rows:
        is_visited = row.visited_at is not None
        if is_visited:
            visited_count += 1
        stamps.append({
            "area_id": row.area_id,
            "name": row.name,
            "visited": is_visited,
            "visited_at": row.visited_at,
        })

    total_neighborhoods = len(stamps)
    badge_earned = total_neighborhoods > 0 and visited_count == total_neighborhoods
    explored_pct = (visited_count / total_neighborhoods * 100.0) if total_neighborhoods > 0 else 0.0

    return {
        "city": city,
        "total_neighborhoods": total_neighborhoods,
        "visited_count": visited_count,
        "stamps": stamps,
        "badge_earned": badge_earned,
        "explored_pct": explored_pct,
    }
