# Versailles Territories & POIs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Seed Versailles Quartier Notre-Dame with 6 named territories (PvP/cooperative), a personal hex grid, ~100 real POIs, and endpoints for claiming a personal home hex.

**Architecture:** Alembic migration adds home territory columns to users and seeds geographic data (6 named areas with hand-drawn polygons + hex grid via PostGIS ST_HexagonGrid in Lambert-93 projection). Two new service functions and API endpoints enable personal hex claiming with 24h relocation cooldown. Standalone Outscraper script seeds ~100 real POIs.

**Tech Stack:** PostGIS 3.4, SQLAlchemy 2.0, FastAPI, geoalchemy2, Outscraper SDK, Alembic, pytest

**Design doc:** `docs/plans/2026-02-26-versailles-territories-design.md`

---

### Task 1: Add Home Territory Fields to User Model

**Files:**
- Modify: `backend/app/models/user.py`

**Step 1: Add home_territory_id and home_claimed_at fields**

Add `ForeignKey` to the existing import from sqlalchemy, add `Optional` to typing import, then add two new columns after `created_at`:

```python
# In imports, change:
from sqlalchemy import Integer, String, DateTime
# To:
from sqlalchemy import Integer, String, DateTime, ForeignKey

# Change typing import:
from typing import Any
# To:
from typing import Any, Optional

# Add after the created_at field (line ~45):
home_territory_id: Mapped[Optional[int]] = mapped_column(
    Integer, ForeignKey("territories.id"), nullable=True, index=True,
)
home_claimed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
    DateTime(timezone=True), nullable=True,
)
```

**Step 2: Verify the model loads without errors**

Run: `cd backend && python -c "from app.models.user import User; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/models/user.py
git commit -m "feat: add home_territory_id and home_claimed_at to User model"
```

---

### Task 2: Add Schemas for Home Territory

**Files:**
- Modify: `backend/app/schemas/territory.py`

**Step 1: Add area_name and residents_count to TerritoryResponse**

In `TerritoryResponse` class, add after `familiarity_rankings`:

```python
area_name: Optional[str] = None
residents_count: Optional[int] = None
```

**Step 2: Add ResidentResponse schema**

Add at the end of the file:

```python
class ResidentResponse(BaseModel):
    """A resident of a personal hex territory."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    home_claimed_at: Optional[str] = None
```

**Step 3: Commit**

```bash
git add backend/app/schemas/territory.py
git commit -m "feat: add area_name, residents_count, and ResidentResponse schemas"
```

---

### Task 3: Migration 005 — Schema Changes + Versailles Seed Data

**Files:**
- Create: `backend/alembic/versions/005_versailles_territories.py`

**Step 1: Create the migration file**

