"""Territory service for claiming, PvP challenges, and cooperative contributions.

Implements territory management with PostGIS spatial queries for nearby
territory discovery, claim validation with visit prerequisites, PvP challenge
resolution with row-level locking, familiarity bonus calculation, and
cooperative zone contribution.

PostGIS queries use the Geography type (SRID 4326) for meter-accurate
distance calculations. Territory challenges use SELECT FOR UPDATE to
prevent race conditions in concurrent PvP resolution.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Optional

from geoalchemy2.functions import ST_DWithin, ST_MakePoint
from geoalchemy2.types import Geography
from sqlalchemy import cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, EntityNotFoundException
from app.models.area import Area
from app.models.creature import Creature
from app.models.item import Item
from app.models.territory import Territory
from app.models.user import User
from app.models.visit import Visit

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class TerritoryClaimDeniedException(AppException):
    """Raised when a territory claim is denied (no prior visit, zone rules)."""

    status_code = 403
    error_type = "territory_claim_denied"
    message = "Territory claim denied"


class TerritoryChallengeDeniedException(AppException):
    """Raised when a territory challenge is denied (non-PvP zone, etc.)."""

    status_code = 403
    error_type = "territory_challenge_denied"
    message = "Territory challenge denied"


class TerritoryContributionDeniedException(AppException):
    """Raised when a territory contribution is denied (non-cooperative zone)."""

    status_code = 403
    error_type = "territory_contribution_denied"
    message = "Territory contribution denied"


class HomeClaimDeniedException(AppException):
    """Raised when a home claim is denied (wrong zone, cooldown, etc.)."""

    status_code = 403
    error_type = "home_claim_denied"
    message = "Home claim denied"


# ---------------------------------------------------------------------------
# Pure computation functions
# ---------------------------------------------------------------------------


def compute_familiarity_bonus(familiarity_score: float) -> float:
    """Compute the familiarity bonus from a raw score.

    The familiarity bonus is a percentage multiplier applied to a
    defender's effective power during PvP challenges. It rewards players
    who spend physical time in a territory's area.

    Formula: min(score / 1000, 0.5) -- caps at 50%.

    Args:
        familiarity_score: Cumulative seconds spent in the area.

    Returns:
        Bonus multiplier between 0.0 and 0.5 (inclusive).
    """
    return min(familiarity_score / 1000.0, 0.5)


def compute_effective_power(
    creature_power: int,
    creature_defense: int,
    creature_stamina: int,
    item_power_boost: int,
    item_defense_boost: int,
    item_stamina_boost: int,
    familiarity_bonus: float,
) -> float:
    """Compute total effective power for PvP comparison.

    Effective power = (base stats + item boosts) * (1 + familiarity_bonus).

    The familiarity bonus is applied as a percentage multiplier on the
    sum of base stats and item boosts. This means defenders with high
    familiarity get a significant advantage.

    Args:
        creature_power: Creature's current power stat.
        creature_defense: Creature's current defense stat.
        creature_stamina: Creature's current stamina stat.
        item_power_boost: Sum of power boosts from equipped items.
        item_defense_boost: Sum of defense boosts from equipped items.
        item_stamina_boost: Sum of stamina boosts from equipped items.
        familiarity_bonus: Familiarity bonus multiplier (0.0 to 0.5).

    Returns:
        Total effective power as a float.
    """
    base_total = (
        (creature_power + item_power_boost)
        + (creature_defense + item_defense_boost)
        + (creature_stamina + item_stamina_boost)
    )
    return base_total * (1.0 + familiarity_bonus)


# ---------------------------------------------------------------------------
# get_nearby_territories
# ---------------------------------------------------------------------------


async def get_nearby_territories(
    db: AsyncSession,
    lat: float,
    lon: float,
    radius_m: float = 5000,
) -> list[dict[str, Any]]:
    """Find territories whose area boundary is within a given radius.

    Uses PostGIS ST_DWithin with Geography type for meter-accurate distance
    calculations on the Area.boundary polygon. Joins Territory data to
    return zone type, owner, and passive reward rate.

    Args:
        db: Async database session.
        lat: Latitude of the search center.
        lon: Longitude of the search center.
        radius_m: Search radius in meters (default 5000).

    Returns:
        List of territory dicts with id, area_id, area_name, zone_type,
        owner_id, chief_creature_id, passive_reward_rate.
    """
    user_point = cast(ST_MakePoint(lon, lat), Geography)

    stmt = (
        select(Territory, Area.name.label("area_name"))
        .join(Area, Territory.area_id == Area.id)
        .where(ST_DWithin(Area.boundary, user_point, radius_m))
    )

    result = await db.execute(stmt)
    rows = result.all()

    territories = []
    for row in rows:
        territory = row[0]
        area_name = row[1]
        territories.append({
            "id": territory.id,
            "area_id": territory.area_id,
            "area_name": area_name,
            "zone_type": territory.zone_type,
            "owner_id": territory.owner_id,
            "chief_creature_id": territory.chief_creature_id,
            "passive_reward_rate": territory.passive_reward_rate,
            "familiarity_scores": territory.familiarity_scores or {},
        })

    return territories


# ---------------------------------------------------------------------------
# get_territory_detail
# ---------------------------------------------------------------------------


async def get_territory_detail(
    db: AsyncSession,
    territory_id: int,
    user_id: int,
) -> Optional[dict[str, Any]]:
    """Retrieve detailed territory information with user's familiarity score.

    Args:
        db: Async database session.
        territory_id: Primary key of the territory.
        user_id: The requesting user's ID (for familiarity lookup).

    Returns:
        Territory detail dict, or None if the territory does not exist.
    """
    stmt = (
        select(Territory, Area.name.label("area_name"), User.username.label("owner_username"))
        .join(Area, Territory.area_id == Area.id)
        .outerjoin(User, Territory.owner_id == User.id)
        .where(Territory.id == territory_id)
    )

    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        return None

    territory = row[0]
    area_name = row[1]
    owner_username = row[2]

    # Extract user's familiarity score from JSONB
    familiarity_scores = territory.familiarity_scores or {}
    user_score = familiarity_scores.get(str(user_id), 0)

    # Build familiarity rankings sorted by score descending
    rankings = sorted(
        [{"user_id": k, "score": v} for k, v in familiarity_scores.items()],
        key=lambda x: x["score"],
        reverse=True,
    )

    return {
        "id": territory.id,
        "area_id": territory.area_id,
        "area_name": area_name,
        "owner_id": territory.owner_id,
        "owner_username": owner_username,
        "chief_creature_id": territory.chief_creature_id,
        "zone_type": territory.zone_type,
        "familiarity_scores": familiarity_scores,
        "familiar_score_for_user": user_score,
        "passive_reward_rate": territory.passive_reward_rate,
        "familiarity_rankings": rankings,
    }


# ---------------------------------------------------------------------------
# claim_territory
# ---------------------------------------------------------------------------


async def claim_territory(
    db: AsyncSession,
    user_id: int,
    territory_id: int,
    creature_id: int,
) -> dict[str, Any]:
    """Claim an unclaimed territory by assigning a creature as chief.

    Validates:
    1. Territory exists.
    2. User has at least one prior Visit in the territory's area.
    3. Territory zone-type rules are respected (personal zones cannot be
       claimed if already owned by another player).
    4. Creature belongs to the user and is not already assigned elsewhere.

    Args:
        db: Async database session.
        user_id: The claiming user's ID.
        territory_id: The territory to claim.
        creature_id: The creature to assign as chief.

    Returns:
        Dict with success, territory_id, owner_id.

    Raises:
        EntityNotFoundException: Territory not found.
        TerritoryClaimDeniedException: Claim prerequisites not met.
    """
    # 1. Fetch territory
    stmt = select(Territory).where(Territory.id == territory_id)
    result = await db.execute(stmt)
    territory = result.scalars().first()

    if territory is None:
        raise EntityNotFoundException("Territory not found")

    # 2. Validate prior visit in the territory's area
    visit_stmt = (
        select(Visit.id)
        .where(Visit.user_id == user_id)
        .where(Visit.area_id == territory.area_id)
        .limit(1)
    )
    visit_result = await db.execute(visit_stmt)
    has_visit = visit_result.scalar_one_or_none()

    if has_visit is None:
        raise TerritoryClaimDeniedException(
            "You must visit the area at least once before claiming this territory"
        )

    # 3. Zone-type rules
    if territory.zone_type == "personal" and territory.owner_id is not None:
        if territory.owner_id != user_id:
            raise TerritoryClaimDeniedException(
                "This personal zone is already owned by another player"
            )

    # 4. Validate creature ownership and availability
    creature_stmt = select(Creature).where(
        Creature.id == creature_id,
        Creature.user_id == user_id,
    )
    creature_result = await db.execute(creature_stmt)
    creature = creature_result.scalars().first()

    if creature is None:
        raise EntityNotFoundException("Creature not found or does not belong to you")

    # If creature is already assigned to another territory, unassign it
    if creature.assigned_territory_id is not None and creature.assigned_territory_id != territory_id:
        creature.assigned_territory_id = None
        db.add(creature)
        await db.flush()

    # Claim the territory
    territory.owner_id = user_id
    territory.chief_creature_id = creature_id
    db.add(territory)

    # Update creature assignment
    creature.assigned_territory_id = territory_id
    db.add(creature)

    await db.flush()

    logger.info(
        "Territory claimed: user=%d territory=%d creature=%d",
        user_id, territory_id, creature_id,
    )

    return {
        "id": territory.id,
        "area_id": territory.area_id,
        "owner_id": user_id,
        "chief_creature_id": creature_id,
        "zone_type": territory.zone_type,
        "familiarity_scores": territory.familiarity_scores or {},
        "passive_reward_rate": territory.passive_reward_rate,
    }


# ---------------------------------------------------------------------------
# challenge_territory
# ---------------------------------------------------------------------------


async def challenge_territory(
    db: AsyncSession,
    user_id: int,
    territory_id: int,
    attacker_creature_id: int,
) -> dict[str, Any]:
    """Challenge the current chief of a PvP territory.

    Uses SELECT FOR UPDATE on the Territory row to prevent concurrent
    challenge race conditions. Computes effective power for both attacker
    and defender, with the defender receiving a familiarity bonus.

    Args:
        db: Async database session.
        user_id: The attacking user's ID.
        territory_id: The territory to challenge.
        attacker_creature_id: The creature to use as attacker.

    Returns:
        Dict with winner, attacker_power, defender_power, breakdown.

    Raises:
        EntityNotFoundException: Territory or creatures not found.
        TerritoryChallengeDeniedException: Not a PvP zone or other rules.
    """
    # 1. Lock the territory row with SELECT FOR UPDATE
    stmt = (
        select(Territory)
        .where(Territory.id == territory_id)
        .with_for_update()
    )
    result = await db.execute(stmt)
    territory = result.scalars().first()

    if territory is None:
        raise EntityNotFoundException("Territory not found")

    # 2. Validate PvP zone
    if territory.zone_type != "pvp":
        raise TerritoryChallengeDeniedException(
            "Challenges are only allowed on PvP zones"
        )

    # 3. Validate territory has a defender
    if territory.owner_id is None or territory.chief_creature_id is None:
        raise TerritoryChallengeDeniedException(
            "Territory is unclaimed; use claim instead of challenge"
        )

    # 4. Validate attacker creature
    att_stmt = select(Creature).where(
        Creature.id == attacker_creature_id,
        Creature.user_id == user_id,
    )
    att_result = await db.execute(att_stmt)
    attacker_creature = att_result.scalars().first()

    if attacker_creature is None:
        raise EntityNotFoundException("Attacker creature not found or does not belong to you")

    # 5. Validate attacker has visited the area
    visit_stmt = (
        select(Visit.id)
        .where(Visit.user_id == user_id)
        .where(Visit.area_id == territory.area_id)
        .limit(1)
    )
    visit_result = await db.execute(visit_stmt)
    has_visit = visit_result.scalar_one_or_none()

    if has_visit is None:
        raise TerritoryChallengeDeniedException(
            "You must visit the area at least once before challenging"
        )

    # 6. Fetch defender creature
    def_stmt = select(Creature).where(Creature.id == territory.chief_creature_id)
    def_result = await db.execute(def_stmt)
    defender_creature = def_result.scalars().first()

    if defender_creature is None:
        raise EntityNotFoundException("Defender creature not found")

    # 7. Compute item boosts for attacker
    att_items_stmt = select(Item).where(
        Item.equipped_on_creature_id == attacker_creature_id
    )
    att_items_result = await db.execute(att_items_stmt)
    att_items = att_items_result.scalars().all()

    att_item_power = sum(i.power_boost for i in att_items)
    att_item_defense = sum(i.defense_boost for i in att_items)
    att_item_stamina = sum(i.stamina_boost for i in att_items)

    # 8. Compute item boosts for defender
    def_items_stmt = select(Item).where(
        Item.equipped_on_creature_id == territory.chief_creature_id
    )
    def_items_result = await db.execute(def_items_stmt)
    def_items = def_items_result.scalars().all()

    def_item_power = sum(i.power_boost for i in def_items)
    def_item_defense = sum(i.defense_boost for i in def_items)
    def_item_stamina = sum(i.stamina_boost for i in def_items)

    # 9. Compute familiarity bonus for defender only
    familiarity_scores = territory.familiarity_scores or {}
    defender_fam_score = familiarity_scores.get(str(territory.owner_id), 0)
    defender_fam_bonus = compute_familiarity_bonus(defender_fam_score)

    # Attacker gets no familiarity bonus
    attacker_power = compute_effective_power(
        creature_power=attacker_creature.power,
        creature_defense=attacker_creature.defense,
        creature_stamina=attacker_creature.stamina,
        item_power_boost=att_item_power,
        item_defense_boost=att_item_defense,
        item_stamina_boost=att_item_stamina,
        familiarity_bonus=0.0,
    )

    defender_power = compute_effective_power(
        creature_power=defender_creature.power,
        creature_defense=defender_creature.defense,
        creature_stamina=defender_creature.stamina,
        item_power_boost=def_item_power,
        item_defense_boost=def_item_defense,
        item_stamina_boost=def_item_stamina,
        familiarity_bonus=defender_fam_bonus,
    )

    # 10. Determine winner (defender wins ties)
    # Save the original defender's creature ID before any mutation
    old_chief_id = territory.chief_creature_id

    if attacker_power > defender_power:
        winner = "attacker"
        # Transfer territory ownership

        # Unassign old defender creature
        if old_chief_id is not None:
            old_chief_stmt = select(Creature).where(Creature.id == old_chief_id)
            old_chief_result = await db.execute(old_chief_stmt)
            old_chief = old_chief_result.scalars().first()
            if old_chief is not None:
                old_chief.assigned_territory_id = None
                db.add(old_chief)

        # Assign attacker as new owner
        territory.owner_id = user_id
        territory.chief_creature_id = attacker_creature_id
        db.add(territory)

        # Update attacker creature assignment
        if attacker_creature.assigned_territory_id is not None:
            attacker_creature.assigned_territory_id = None
            db.add(attacker_creature)
            await db.flush()

        attacker_creature.assigned_territory_id = territory_id
        db.add(attacker_creature)

        # NOTE: Familiarity scores persist -- they are NOT cleared on ownership change
    else:
        winner = "defender"

    await db.flush()

    breakdown = {
        "attacker": {
            "creature_id": attacker_creature_id,
            "base_power": attacker_creature.power,
            "base_defense": attacker_creature.defense,
            "base_stamina": attacker_creature.stamina,
            "item_power_boost": att_item_power,
            "item_defense_boost": att_item_defense,
            "item_stamina_boost": att_item_stamina,
            "familiarity_bonus": 0.0,
            "total_effective_power": attacker_power,
        },
        "defender": {
            "creature_id": old_chief_id,
            "base_power": defender_creature.power,
            "base_defense": defender_creature.defense,
            "base_stamina": defender_creature.stamina,
            "item_power_boost": def_item_power,
            "item_defense_boost": def_item_defense,
            "item_stamina_boost": def_item_stamina,
            "familiarity_bonus": defender_fam_bonus,
            "familiarity_score": defender_fam_score,
            "total_effective_power": defender_power,
        },
    }

    logger.info(
        "Territory challenge: territory=%d attacker_user=%d winner=%s "
        "attacker_power=%.1f defender_power=%.1f",
        territory_id, user_id, winner, attacker_power, defender_power,
    )

    return {
        "winner": winner,
        "attacker_power": attacker_power,
        "defender_power": defender_power,
        "breakdown": breakdown,
    }


# ---------------------------------------------------------------------------
# contribute_to_territory
# ---------------------------------------------------------------------------


async def contribute_to_territory(
    db: AsyncSession,
    user_id: int,
    territory_id: int,
    creature_id: int,
) -> dict[str, Any]:
    """Contribute a creature to a cooperative territory.

    Cooperative zones allow multiple players to assign creatures. Each
    contributor receives a share of the passive rewards proportional to
    their creature's power.

    Args:
        db: Async database session.
        user_id: The contributing user's ID.
        territory_id: The territory to contribute to.
        creature_id: The creature to contribute.

    Returns:
        Dict with success, territory_id, creature_id.

    Raises:
        EntityNotFoundException: Territory or creature not found.
        TerritoryContributionDeniedException: Not a cooperative zone or
            no prior visit.
    """
    # 1. Fetch territory
    stmt = select(Territory).where(Territory.id == territory_id)
    result = await db.execute(stmt)
    territory = result.scalars().first()

    if territory is None:
        raise EntityNotFoundException("Territory not found")

    # 2. Validate cooperative zone
    if territory.zone_type != "cooperative":
        raise TerritoryContributionDeniedException(
            "Contributions are only allowed on cooperative zones"
        )

    # 3. Validate prior visit in the territory's area
    visit_stmt = (
        select(Visit.id)
        .where(Visit.user_id == user_id)
        .where(Visit.area_id == territory.area_id)
        .limit(1)
    )
    visit_result = await db.execute(visit_stmt)
    has_visit = visit_result.scalar_one_or_none()

    if has_visit is None:
        raise TerritoryContributionDeniedException(
            "You must visit the area at least once before contributing"
        )

    # 4. Validate creature ownership
    creature_stmt = select(Creature).where(
        Creature.id == creature_id,
        Creature.user_id == user_id,
    )
    creature_result = await db.execute(creature_stmt)
    creature = creature_result.scalars().first()

    if creature is None:
        raise EntityNotFoundException("Creature not found or does not belong to you")

    # 5. If creature is assigned elsewhere, unassign it first
    if creature.assigned_territory_id is not None and creature.assigned_territory_id != territory_id:
        creature.assigned_territory_id = None
        db.add(creature)
        await db.flush()

    # 6. Assign creature to this territory
    creature.assigned_territory_id = territory_id
    db.add(creature)

    # 7. Set the first contributor as owner if territory has no owner yet
    if territory.owner_id is None:
        territory.owner_id = user_id
        territory.chief_creature_id = creature_id
        db.add(territory)

    await db.flush()

    logger.info(
        "Territory contribution: user=%d territory=%d creature=%d",
        user_id, territory_id, creature_id,
    )

    return {
        "id": territory.id,
        "area_id": territory.area_id,
        "owner_id": territory.owner_id,
        "chief_creature_id": territory.chief_creature_id,
        "zone_type": territory.zone_type,
        "familiarity_scores": territory.familiarity_scores or {},
        "passive_reward_rate": territory.passive_reward_rate,
    }


# ---------------------------------------------------------------------------
# claim_home
# ---------------------------------------------------------------------------

_HOME_COOLDOWN = datetime.timedelta(hours=24)


async def claim_home(
    db: AsyncSession,
    user_id: int,
    territory_id: int,
) -> dict[str, Any]:
    """Claim a personal hex territory as the user's home."""
    territory = await db.get(Territory, territory_id)
    if not territory:
        raise EntityNotFoundException("Territory not found")
    if territory.zone_type != "personal":
        raise HomeClaimDeniedException("Only personal zones can be claimed as home")

    user = await db.get(User, user_id)
    if not user:
        raise EntityNotFoundException("User not found")

    if user.home_claimed_at is not None:
        now = datetime.datetime.now(datetime.timezone.utc)
        claimed_at = user.home_claimed_at
        if claimed_at.tzinfo is None:
            claimed_at = claimed_at.replace(tzinfo=datetime.timezone.utc)
        elapsed = now - claimed_at
        if elapsed < _HOME_COOLDOWN:
            remaining = _HOME_COOLDOWN - elapsed
            hours = int(remaining.total_seconds() // 3600)
            raise HomeClaimDeniedException(f"Relocation cooldown: {hours}h remaining")

    user.home_territory_id = territory_id
    user.home_claimed_at = datetime.datetime.now(datetime.timezone.utc)
    await db.flush()

    return {
        "home_territory_id": user.home_territory_id,
        "home_claimed_at": user.home_claimed_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# get_residents
# ---------------------------------------------------------------------------


async def get_residents(
    db: AsyncSession,
    territory_id: int,
) -> list[dict[str, Any]]:
    """Get all users who have claimed this territory as their home."""
    territory = await db.get(Territory, territory_id)
    if not territory:
        raise EntityNotFoundException("Territory not found")
    if territory.zone_type != "personal":
        raise HomeClaimDeniedException("Only personal zones have residents")

    result = await db.execute(
        select(User.id, User.username, User.home_claimed_at)
        .where(User.home_territory_id == territory_id)
        .order_by(User.home_claimed_at)
    )
    return [
        {
            "user_id": row.id,
            "username": row.username,
            "home_claimed_at": row.home_claimed_at.isoformat() if row.home_claimed_at else None,
        }
        for row in result
    ]
