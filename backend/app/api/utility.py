"""Utility API router.

Provides endpoints for:
- GET /users/me/stats: Aggregate visit statistics for the current user
- GET /users/me/achievements: Themed achievements with progress tracking
- GET /journal: Paginated travel journal entries
- POST /journal/{visit_id}/note: Create or update a journal note
- GET /explore/heatmap: Exploration heatmap with area visited status
- GET /passports: City passport with neighborhood stamps

All endpoints require authentication via JWT Bearer token.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.utility import (
    AchievementResponse,
    CityPassportResponse,
    HeatmapResponse,
    JournalEntryResponse,
    JournalNoteRequest,
    UserStatsResponse,
)
from app.services.utility_service import (
    add_journal_note,
    get_city_passport,
    get_heatmap,
    get_journal_entries,
    get_user_achievements,
    get_user_stats,
)

router = APIRouter(tags=["utility"])


@router.get("/users/me/stats", response_model=UserStatsResponse)
async def user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get aggregate visit statistics for the current user.

    Returns total places visited, cities explored, countries reached,
    and total visit duration.
    """
    result = await get_user_stats(db=db, user_id=current_user.id)
    return result


@router.get("/users/me/achievements", response_model=list[AchievementResponse])
async def user_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Get all 6 themed achievements with current progress for the user.

    Returns achievements across 3 categories (Explorer, Habits, Categories),
    each showing name, description, current progress count, required
    threshold, and earned status.
    """
    result = await get_user_achievements(db=db, user_id=current_user.id)
    return result


@router.get("/journal", response_model=list[JournalEntryResponse])
async def journal_entries(
    limit: int = Query(default=20, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(default=0, ge=0, description="Number of entries to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Get paginated travel journal entries for the current user.

    Returns visits ordered by most recent first, each including
    place name, visit timing, and optional journal note and photo.

    Query Parameters:
        limit: Maximum number of entries (default 20, max 100).
        offset: Number of entries to skip (default 0).
    """
    result = await get_journal_entries(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return result


@router.post("/journal/{visit_id}/note", response_model=JournalEntryResponse)
async def create_journal_note(
    visit_id: int,
    body: JournalNoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create or update a journal note for a visit.

    Performs an upsert: if a note already exists for the visit, it is
    updated; otherwise a new note is created.

    Raises:
        EntityNotFoundException: If the visit does not exist or does not
            belong to the current user.
    """
    result = await add_journal_note(
        db=db,
        user_id=current_user.id,
        visit_id=visit_id,
        text=body.text,
        photo_url=body.photo_url,
    )
    return result


@router.get("/explore/heatmap", response_model=HeatmapResponse)
async def exploration_heatmap(
    city: str | None = Query(default=None, description="Optional city filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get the exploration heatmap for the current user.

    Returns all areas (optionally filtered by city) with visited status,
    GeoJSON boundaries for map rendering, and exploration percentage.

    Query Parameters:
        city: Optional city filter. When omitted, returns all areas.
    """
    result = await get_heatmap(
        db=db,
        user_id=current_user.id,
        city=city,
    )
    return result


@router.get("/passports", response_model=CityPassportResponse)
async def city_passport(
    city: str = Query(..., description="City to generate passport for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get city passport with neighborhood stamps.

    Returns all neighborhoods in the specified city, showing which ones
    the user has visited (stamped), a progress bar, and whether the
    city completion badge has been earned.

    Query Parameters:
        city: Required city name to generate passport for.
    """
    result = await get_city_passport(
        db=db,
        user_id=current_user.id,
        city=city,
    )
    return result