```python
"""Add home territory to users and seed Versailles territories.

Adds home_territory_id and home_claimed_at columns to the users table,
then seeds 6 named areas with PostGIS polygon boundaries in Versailles
Quartier Notre-Dame, creates corresponding territory records, and generates
a personal hex grid (100m edge, Lambert-93 projection) for the remaining
space.

Revision ID: 005
Revises: 004
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


# Named territories for Versailles Quartier Notre-Dame.
# Polygons are approximate rectangles in SRID 4326 (lon lat).
_NAMED_TERRITORIES = [
    {
        "name": "Château de Versailles & Jardins",
        "city": "Versailles",
        "zone_type": "pvp",
        "wkt": (
            "SRID=4326;POLYGON(("
            "2.0830 48.8130, 2.1190 48.8130, 2.1190 48.8000, "
            "2.0830 48.8000, 2.0830 48.8130))"
        ),
    },
    {
        "name": "Place d'Armes",
        "city": "Versailles",
        "zone_type": "pvp",
        "wkt": (
            "SRID=4326;POLYGON(("
            "2.1190 48.8090, 2.1260 48.8090, 2.1260 48.8030, "
            "2.1190 48.8030, 2.1190 48.8090))"
        ),
    },
    {
        "name": "Marché Notre-Dame",
        "city": "Versailles",
        "zone_type": "cooperative",
        "wkt": (
            "SRID=4326;POLYGON(("
            "2.1280 48.8055, 2.1340 48.8055, 2.1340 48.8020, "
            "2.1280 48.8020, 2.1280 48.8055))"
        ),
    },
    {
        "name": "Cathédrale Saint-Louis",
        "city": "Versailles",
        "zone_type": "cooperative",
        "wkt": (
            "SRID=4326;POLYGON(("
            "2.1230 48.8030, 2.1280 48.8030, 2.1280 48.7990, "
            "2.1230 48.7990, 2.1230 48.8030))"
        ),
    },
    {
        "name": "Rue de la Paroisse",
        "city": "Versailles",
        "zone_type": "cooperative",
        "wkt": (
            "SRID=4326;POLYGON(("
            "2.1290 48.8090, 2.1320 48.8090, 2.1320 48.8055, "
            "2.1290 48.8055, 2.1290 48.8090))"
        ),
    },
    {
        "name": "Parc Balbi & Pièce d'Eau des Suisses",
        "city": "Versailles",
        "zone_type": "pvp",
        "wkt": (
            "SRID=4326;POLYGON(("
            "2.1100 48.8000, 2.1250 48.8000, 2.1250 48.7920, "
            "2.1100 48.7920, 2.1100 48.8000))"
        ),
    },
]

# Bounding box for hex grid (covers Quartier Notre-Dame + buffer).
# Coordinates: xmin, ymin, xmax, ymax in SRID 4326.
_HEX_BBOX = (2.100, 48.790, 2.145, 48.815)

# Hex edge length in meters (Lambert-93 EPSG:2154).
_HEX_EDGE_M = 100


def upgrade() -> None:
    # ---------------------------------------------------------------
    # 1. Schema changes: add home territory columns to users
    # ---------------------------------------------------------------
    op.add_column(
        "users",
        sa.Column("home_territory_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("home_claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_home_territory_id", "users", ["home_territory_id"],
    )
    op.create_foreign_key(
        "fk_users_home_territory_id",
        "users",
        "territories",
        ["home_territory_id"],
        ["id"],
    )

    # ---------------------------------------------------------------
    # 2. Seed 6 named areas + territories
    # ---------------------------------------------------------------
    conn = op.get_bind()

    for t in _NAMED_TERRITORIES:
        result = conn.execute(
            sa.text(
                "INSERT INTO areas (name, city, boundary, zone_type) "
                "VALUES (:name, :city, ST_GeogFromText(:wkt), :zone_type) "
                "RETURNING id"
            ),
            {"name": t["name"], "city": t["city"], "wkt": t["wkt"], "zone_type": t["zone_type"]},
        )
        area_id = result.scalar_one()
        conn.execute(
            sa.text(
                "INSERT INTO territories (area_id, zone_type, passive_reward_rate, familiarity_scores) "
                "VALUES (:area_id, :zone_type, 1.0, :fs)"
            ),
            {"area_id": area_id, "zone_type": t["zone_type"], "fs": "{}"},
        )

    # ---------------------------------------------------------------
    # 3. Generate hex grid for remaining space
    #    - Project bounding box to Lambert-93 (EPSG:2154) for meter sizing
    #    - Generate hexagons with ST_HexagonGrid
    #    - Project back to SRID 4326
    #    - Exclude hexes whose centroid falls inside a named territory
    # ---------------------------------------------------------------
    xmin, ymin, xmax, ymax = _HEX_BBOX
    conn.execute(
        sa.text(f"""
            WITH bounds AS (
                SELECT ST_Transform(
                    ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, 4326),
                    2154
                ) AS geom
            ),
            hex_raw AS (
                SELECT (h).geom, (h).i, (h).j
                FROM bounds,
                     LATERAL ST_HexagonGrid({_HEX_EDGE_M}, bounds.geom) AS h
            ),
            hex_4326 AS (
                SELECT ST_Transform(geom, 4326) AS geom, i, j
                FROM hex_raw
            ),
            filtered AS (
                SELECT geom, i, j
                FROM hex_4326
                WHERE NOT EXISTS (
                    SELECT 1 FROM areas named
                    WHERE named.zone_type IN ('pvp', 'cooperative')
                      AND ST_Contains(
                          named.boundary::geometry,
                          ST_Centroid(geom)
                      )
                )
            ),
            numbered AS (
                SELECT geom,
                       ROW_NUMBER() OVER (ORDER BY j, i) AS n
                FROM filtered
            )
            INSERT INTO areas (name, city, boundary, zone_type)
            SELECT
                'Hex-' || n,
                'Versailles',
                geom::geography,
                'personal'
            FROM numbered
        """)
    )

    # Create a territory record for each personal hex area
    conn.execute(
        sa.text(
            "INSERT INTO territories (area_id, zone_type, passive_reward_rate, familiarity_scores) "
            "SELECT a.id, 'personal', 1.0, '{}' "
            "FROM areas a "
            "WHERE a.zone_type = 'personal' "
            "  AND a.city = 'Versailles' "
            "  AND NOT EXISTS (SELECT 1 FROM territories t WHERE t.area_id = a.id)"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Clear home territory references from users first (FK constraint)
    conn.execute(sa.text(
        "UPDATE users SET home_territory_id = NULL, home_claimed_at = NULL "
        "WHERE home_territory_id IS NOT NULL"
    ))

    # Remove territories and areas seeded by this migration
    conn.execute(sa.text(
        "DELETE FROM territories WHERE area_id IN "
        "(SELECT id FROM areas WHERE city = 'Versailles')"
    ))
    conn.execute(sa.text("DELETE FROM areas WHERE city = 'Versailles'"))

    # Drop home territory columns
    op.drop_constraint("fk_users_home_territory_id", "users", type_="foreignkey")
    op.drop_index("ix_users_home_territory_id", table_name="users")
    op.drop_column("users", "home_claimed_at")
    op.drop_column("users", "home_territory_id")
```

