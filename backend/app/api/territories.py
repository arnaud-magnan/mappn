"""Territories API router.

Provides endpoints for:
- GET /game/territories/nearby: Territories within a radius of given coordinates
- GET /game/territories/{id}: Single territory detail with familiarity data
- POST /game/territories/{id}/claim: Claim an unclaimed territory
- POST /game/territories/{id}/challenge: Challenge a PvP territory chief
- POST /game/territories/{id}/contribute: Contribute to a cooperative territory

All endpoints require authentication via JWT Bearer token.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import EntityNotFoundException
from app.models.user import User
from app.schemas.territory import (
    ChallengeResult,
    ChallengeTerritoryRequest,
    ClaimTerritoryRequest,
    ContributeRequest,
    ResidentResponse,
    TerritoryResponse,
)
from app.services.territory_service import (
    challenge_territory,
    claim_home,
    claim_territory,
    contribute_to_territory,
    get_nearby_territories,
    get_residents,
    get_territory_detail,
)

router = APIRouter(prefix="/game/territories", tags=["territories"])


@router.get("/nearby", response_model=list[TerritoryResponse])
async def nearby_territories(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
    radius_m: float = Query(default=5000, ge=0, le=50000, description="Search radius in meters"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Find territories within a radius of the given coordinates.

    Uses PostGIS ST_DWithin for meter-accurate spatial queries on area
    boundaries.

    Query Parameters:
        lat: Latitude of the search center.
        lon: Longitude of the search center.
        radius_m: Search radius in meters (default 5000, max 50000).
    """
    result = await get_nearby_territories(
        db=db,
        lat=lat,
        lon=lon,
        radius_m=radius_m,
    )
    return result


@router.get("/{territory_id}", response_model=TerritoryResponse)
async def territory_detail(
    territory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get detailed territory information with the user's familiarity score.

    Returns zone type, owner, chief creature, passive reward rate,
    familiarity scores, and familiarity rankings.

    Raises:
        EntityNotFoundException: If the territory does not exist.
    """
    result = await get_territory_detail(
        db=db,
        territory_id=territory_id,
        user_id=current_user.id,
    )
    if result is None:
        raise EntityNotFoundException("Territory not found")
    return result


@router.post("/{territory_id}/claim", response_model=TerritoryResponse)
async def claim_territory_endpoint(
    territory_id: int,
    body: ClaimTerritoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Claim an unclaimed territory by assigning a creature as chief.

    Requires at least one prior visit to the territory's area.

    Raises:
        EntityNotFoundException: If the territory or creature is not found.
        TerritoryClaimDeniedException: If claim prerequisites are not met.
    """
    result = await claim_territory(
        db=db,
        user_id=current_user.id,
        territory_id=territory_id,
        creature_id=body.creature_id,
    )
    return result


@router.post("/{territory_id}/challenge", response_model=ChallengeResult)
async def challenge_territory_endpoint(
    territory_id: int,
    body: ChallengeTerritoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Challenge the current chief of a PvP territory.

    Uses SELECT FOR UPDATE to prevent race conditions. Computes effective
    power for both attacker and defender, with the defender receiving a
    familiarity bonus.

    Raises:
        EntityNotFoundException: If territory or creatures not found.
        TerritoryChallengeDeniedException: If not a PvP zone or other rules.
    """
    result = await challenge_territory(
        db=db,
        user_id=current_user.id,
        territory_id=territory_id,
        attacker_creature_id=body.attacker_creature_id,
    )
    return result


@router.post("/{territory_id}/contribute", response_model=TerritoryResponse)
async def contribute_territory_endpoint(
    territory_id: int,
    body: ContributeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Contribute a creature to a cooperative territory.

    Cooperative zones allow multiple players to assign creatures for
    pooled rewards.

    Raises:
        EntityNotFoundException: If territory or creature not found.
        TerritoryContributionDeniedException: If not a cooperative zone
            or no prior visit.
    """
    result = await contribute_to_territory(
        db=db,
        user_id=current_user.id,
        territory_id=territory_id,
        creature_id=body.creature_id,
    )
    return result


@router.post("/{territory_id}/claim-home", response_model=TerritoryResponse)
async def claim_home_endpoint(
    territory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Claim a personal hex territory as the user's home.

    Only personal zone territories can be claimed. Multiple users can
    share the same hex. A 24-hour cooldown applies when relocating.
    """
    await claim_home(db=db, user_id=current_user.id, territory_id=territory_id)
    result = await get_territory_detail(
        db=db, territory_id=territory_id, user_id=current_user.id,
    )
    if result is None:
        raise EntityNotFoundException("Territory not found")
    return result


@router.get("/{territory_id}/residents", response_model=list[ResidentResponse])
async def get_residents_endpoint(
    territory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List all users who have claimed this personal hex as home."""
    return await get_residents(db=db, territory_id=territory_id)
