"""Territory request and response schemas.

Defines Pydantic models for the territory API contract:
- TerritoryResponse: Single territory with zone type, owner, and familiarity
- TerritoryListResponse: List of territories with total count
- ClaimTerritoryRequest: Request body for claiming a territory
- ChallengeTerritoryRequest: Request body for challenging a PvP territory
- ChallengeResult: Result of a PvP territory challenge
- ContributeRequest: Request body for contributing to a cooperative territory
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TerritoryResponse(BaseModel):
    """Single territory with zone type, owner, and familiarity data.

    Attributes:
        id: Territory primary key.
        area_id: FK to areas.id (the geographic area).
        owner_id: FK to users.id (current owner, nullable if unclaimed).
        owner_username: Display name of the territory owner (nullable).
        chief_creature_id: FK to creatures.id (assigned chief, nullable).
        zone_type: Zone classification (personal, cooperative, pvp, nullable).
        familiarity_scores: JSONB mapping user_id (string) to cumulative
            seconds spent in the area (nullable).
        familiar_score_for_user: The requesting user's familiarity score
            for this territory (nullable, computed by service layer).
        passive_reward_rate: Multiplier for hourly passive reward generation.
        familiarity_rankings: Ranked list of users by familiarity score
            (nullable, computed by service layer).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    area_id: int
    owner_id: Optional[int] = None
    owner_username: Optional[str] = None
    chief_creature_id: Optional[int] = None
    zone_type: Optional[str] = None
    familiarity_scores: Optional[dict[str, Any]] = None
    familiar_score_for_user: Optional[float] = None
    passive_reward_rate: float
    area_name: Optional[str] = None
    familiarity_rankings: Optional[list[dict[str, Any]]] = None


class TerritoryListResponse(BaseModel):
    """List of territories with total count.

    Attributes:
        territories: List of territory responses.
        total: Total number of territories matching the query.
    """

    model_config = ConfigDict(from_attributes=True)

    territories: list[TerritoryResponse]
    total: int


class ClaimTerritoryRequest(BaseModel):
    """Request body for claiming an unclaimed territory.

    Attributes:
        creature_id: The creature to assign as territory chief.
    """

    creature_id: int = Field(..., gt=0)


class ChallengeTerritoryRequest(BaseModel):
    """Request body for challenging a PvP territory.

    Attributes:
        attacker_creature_id: The creature to use as attacker.
    """

    attacker_creature_id: int = Field(..., gt=0)


class ChallengeResult(BaseModel):
    """Result of a PvP territory challenge.

    Attributes:
        winner: Who won the challenge ("attacker" or "defender").
        attacker_power: Total effective power of the attacker.
        defender_power: Total effective power of the defender.
        breakdown: Detailed power breakdown (base stats, item boosts,
            familiarity bonus, etc.).
    """

    model_config = ConfigDict(from_attributes=True)

    winner: str
    attacker_power: float
    defender_power: float
    breakdown: dict[str, Any]


class ResidentResponse(BaseModel):
    """A resident of a personal hex territory."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    home_claimed_at: Optional[str] = None


class ContributeRequest(BaseModel):
    """Request body for contributing a creature to a cooperative territory.

    Attributes:
        creature_id: The creature to contribute.
    """

    creature_id: int = Field(..., gt=0)