**Step 2: Run the migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration applies successfully.

**Step 3: Verify seed data**

Run: `cd backend && python -c "
import asyncio
from sqlalchemy import text
from app.db.session import async_engine

async def verify():
    async with async_engine.connect() as conn:
        r = await conn.execute(text(\"SELECT zone_type, COUNT(*) FROM areas WHERE city = 'Versailles' GROUP BY zone_type ORDER BY zone_type\"))
        for row in r:
            print(f'{row[0]}: {row[1]} areas')
        r = await conn.execute(text('SELECT COUNT(*) FROM territories'))
        print(f'Total territories: {r.scalar()}')
asyncio.run(verify())
"`

Expected output (approximately):
```
cooperative: 3 areas
personal: ~200-300 areas
pvp: 3 areas
Total territories: ~206-306
```

**Step 4: Commit**

```bash
git add backend/alembic/versions/005_versailles_territories.py
git commit -m "feat: migration 005 - Versailles areas, territories, and hex grid"
```

---

### Task 4: Territory Service — claim_home() (TDD)

**Files:**
- Create: `backend/tests/test_claim_home.py`
- Modify: `backend/app/services/territory_service.py`

**Step 1: Write failing tests**

```python
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


async def _create_personal_territory(db: AsyncSession, name: str = "Hex-Test") -> Territory:
    """Helper: create a personal territory with a PostGIS polygon area."""
    area = Area(
        name=name,
        city="Versailles",
        zone_type="personal",
    )
    db.add(area)
    await db.flush()

    # Set a real PostGIS polygon boundary via raw SQL
    await db.execute(
        text(
            "UPDATE areas SET boundary = ST_GeogFromText("
            "'SRID=4326;POLYGON((2.12 48.80, 2.121 48.80, 2.121 48.801, 2.12 48.801, 2.12 48.80))')"
            " WHERE id = :aid"
        ),
        {"aid": area.id},
    )
    await db.flush()

    territory = Territory(
        area_id=area.id,
        zone_type="personal",
        passive_reward_rate=1.0,
        familiarity_scores={},
    )
    db.add(territory)
    await db.flush()
    return territory


async def _create_pvp_territory(db: AsyncSession) -> Territory:
    """Helper: create a PvP territory."""
    area = Area(
        name="PvP Zone",
        city="Versailles",
        zone_type="pvp",
    )
    db.add(area)
    await db.flush()

    await db.execute(
        text(
            "UPDATE areas SET boundary = ST_GeogFromText("
            "'SRID=4326;POLYGON((2.13 48.80, 2.131 48.80, 2.131 48.801, 2.13 48.801, 2.13 48.80))')"
            " WHERE id = :aid"
        ),
        {"aid": area.id},
    )
    await db.flush()

    territory = Territory(
        area_id=area.id,
        zone_type="pvp",
        passive_reward_rate=1.0,
        familiarity_scores={},
    )
    db.add(territory)
    await db.flush()
    return territory


async def test_claim_home_success(db_session: AsyncSession, test_user: User):
    """User can claim a personal hex as home."""
    from app.services.territory_service import claim_home

    territory = await _create_personal_territory(db_session)
    result = await claim_home(db_session, test_user.id, territory.id)

    assert result["home_territory_id"] == territory.id
    assert result["home_claimed_at"] is not None


async def test_claim_home_wrong_zone_type(db_session: AsyncSession, test_user: User):
    """Cannot claim a PvP territory as home."""
    from app.services.territory_service import claim_home

    territory = await _create_pvp_territory(db_session)

    with pytest.raises(AppException, match="personal"):
        await claim_home(db_session, test_user.id, territory.id)


async def test_claim_home_relocate_after_cooldown(db_session: AsyncSession, test_user: User):
    """User can relocate home after 24h cooldown."""
    from app.services.territory_service import claim_home

    t1 = await _create_personal_territory(db_session, "Hex-A")
    t2 = await _create_personal_territory(db_session, "Hex-B")

    await claim_home(db_session, test_user.id, t1.id)

    # Backdate home_claimed_at to 25 hours ago to bypass cooldown
    test_user.home_claimed_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=25)
    await db_session.flush()

    result = await claim_home(db_session, test_user.id, t2.id)
    assert result["home_territory_id"] == t2.id


async def test_claim_home_cooldown_enforced(db_session: AsyncSession, test_user: User):
    """Cannot relocate home within 24h cooldown."""
    from app.services.territory_service import claim_home

    t1 = await _create_personal_territory(db_session, "Hex-C")
    t2 = await _create_personal_territory(db_session, "Hex-D")

    await claim_home(db_session, test_user.id, t1.id)

    with pytest.raises(AppException, match="cooldown"):
        await claim_home(db_session, test_user.id, t2.id)


async def test_claim_home_territory_not_found(db_session: AsyncSession, test_user: User):
    """Raises EntityNotFoundException for non-existent territory."""
    from app.services.territory_service import claim_home

    with pytest.raises(EntityNotFoundException):
        await claim_home(db_session, test_user.id, 99999)
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_claim_home.py -v`
Expected: FAIL — `ImportError: cannot import name 'claim_home'`

