"""Unit tests for the initial Alembic migration structure.

Tests verify the migration file contains the correct operations
(PostGIS extension, tables, indexes) without requiring a database.
Since the migration module imports from `alembic.op` which requires
the Alembic runtime context, we test by reading the source file directly.
"""

import os

import pytest

MIGRATION_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "alembic",
    "versions",
    "001_initial_schema.py",
)


@pytest.fixture
def migration_source():
    """Read the migration source file."""
    with open(MIGRATION_PATH) as f:
        return f.read()


class TestMigration001Structure:
    """Tests for 001_initial_schema.py migration structure."""

    def test_migration_file_exists(self):
        assert os.path.isfile(MIGRATION_PATH)

    def test_revision_id_is_001(self, migration_source):
        assert 'revision = "001"' in migration_source

    def test_down_revision_is_none(self, migration_source):
        assert "down_revision = None" in migration_source

    def test_has_upgrade_function(self, migration_source):
        assert "def upgrade()" in migration_source

    def test_has_downgrade_function(self, migration_source):
        assert "def downgrade()" in migration_source

    def test_creates_postgis_extension(self, migration_source):
        assert "CREATE EXTENSION IF NOT EXISTS postgis" in migration_source

    def test_creates_users_table(self, migration_source):
        assert '"users"' in migration_source

    def test_creates_places_table(self, migration_source):
        assert '"places"' in migration_source

    def test_creates_areas_table(self, migration_source):
        assert '"areas"' in migration_source

    def test_creates_visits_table(self, migration_source):
        assert '"visits"' in migration_source

    def test_creates_gist_index_on_places_coordinates(self, migration_source):
        assert "ix_places_coordinates" in migration_source
        assert "GIST" in migration_source

    def test_creates_gist_index_on_areas_boundary(self, migration_source):
        assert "ix_areas_boundary" in migration_source

    def test_creates_index_on_visits_user_id(self, migration_source):
        assert "ix_visits_user_id" in migration_source

    def test_creates_index_on_visits_place_id(self, migration_source):
        assert "ix_visits_place_id" in migration_source

    def test_creates_index_on_places_category(self, migration_source):
        assert "ix_places_category" in migration_source

    def test_has_user_unique_constraints(self, migration_source):
        assert "uq_users_username" in migration_source
        assert "uq_users_email" in migration_source

    def test_has_visits_foreign_keys(self, migration_source):
        assert 'ForeignKey("users.id")' in migration_source
        assert 'ForeignKey("places.id")' in migration_source
        assert 'ForeignKey("areas.id")' in migration_source

    def test_has_geography_point(self, migration_source):
        assert 'geometry_type="POINT"' in migration_source
        assert "srid=4326" in migration_source

    def test_has_geography_polygon(self, migration_source):
        assert 'geometry_type="POLYGON"' in migration_source

    def test_downgrade_drops_all_tables(self, migration_source):
        # Extract just the downgrade function body
        downgrade_start = migration_source.index("def downgrade()")
        downgrade_body = migration_source[downgrade_start:]
        assert "visits" in downgrade_body
        assert "areas" in downgrade_body
        assert "places" in downgrade_body
        assert "users" in downgrade_body

    def test_downgrade_drops_postgis_extension(self, migration_source):
        downgrade_start = migration_source.index("def downgrade()")
        downgrade_body = migration_source[downgrade_start:]
        assert "DROP EXTENSION IF EXISTS postgis" in downgrade_body

    def test_downgrade_drops_tables_in_correct_order(self, migration_source):
        """Visits must be dropped before users/places/areas due to FK dependencies."""
        downgrade_start = migration_source.index("def downgrade()")
        downgrade_body = migration_source[downgrade_start:]
        # Find positions of drop_table calls in the downgrade function
        visits_pos = downgrade_body.index('drop_table("visits")')
        areas_pos = downgrade_body.index('drop_table("areas")')
        places_pos = downgrade_body.index('drop_table("places")')
        users_pos = downgrade_body.index('drop_table("users")')
        assert visits_pos < areas_pos
        assert visits_pos < places_pos
        assert visits_pos < users_pos

    def test_upgrade_creates_jsonb_column(self, migration_source):
        assert "JSONB" in migration_source

    def test_upgrade_has_server_defaults_for_xp_and_level(self, migration_source):
        assert 'server_default="0"' in migration_source
        assert 'server_default="1"' in migration_source

    def test_visits_area_id_is_nullable(self, migration_source):
        # The area_id column in the visits table should have nullable=True
        # Search for the area_id line in the migration source
        lines = migration_source.split("\n")
        area_id_lines = [l for l in lines if "area_id" in l]
        assert len(area_id_lines) >= 1
        # The area_id column definition should contain nullable=True
        area_id_def = area_id_lines[0]
        assert "nullable=True" in area_id_def
