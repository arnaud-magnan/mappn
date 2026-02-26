"""Initial schema: PostGIS extension, shared tables, and indexes.

Creates the four shared entity tables (users, places, areas, visits) with
PostGIS Geography columns and GIST spatial indexes. This migration is the
foundation for both Mappn apps.

Revision ID: 001
Revises: None
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geography


# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create PostGIS extension, shared tables, and indexes."""

    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # --- Users table ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    # --- Places table ---
    op.create_table(
        "places",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("google_place_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column(
            "coordinates",
            Geography(geometry_type="POINT", srid=4326),
            nullable=False,
        ),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("busyness_data", JSONB(), nullable=True),
        sa.Column("busyness_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("google_place_id", name="uq_places_google_place_id"),
    )
    # GIST index for spatial queries (ST_DWithin, ST_Distance)
    op.execute(
        "CREATE INDEX ix_places_coordinates ON places USING GIST (coordinates)"
    )
    # Standard index for category filtering
    op.create_index("ix_places_category", "places", ["category"])

    # --- Areas table ---
    op.create_table(
        "areas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column(
            "boundary",
            Geography(geometry_type="POLYGON", srid=4326),
            nullable=False,
        ),
        sa.Column("zone_type", sa.String(50), nullable=True),
        sa.Column("busyness_score", sa.Float(), nullable=True),
    )
    # GIST index for spatial containment queries (ST_Contains)
    op.execute(
        "CREATE INDEX ix_areas_boundary ON areas USING GIST (boundary)"
    )

    # --- Visits table ---
    op.create_table(
        "visits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("place_id", sa.Integer(), sa.ForeignKey("places.id"), nullable=False),
        sa.Column("area_id", sa.Integer(), sa.ForeignKey("areas.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
    )
    # Standard indexes for visit queries
    op.create_index("ix_visits_user_id", "visits", ["user_id"])
    op.create_index("ix_visits_place_id", "visits", ["place_id"])


def downgrade() -> None:
    """Drop all shared tables and PostGIS extension."""

    # Drop tables in reverse order (respecting FK dependencies)
    op.drop_table("visits")
    op.drop_table("areas")
    op.drop_table("places")
    op.drop_table("users")

    # Drop PostGIS extension
    op.execute("DROP EXTENSION IF EXISTS postgis CASCADE")
