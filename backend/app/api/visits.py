"""Visits API router.

Provides endpoints for:
- POST /visits/ping: Process a GPS ping for visit tracking
- GET /visits/history: Get paginated visit history for the authenticated user

All endpoints require authentication via JWT Bearer token.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.visit import (
    GPSPingRequest,
    GPSPingResponse,
    VisitResponse,
)
from app.services.visit_service import get_visit_history, process_gps_ping

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("/ping", response_model=GPSPingResponse)
async def ping(
    body: GPSPingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Process a GPS ping for visit tracking.

    Validates GPS accuracy, finds nearby places within geofence radius,
    manages UserPresence state in Redis, and auto-confirms visits when
    dwell time and reading count thresholds are met.

    Returns:
        GPSPingResponse with nearby_places, confirmed_visits, and
        rejection status.
    """
    result = await process_gps_ping(
        db=db,
        user_id=current_user.id,
        lat=body.lat,
        lon=body.lon,
        accuracy=body.accuracy,
        timestamp=body.timestamp,
    )
    return result


@router.get("/history", response_model=list[VisitResponse])
async def history(
    limit: int = Query(default=20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Get paginated visit history for the authenticated user.

    Returns visits ordered by most recent first, with place_name,
    area_id, timestamps, and duration.

    Query Parameters:
        limit: Maximum number of results (default 20, max 100).
        offset: Number of results to skip (default 0).
    """
    visits = await get_visit_history(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return visits