**Step 3: Implement claim_home in territory service**

Add a new custom exception class after `TerritoryContributionDeniedException` (~line 60):

```python
class HomeClaimDeniedException(AppException):
    """Raised when a home claim is denied (wrong zone, cooldown, etc.)."""

    status_code = 403
    error_type = "home_claim_denied"
    message = "Home claim denied"
```

Add the `claim_home` function at the end of the file (before the module ends):

```python
# ---------------------------------------------------------------------------
# claim_home
# ---------------------------------------------------------------------------

_HOME_COOLDOWN = datetime.timedelta(hours=24)


async def claim_home(
    db: AsyncSession,
    user_id: int,
    territory_id: int,
) -> dict[str, Any]:
    """Claim a personal hex territory as the user's home.

    Rules:
    - Territory must exist and have zone_type = 'personal'.
    - If the user already has a home, a 24-hour cooldown must have elapsed
      since their last claim before they can relocate.
    - Multiple users can claim the same personal hex.

    Args:
        db: Async database session.
        user_id: ID of the claiming user.
        territory_id: ID of the personal territory to claim as home.

    Returns:
        Dict with home_territory_id and home_claimed_at.

    Raises:
        EntityNotFoundException: If the territory or user does not exist.
        HomeClaimDeniedException: If the territory is not personal or
            the cooldown has not elapsed.
    """
    territory = await db.get(Territory, territory_id)
    if not territory:
        raise EntityNotFoundException("Territory not found")

    if territory.zone_type != "personal":
        raise HomeClaimDeniedException("Only personal zones can be claimed as home")

    user = await db.get(User, user_id)
    if not user:
        raise EntityNotFoundException("User not found")

    # Enforce 24h relocation cooldown
    if user.home_claimed_at is not None:
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = now - user.home_claimed_at
        if elapsed < _HOME_COOLDOWN:
            remaining = _HOME_COOLDOWN - elapsed
            hours = int(remaining.total_seconds() // 3600)
            raise HomeClaimDeniedException(
                f"Relocation cooldown: {hours}h remaining"
            )

    user.home_territory_id = territory_id
    user.home_claimed_at = datetime.datetime.now(datetime.timezone.utc)
    await db.flush()

    return {
        "home_territory_id": user.home_territory_id,
        "home_claimed_at": user.home_claimed_at.isoformat(),
    }
```

