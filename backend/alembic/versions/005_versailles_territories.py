"""Add home territory columns to users, seed Versailles named areas + hex grid.

Adds home_territory_id and home_claimed_at columns to the users table,
seeds 6 named areas (pvp/cooperative) for the Versailles Quartier Notre-Dame,
creates corresponding Territory records, then generates a hex grid of personal
territories covering the remaining bounding-box space.

Revision ID: 005
Revises: 004
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add home territory columns, seed Versailles areas/territories, generate hex grid."""

    # ------------------------------------------------------------------ #
    # 1. Schema changes: add home territory columns to users table
    # ------------------------------------------------------------------ #
    op.add_column(
        "users",
        sa.Column("home_territory_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("home_claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_home_territory_id", "users", ["home_territory_id"])
    op.create_foreign_key(
        "fk_users_home_territory_id",
        "users",
        "territories",
        ["home_territory_id"],
        ["id"],
    )

    # ------------------------------------------------------------------ #
    # 2. Seed 6 named areas + territories for Versailles
    # ------------------------------------------------------------------ #
    conn = op.get_bind()

    named_areas = [
        {
            "name": "Château de Versailles & Jardins",
            "zone_type": "pvp",
            "wkt": "SRID=4326;POLYGON((2.0830 48.8130, 2.1190 48.8130, 2.1190 48.8000, 2.0830 48.8000, 2.0830 48.8130))",
        },
        {
            "name": "Place d'Armes",
            "zone_type": "pvp",
            "wkt": "SRID=4326;POLYGON((2.1190 48.8090, 2.1260 48.8090, 2.1260 48.8030, 2.1190 48.8030, 2.1190 48.8090))",
        },
        {
            "name": "Marché Notre-Dame",
            "zone_type": "cooperative",
            "wkt": "SRID=4326;POLYGON((2.1280 48.8055, 2.1340 48.8055, 2.1340 48.8020, 2.1280 48.8020, 2.1280 48.8055))",
        },
        {
            "name": "Cathédrale Saint-Louis",
            "zone_type": "cooperative",
            "wkt": "SRID=4326;POLYGON((2.1230 48.8030, 2.1280 48.8030, 2.1280 48.7990, 2.1230 48.7990, 2.1230 48.8030))",
        },
        {
            "name": "Rue de la Paroisse",
            "zone_type": "cooperative",
            "wkt": "SRID=4326;POLYGON((2.1290 48.8090, 2.1320 48.8090, 2.1320 48.8055, 2.1290 48.8055, 2.1290 48.8090))",
        },
        {
            "name": "Parc Balbi & Pièce d'Eau des Suisses",
            "zone_type": "pvp",
            "wkt": "SRID=4326;POLYGON((2.1100 48.8000, 2.1250 48.8000, 2.1250 48.7920, 2.1100 48.7920, 2.1100 48.8000))",
        },
    ]

    insert_area_sql = sa.text(
        "INSERT INTO areas (name, city, boundary, zone_type) "
        "VALUES (:name, 'Versailles', ST_GeogFromText(:wkt), :zone_type) "
        "RETURNING id"
    )

    insert_territory_sql = sa.text(
        "INSERT INTO territories (area_id, zone_type, passive_reward_rate, familiarity_scores) "
        "VALUES (:area_id, :zone_type, 1.0, '{}')"
    )

    for area in named_areas:
        result = conn.execute(
            insert_area_sql,
            {"name": area["name"], "wkt": area["wkt"], "zone_type": area["zone_type"]},
        )
        area_id = result.scalar_one()
        conn.execute(
            insert_territory_sql,
            {"area_id": area_id, "zone_type": area["zone_type"]},
        )

    # ------------------------------------------------------------------ #
    # 3. Generate hex grid for remaining space (personal territories)
    # ------------------------------------------------------------------ #
    hex_grid_sql = sa.text("""
        WITH bounds AS (
            SELECT ST_Transform(
                ST_MakeEnvelope(2.100, 48.790, 2.145, 48.815, 4326),
                2154
            ) AS geom
        ),
        hex_raw AS (
            SELECT (h).geom, (h).i, (h).j
            FROM bounds,
                 LATERAL ST_HexagonGrid(100, bounds.geom) AS h
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
                  AND ST_Contains(named.boundary::geometry, ST_Centroid(geom))
            )
        ),
        numbered AS (
            SELECT geom, ROW_NUMBER() OVER (ORDER BY j, i) AS n
            FROM filtered
        )
        INSERT INTO areas (name, city, boundary, zone_type)
        SELECT 'Hex-' || n, 'Versailles', geom::geography, 'personal'
        FROM numbered
    """)
    conn.execute(hex_grid_sql)

    # Create territory records for each personal hex
    hex_territory_sql = sa.text("""
        INSERT INTO territories (area_id, zone_type, passive_reward_rate, familiarity_scores)
        SELECT a.id, 'personal', 1.0, '{}'
        FROM areas a
        WHERE a.zone_type = 'personal' AND a.city = 'Versailles'
          AND NOT EXISTS (SELECT 1 FROM territories t WHERE t.area_id = a.id)
    """)
    conn.execute(hex_territory_sql)


def downgrade() -> None:
    """Remove Versailles seed data and home territory columns from users."""

    conn = op.get_bind()

    # 1. Clear home_territory_id references from users
    conn.execute(sa.text(
        "UPDATE users SET home_territory_id = NULL, home_claimed_at = NULL"
    ))

    # 2. Delete territories where area city = 'Versailles'
    conn.execute(sa.text(
        "DELETE FROM territories "
        "WHERE area_id IN (SELECT id FROM areas WHERE city = 'Versailles')"
    ))

    # 3. Delete areas where city = 'Versailles'
    conn.execute(sa.text("DELETE FROM areas WHERE city = 'Versailles'"))

    # 4. Drop FK, index, and columns from users
    op.drop_constraint("fk_users_home_territory_id", "users", type_="foreignkey")
    op.drop_index("ix_users_home_territory_id", table_name="users")
    op.drop_column("users", "home_claimed_at")
    op.drop_column("users", "home_territory_id")
