"""Integration tests for personal hex home claiming API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.area import Area
from app.models.territory import Territory
from app.models.user import User

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _seed_personal_territory(db: AsyncSession) -> int:
    """Seed a personal territory and return its ID."""
    result = await db.execute(
        text(
            "INSERT INTO areas (name, city, boundary, zone_type) "
            "VALUES ('Hex-API-Test', 'Versailles', "
            "ST_GeogFromText('SRID=4326;POLYGON((2.12 48.80, 2.121 48.80, 2.121 48.801, 2.12 48.801, 2.12 48.80))'), "
            "'personal') RETURNING id"
        )
    )
    area_id = result.scalar_one()
    territory = Territory(
        area_id=area_id, zone_type="personal",
        passive_reward_rate=1.0, familiarity_scores={},
    )
    db.add(territory)
    await db.flush()
    return territory.id


async def test_claim_home_endpoint(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
):
    """POST /game/territories/{id}/claim-home returns updated territory."""
    tid = await _seed_personal_territory(db_session)
    resp = await authenticated_client.post(f"/game/territories/{tid}/claim-home")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == tid
    assert data["zone_type"] == "personal"


async def test_claim_home_unauthenticated(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """POST /game/territories/{id}/claim-home requires auth."""
    tid = await _seed_personal_territory(db_session)
    resp = await client.post(f"/game/territories/{tid}/claim-home")
    assert resp.status_code == 401


async def test_get_residents_endpoint(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
):
    """GET /game/territories/{id}/residents returns resident list."""
    tid = await _seed_personal_territory(db_session)
    # Claim first
    await authenticated_client.post(f"/game/territories/{tid}/claim-home")
    resp = await authenticated_client.get(f"/game/territories/{tid}/residents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["username"] == "testuser"