Also add `import datetime` to the top of the file imports (after `import logging`).

**Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_claim_home.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add backend/tests/test_claim_home.py backend/app/services/territory_service.py
git commit -m "feat: add claim_home() to territory service with 24h cooldown"
```

---

### Task 5: Territory Service — get_residents() (TDD)

**Files:**
- Modify: `backend/tests/test_claim_home.py` (add new tests)
- Modify: `backend/app/services/territory_service.py`

**Step 1: Write failing tests**

Append to `backend/tests/test_claim_home.py`:

```python
async def test_get_residents_returns_users(db_session: AsyncSession, test_user: User):
    """get_residents returns users who claimed a personal hex."""
    from app.services.territory_service import claim_home, get_residents

    territory = await _create_personal_territory(db_session, "Hex-Res")
    await claim_home(db_session, test_user.id, territory.id)

    # Create a second user and claim the same hex
    user2 = User(
        username="resident2",
        email="resident2@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user2)
    await db_session.flush()

    # Bypass cooldown for user2 (fresh user, no prior home)
    await claim_home(db_session, user2.id, territory.id)

    residents = await get_residents(db_session, territory.id)
    assert len(residents) == 2
    usernames = {r["username"] for r in residents}
    assert "testuser" in usernames
    assert "resident2" in usernames


async def test_get_residents_empty(db_session: AsyncSession):
    """get_residents returns empty list for unclaimed personal hex."""
    from app.services.territory_service import get_residents

    territory = await _create_personal_territory(db_session, "Hex-Empty")
    residents = await get_residents(db_session, territory.id)
    assert residents == []


async def test_get_residents_wrong_zone_type(db_session: AsyncSession):
    """get_residents raises for non-personal territory."""
    from app.services.territory_service import get_residents

    territory = await _create_pvp_territory(db_session)
    with pytest.raises(AppException, match="personal"):
        await get_residents(db_session, territory.id)
```

**Step 2: Run tests to verify new tests fail**

Run: `cd backend && python -m pytest tests/test_claim_home.py::test_get_residents_returns_users -v`
Expected: FAIL — `ImportError: cannot import name 'get_residents'`

**Step 3: Implement get_residents**

Add at the end of `backend/app/services/territory_service.py`:

```python
# ---------------------------------------------------------------------------
# get_residents
# ---------------------------------------------------------------------------


async def get_residents(
    db: AsyncSession,
    territory_id: int,
) -> list[dict[str, Any]]:
    """Get all users who have claimed this territory as their home.

    Only valid for personal zone territories.

    Args:
        db: Async database session.
        territory_id: Territory to look up residents for.

    Returns:
        List of dicts with user_id, username, and home_claimed_at.

    Raises:
        EntityNotFoundException: If the territory does not exist.
        HomeClaimDeniedException: If the territory is not a personal zone.
    """
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
```

**Step 4: Run all claim_home tests**

Run: `cd backend && python -m pytest tests/test_claim_home.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add backend/tests/test_claim_home.py backend/app/services/territory_service.py
git commit -m "feat: add get_residents() to territory service"
```

---

### Task 6: Territory API — claim-home and residents Endpoints (TDD)

**Files:**
- Create: `backend/tests/test_home_api.py`
- Modify: `backend/app/api/territories.py`

**Step 1: Write failing API tests**

```python
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
    area = Area(name="Hex-API-Test", city="Versailles", zone_type="personal")
    db.add(area)
    await db.flush()
    await db.execute(
        text(
            "UPDATE areas SET boundary = ST_GeogFromText("
            "'SRID=4326;POLYGON((2.12 48.80, 2.121 48.80, 2.121 48.801, 2.12 48.801, 2.12 48.80))')"
            " WHERE id = :aid"
        ),
        {"aid": area.id},
    )
    await db.flush()
    territory = Territory(
        area_id=area.id, zone_type="personal",
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
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_home_api.py -v`
Expected: FAIL — 404 (endpoints don't exist yet)

**Step 3: Add endpoints to territories router**

In `backend/app/api/territories.py`, add imports:

```python
# Add to the schema imports:
from app.schemas.territory import (
    ChallengeResult,
    ChallengeTerritoryRequest,
    ClaimTerritoryRequest,
    ContributeRequest,
    ResidentResponse,
    TerritoryResponse,
)

# Add to the service imports:
from app.services.territory_service import (
    challenge_territory,
    claim_home,
    claim_territory,
    contribute_to_territory,
    get_nearby_territories,
    get_residents,
    get_territory_detail,
)
```

Then add the two new endpoints at the end of the file:

```python
@router.post("/{territory_id}/claim-home", response_model=TerritoryResponse)
async def claim_home_endpoint(
    territory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Claim a personal hex territory as the user's home.

    Only personal zone territories can be claimed. Multiple users can
    share the same hex. A 24-hour cooldown applies when relocating.

    Raises:
        EntityNotFoundException: If the territory does not exist.
        HomeClaimDeniedException: If not a personal zone or cooldown active.
    """
    await claim_home(db=db, user_id=current_user.id, territory_id=territory_id)
    result = await get_territory_detail(
        db=db, territory_id=territory_id, user_id=current_user.id,
    )
    return result


@router.get("/{territory_id}/residents", response_model=list[ResidentResponse])
async def get_residents_endpoint(
    territory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List all users who have claimed this personal hex as home.

    Raises:
        EntityNotFoundException: If the territory does not exist.
        HomeClaimDeniedException: If not a personal zone.
    """
    return await get_residents(db=db, territory_id=territory_id)
```

**Step 4: Run API tests**

Run: `cd backend && python -m pytest tests/test_home_api.py -v`
Expected: All 3 tests PASS

**Step 5: Run full test suite to check for regressions**

Run: `cd backend && python -m pytest tests/ -v --timeout=120`
Expected: All tests pass

**Step 6: Commit**

```bash
git add backend/tests/test_home_api.py backend/app/api/territories.py
git commit -m "feat: add claim-home and residents API endpoints"
```

---

### Task 7: POI Seed Script

**Files:**
- Create: `backend/scripts/seed_versailles_pois.py`

**Step 1: Create the seed script**

```python
#!/usr/bin/env python3
"""Seed ~100 notable POIs in Versailles Quartier Notre-Dame via Outscraper.

Usage:
    cd backend
    python scripts/seed_versailles_pois.py

Requires OUTSCRAPER_API_KEY environment variable (from .env or export).
"""

import asyncio
import os
import sys

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from outscraper import ApiClient
from sqlalchemy import text

from app.db.session import async_engine

OUTSCRAPER_API_KEY = os.environ.get("OUTSCRAPER_API_KEY", "")
TARGET_COUNT = 100

# Queries targeting notable/famous places, with per-query limits.
SEARCH_QUERIES = [
    ("restaurants Versailles centre-ville, France", 15),
    ("cafés Versailles Quartier Notre-Dame, France", 12),
    ("monuments historiques Versailles, France", 12),
    ("musées Versailles, France", 10),
    ("parcs jardins Versailles, France", 10),
    ("boutiques Versailles Rue de la Paroisse, France", 12),
    ("églises Versailles, France", 8),
    ("bars Versailles centre, France", 10),
    ("boulangeries pâtisseries Versailles centre, France", 11),
]

# Map Outscraper place types to our Place.category values.
TYPE_TO_CATEGORY = {
    "restaurant": "restaurant",
    "cafe": "cafe",
    "bar": "bar",
    "museum": "museum",
    "park": "park",
    "church": "church",
    "store": "shop",
    "clothing_store": "shop",
    "bakery": "restaurant",
    "tourist_attraction": "landmark",
    "point_of_interest": "landmark",
    "establishment": "general",
    "food": "restaurant",
    "night_club": "bar",
    "library": "library",
    "book_store": "shop",
    "gym": "gym",
    "art_gallery": "museum",
    "shopping_mall": "shop",
    "spa": "general",
    "lodging": "general",
}


def _extract_category(place: dict) -> str:
    """Extract our category from Outscraper place type string."""
    raw_type = place.get("type", "") or ""
    for part in raw_type.split(","):
        part = part.strip().lower()
        if part in TYPE_TO_CATEGORY:
            return TYPE_TO_CATEGORY[part]
    # Fallback: try subtypes
    for subtype in (place.get("subtypes") or "").split(","):
        subtype = subtype.strip().lower()
        if subtype in TYPE_TO_CATEGORY:
            return TYPE_TO_CATEGORY[subtype]
    return "general"


async def seed_pois() -> None:
    if not OUTSCRAPER_API_KEY:
        print("ERROR: Set OUTSCRAPER_API_KEY environment variable")
        sys.exit(1)

    client = ApiClient(api_key=OUTSCRAPER_API_KEY)
    all_places: dict[str, dict] = {}  # google_place_id -> place data

    for query, limit in SEARCH_QUERIES:
        if len(all_places) >= TARGET_COUNT:
            break
        print(f"  Searching: {query} (limit={limit})")
        try:
            results = client.google_maps_search([query], limit=limit, language="en")
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        if results and results[0]:
            for place in results[0]:
                place_id = place.get("place_id")
                if place_id and place_id not in all_places:
                    all_places[place_id] = place
        print(f"  Running total: {len(all_places)} unique places")

    # Trim to target
    places_list = list(all_places.items())[:TARGET_COUNT]
    print(f"\nInserting {len(places_list)} places into database...")

    async with async_engine.begin() as conn:
        inserted = 0
        skipped = 0
        for place_id, place in places_list:
            lat = place.get("latitude")
            lng = place.get("longitude")
            name = place.get("name", "Unknown")
            category = _extract_category(place)
            address = place.get("full_address")

            if not lat or not lng:
                skipped += 1
                continue

            try:
                result = await conn.execute(
                    text(
                        "INSERT INTO places "
                        "(google_place_id, name, category, coordinates, address, city, country) "
                        "VALUES (:pid, :name, :cat, ST_GeogFromText(:coords), :addr, 'Versailles', 'France') "
                        "ON CONFLICT (google_place_id) DO NOTHING "
                        "RETURNING id"
                    ),
                    {
                        "pid": place_id,
                        "name": name,
                        "cat": category,
                        "coords": f"SRID=4326;POINT({lng} {lat})",
                        "addr": address,
                    },
                )
                if result.scalar_one_or_none() is not None:
                    inserted += 1
            except Exception as e:
                print(f"  Error inserting {name}: {e}")
                skipped += 1

        print(f"Inserted: {inserted}, Skipped: {skipped}")

    # Report distribution across named territories
    print("\nPOI distribution across named territories:")
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT a.name, a.zone_type, COUNT(p.id) AS poi_count "
                "FROM areas a "
                "LEFT JOIN places p "
                "  ON ST_Contains(a.boundary::geometry, p.coordinates::geometry) "
                "WHERE a.city = 'Versailles' "
                "  AND a.zone_type IN ('pvp', 'cooperative') "
                "GROUP BY a.name, a.zone_type "
                "ORDER BY poi_count DESC"
            )
        )
        for row in result:
            print(f"  {row[0]} ({row[1]}): {row[2]} POIs")

        # Total in personal hexes
        result = await conn.execute(
            text(
                "SELECT COUNT(DISTINCT p.id) "
                "FROM areas a "
                "JOIN places p "
                "  ON ST_Contains(a.boundary::geometry, p.coordinates::geometry) "
                "WHERE a.city = 'Versailles' AND a.zone_type = 'personal'"
            )
        )
        print(f"  Personal hexes (total): {result.scalar()} POIs")


if __name__ == "__main__":
    print("=== Versailles POI Seeder ===\n")
    asyncio.run(seed_pois())
```

**Step 2: Create the scripts directory if needed and run**

Run: `mkdir -p backend/scripts`

Run: `cd backend && python scripts/seed_versailles_pois.py`
Expected: ~100 places inserted, distribution printed.

**Step 3: Verify in DB**

Run: `cd backend && python -c "
import asyncio
from sqlalchemy import text
from app.db.session import async_engine

async def check():
    async with async_engine.connect() as conn:
        r = await conn.execute(text(\"SELECT COUNT(*) FROM places WHERE city = 'Versailles'\"))
        print(f'Total Versailles places: {r.scalar()}')
        r = await conn.execute(text(\"SELECT category, COUNT(*) FROM places WHERE city = 'Versailles' GROUP BY category ORDER BY COUNT(*) DESC\"))
        for row in r:
            print(f'  {row[0]}: {row[1]}')
asyncio.run(check())
"`

Expected: ~100 places across multiple categories.

**Step 4: Commit**

```bash
git add backend/scripts/seed_versailles_pois.py
git commit -m "feat: add Versailles POI seed script via Outscraper"
```

---

### Task 8: Frontend — Personal Zone Claiming UI

**Files:**
- Modify: `game/app/territory/[id].tsx`
- Modify: game territory API service file (find via `grep -r "claimTerritory" game/`)

**Step 1: Add claimHome API call to territory service**

Find the territory service file in the game app (likely in `game/services/` or `game/api/`). Add:

```typescript
export async function claimHome(territoryId: number): Promise<TerritoryResponse> {
  const response = await apiClient.post(`/game/territories/${territoryId}/claim-home`);
  return response.data;
}

export async function getResidents(territoryId: number): Promise<ResidentResponse[]> {
  const response = await apiClient.get(`/game/territories/${territoryId}/residents`);
  return response.data;
}

export interface ResidentResponse {
  user_id: number;
  username: string;
  home_claimed_at: string | null;
}
```

**Step 2: Add "Claim as Home" button to territory detail screen**

In `game/app/territory/[id].tsx`, add a section for personal zones (alongside existing claim/challenge/contribute sections):

```typescript
{territory.zone_type === "personal" && (
  <View style={styles.actionSection}>
    <Text style={styles.sectionTitle}>Personal Zone</Text>
    <Text style={styles.description}>
      Claim this hex as your home base. Multiple players can share the same hex.
    </Text>
    <TouchableOpacity
      style={styles.claimButton}
      onPress={handleClaimHome}
      disabled={isClaimingHome}
    >
      <Text style={styles.claimButtonText}>
        {isClaimingHome ? "Claiming..." : "Claim as Home"}
      </Text>
    </TouchableOpacity>

    {/* Residents list */}
    {residents.length > 0 && (
      <View style={styles.residentsSection}>
        <Text style={styles.sectionTitle}>
          Residents ({residents.length})
        </Text>
        {residents.map((r) => (
          <Text key={r.user_id} style={styles.residentName}>
            {r.username}
          </Text>
        ))}
      </View>
    )}
  </View>
)}
```

Add the handler and query hooks:

```typescript
const handleClaimHome = async () => {
  try {
    setIsClaimingHome(true);
    await claimHome(territory.id);
    // Refetch territory data
    queryClient.invalidateQueries(["territory", territory.id]);
    queryClient.invalidateQueries(["residents", territory.id]);
  } catch (error: any) {
    Alert.alert("Cannot Claim", error?.response?.data?.message || "Failed to claim home");
  } finally {
    setIsClaimingHome(false);
  }
};
```

**Step 3: Verify on device/simulator**

Launch the app, navigate to the map, tap a personal hex, and verify:
- The territory detail screen shows "Personal Zone" section
- "Claim as Home" button works
- Residents list appears after claiming

**Step 4: Commit**

```bash
git add game/
git commit -m "feat: add personal zone claiming UI to territory detail screen"
```

---

## Execution Order & Dependencies

```
Task 1 (User model) ──┐
Task 2 (Schemas)   ────┤
                       ▼
Task 3 (Migration) ────┐
                       ▼
Task 4 (claim_home) ───┤
Task 5 (get_residents) ┤
                       ▼
Task 6 (API endpoints) ┤
                       ▼
Task 7 (POI script) ───┤  (can run in parallel with Task 6)
Task 8 (Frontend)   ───┘  (can run in parallel with Task 7)
```

Tasks 1-6 are sequential. Tasks 7 and 8 can run in parallel with each other once Task 6 is done.
