"""Tests for personal hex home claiming."""

import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, EntityNotFoundException
from app.core.security import hash_password
from app.models.area import Area
from app.models.territory import Territory
from app.models.user import User

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_area(db: AsyncSession, name: str, zone_type: str) -> int:
    """Helper: create an area with a PostGIS polygon boundary via raw SQL."""
    result = await db.execute(
        text(
            "INSERT INTO areas (name, city, boundary, zone_type) "
            "VALUES (:name, 'Versailles', "
            "CAST(ST_SetSRID(ST_GeomFromText("
            "'POLYGON((2.12 48.80, 2.121 48.80, 2.121 48.801, 2.12 48.801, 2.12 48.80))'"
            "), 4326) AS geography), :zone_type) "
            "RETURNING id"
        ),
        {"name": name, "zone_type": zone_type},
    )
    area_id = result.scalar_one()
    await db.flush()
    return area_id


async def _create_personal_territory(db: AsyncSession, name: str = "Hex-Test") -> Territory:
    """Helper: create a personal territory with a PostGIS polygon area."""
    area_id = await _create_area(db, name, "personal")
    territory = Territory(
        area_id=area_id,
        zone_type="personal",
        passive_reward_rate=1.0,
        familiarity_scores={},
    )
    db.add(territory)
    await db.flush()
    return territory


async def _create_pvp_territory(db: AsyncSession) -> Territory:
    """Helper: create a PvP territory."""
    area_id = await _create_area(db, "PvP Zone", "pvp")
    territory = Territory(
        area_id=area_id,
        zone_type="pvp",
        passive_reward_rate=1.0,
        familiarity_scores={},
    )
    db.add(territory)
    await db.flush()
    return territory


async def test_claim_home_success(db_session: AsyncSession, test_user: User):
    from app.services.territory_service import claim_home
    territory = await _create_personal_territory(db_session)
    result = await claim_home(db_session, test_user.id, territory.id)
    assert result["home_territory_id"] == territory.id
    assert result["home_claimed_at"] is not None


async def test_claim_home_wrong_zone_type(db_session: AsyncSession, test_user: User):
    from app.services.territory_service import claim_home
    territory = await _create_pvp_territory(db_session)
    with pytest.raises(AppException, match="personal"):
        await claim_home(db_session, test_user.id, territory.id)


async def test_claim_home_relocate_after_cooldown(db_session: AsyncSession, test_user: User):
    from app.services.territory_service import claim_home
    t1 = await _create_personal_territory(db_session, "Hex-A")
    t2 = await _create_personal_territory(db_session, "Hex-B")
    await claim_home(db_session, test_user.id, t1.id)
    test_user.home_claimed_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=25)
    await db_session.flush()
    result = await claim_home(db_session, test_user.id, t2.id)
    assert result["home_territory_id"] == t2.id


async def test_claim_home_cooldown_enforced(db_session: AsyncSession, test_user: User):
    from app.services.territory_service import claim_home
    t1 = await _create_personal_territory(db_session, "Hex-C")
    t2 = await _create_personal_territory(db_session, "Hex-D")
    await claim_home(db_session, test_user.id, t1.id)
    with pytest.raises(AppException, match="cooldown"):
        await claim_home(db_session, test_user.id, t2.id)


async def test_claim_home_territory_not_found(db_session: AsyncSession, test_user: User):
    from app.services.territory_service import claim_home
    with pytest.raises(EntityNotFoundException):
        await claim_home(db_session, test_user.id, 99999)


async def test_get_residents_returns_users(db_session: AsyncSession, test_user: User):
    from app.services.territory_service import claim_home, get_residents
    territory = await _create_personal_territory(db_session, "Hex-Res")
    await claim_home(db_session, test_user.id, territory.id)
    user2 = User(
        username="resident2", email="resident2@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user2)
    await db_session.flush()
    await claim_home(db_session, user2.id, territory.id)
    residents = await get_residents(db_session, territory.id)
    assert len(residents) == 2
    usernames = {r["username"] for r in residents}
    assert "testuser" in usernames
    assert "resident2" in usernames


async def test_get_residents_empty(db_session: AsyncSession):
    from app.services.territory_service import get_residents
    territory = await _create_personal_territory(db_session, "Hex-Empty")
    residents = await get_residents(db_session, territory.id)
    assert residents == []


async def test_get_residents_wrong_zone_type(db_session: AsyncSession):
    from app.services.territory_service import get_residents
    territory = await _create_pvp_territory(db_session)
    with pytest.raises(AppException, match="personal"):
        await get_residents(db_session, territory.id)
