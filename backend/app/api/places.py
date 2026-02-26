"""Places API router.

Provides endpoints for:
- GET /places/nearby: Search for places within a radius of given coordinates
- GET /places/{id}: Get full place detail including busyness data
- GET /places/{id}/forecast: Get predicted busyness for a specific day and hour

All endpoints require authentication via JWT Bearer token.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import EntityNotFoundException
from app.models.user import User
from app.schemas.place import (
    ForecastResponse,
    NearbyQueryParams,
    PlaceDetailResponse,
    PlaceResponse,
)
from app.services.forecast_service import predict_busyness
from app.services.places_service import (
    _is_busyness_stale,
    get_nearby_places,
    get_place_detail,
)

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/nearby", response_model=list[PlaceResponse])
async def nearby_places(
    params: NearbyQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Search for places within a radius of the given coordinates.

    Returns places ordered by distance from the search center, each
    including current busyness level and staleness indicator.

    Query Parameters:
        lat: Latitude of the search center.
        lon: Longitude of the search center.
        radius_m: Search radius in meters (default 500).
        category: Optional category filter (e.g., "restaurant").
    """
    results = await get_nearby_places(
        db=db,
        lat=params.lat,
        lon=params.lon,
        radius_m=params.radius_m,
        category=params.category,
    )
    return results


@router.get("/{place_id}", response_model=PlaceDetailResponse)
async def place_detail(
    place_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get full place detail including busyness data.

    Returns the complete place information with busyness_data containing
    popular_times histogram and current_popularity. Returns busyness fields
    as null when no busyness data exists (no error).

    Raises:
        EntityNotFoundException: If the place does not exist.
    """
    result = await get_place_detail(db=db, place_id=place_id)
    if result is None:
        raise EntityNotFoundException("Place not found")
    return result


@router.get("/{place_id}/forecast", response_model=ForecastResponse)
async def place_forecast(
    place_id: int,
    day: int = Query(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)"),
    hour: int = Query(..., ge=0, le=23, description="Hour of day (0-23)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get predicted busyness for a specific day and hour.

    Looks up the predicted busyness value from the place's popular_times
    histogram data.

    Query Parameters:
        day: Day of week (0=Monday, 6=Sunday).
        hour: Hour of day (0-23).

    Raises:
        EntityNotFoundException: If the place does not exist or has no busyness data.
    """
    result = await get_place_detail(db=db, place_id=place_id)
    if result is None:
        raise EntityNotFoundException("Place not found")

    predicted = predict_busyness(
        busyness_data=result.get("busyness_data"),
        day=day,
        hour=hour,
    )

    if predicted is None:
        raise EntityNotFoundException("No busyness data available for forecast")

    return {
        "place_id": place_id,
        "day": day,
        "hour": hour,
        "predicted_busyness": predicted,
        "data_stale": _is_busyness_stale(result.get("busyness_updated_at")),
    }
