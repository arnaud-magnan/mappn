"""Unit tests for ORM models.

Tests verify model structure, column types, constraints, and relationships
at the class level without requiring a database connection.
"""

import datetime

import pytest
from sqlalchemy import Integer, String, Float, inspect
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.models.user import User
from app.models.place import Place
from app.models.area import Area
from app.models.visit import Visit


class TestUserModel:
    """Tests for the User ORM model."""

    def test_user_inherits_from_base(self):
        assert issubclass(User, Base)

    def test_user_tablename(self):
        assert User.__tablename__ == "users"

    def test_user_has_all_columns(self):
        columns = {c.name for c in User.__table__.columns}
        expected = {"id", "username", "email", "password_hash", "xp", "level", "created_at"}
        assert expected == columns

    def test_user_id_is_integer_primary_key(self):
        col = User.__table__.columns["id"]
        assert col.primary_key is True
        assert isinstance(col.type, Integer)

    def test_user_username_is_unique(self):
        col = User.__table__.columns["username"]
        assert col.unique is True

    def test_user_email_is_unique(self):
        col = User.__table__.columns["email"]
        assert col.unique is True

    def test_user_username_is_not_nullable(self):
        col = User.__table__.columns["username"]
        assert col.nullable is False

    def test_user_email_is_not_nullable(self):
        col = User.__table__.columns["email"]
        assert col.nullable is False

    def test_user_password_hash_is_not_nullable(self):
        col = User.__table__.columns["password_hash"]
        assert col.nullable is False

    def test_user_xp_has_default(self):
        col = User.__table__.columns["xp"]
        assert col.default is not None

    def test_user_level_has_default(self):
        col = User.__table__.columns["level"]
        assert col.default is not None


class TestPlaceModel:
    """Tests for the Place ORM model."""

    def test_place_inherits_from_base(self):
        assert issubclass(Place, Base)

    def test_place_tablename(self):
        assert Place.__tablename__ == "places"

    def test_place_has_all_columns(self):
        columns = {c.name for c in Place.__table__.columns}
        expected = {
            "id", "google_place_id", "name", "category", "coordinates",
            "address", "city", "country", "busyness_data", "busyness_updated_at",
        }
        assert expected == columns

    def test_place_id_is_integer_primary_key(self):
        col = Place.__table__.columns["id"]
        assert col.primary_key is True
        assert isinstance(col.type, Integer)

    def test_place_coordinates_is_geography_point(self):
        from geoalchemy2 import Geography
        col = Place.__table__.columns["coordinates"]
        assert isinstance(col.type, Geography)
        assert col.type.geometry_type == "POINT"
        assert col.type.srid == 4326

    def test_place_busyness_data_is_jsonb(self):
        col = Place.__table__.columns["busyness_data"]
        assert isinstance(col.type, JSONB)

    def test_place_busyness_updated_at_is_nullable(self):
        col = Place.__table__.columns["busyness_updated_at"]
        assert col.nullable is True

    def test_place_google_place_id_is_not_nullable(self):
        col = Place.__table__.columns["google_place_id"]
        assert col.nullable is False

    def test_place_name_is_not_nullable(self):
        col = Place.__table__.columns["name"]
        assert col.nullable is False


class TestAreaModel:
    """Tests for the Area ORM model."""

    def test_area_inherits_from_base(self):
        assert issubclass(Area, Base)

    def test_area_tablename(self):
        assert Area.__tablename__ == "areas"

    def test_area_has_all_columns(self):
        columns = {c.name for c in Area.__table__.columns}
        expected = {"id", "name", "city", "boundary", "zone_type", "busyness_score"}
        assert expected == columns

    def test_area_id_is_integer_primary_key(self):
        col = Area.__table__.columns["id"]
        assert col.primary_key is True
        assert isinstance(col.type, Integer)

    def test_area_boundary_is_geography_polygon(self):
        from geoalchemy2 import Geography
        col = Area.__table__.columns["boundary"]
        assert isinstance(col.type, Geography)
        assert col.type.geometry_type == "POLYGON"
        assert col.type.srid == 4326

    def test_area_zone_type_is_string(self):
        col = Area.__table__.columns["zone_type"]
        assert isinstance(col.type, String)

    def test_area_busyness_score_is_nullable(self):
        col = Area.__table__.columns["busyness_score"]
        assert col.nullable is True


class TestVisitModel:
    """Tests for the Visit ORM model."""

    def test_visit_inherits_from_base(self):
        assert issubclass(Visit, Base)

    def test_visit_tablename(self):
        assert Visit.__tablename__ == "visits"

    def test_visit_has_all_columns(self):
        columns = {c.name for c in Visit.__table__.columns}
        expected = {
            "id", "user_id", "place_id", "area_id",
            "started_at", "ended_at", "duration_seconds",
        }
        assert expected == columns

    def test_visit_id_is_integer_primary_key(self):
        col = Visit.__table__.columns["id"]
        assert col.primary_key is True
        assert isinstance(col.type, Integer)

    def test_visit_user_id_has_foreign_key(self):
        col = Visit.__table__.columns["user_id"]
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "users.id" in fk_targets

    def test_visit_place_id_has_foreign_key(self):
        col = Visit.__table__.columns["place_id"]
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "places.id" in fk_targets

    def test_visit_area_id_has_foreign_key_and_is_nullable(self):
        col = Visit.__table__.columns["area_id"]
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "areas.id" in fk_targets
        assert col.nullable is True

    def test_visit_user_id_is_not_nullable(self):
        col = Visit.__table__.columns["user_id"]
        assert col.nullable is False

    def test_visit_place_id_is_not_nullable(self):
        col = Visit.__table__.columns["place_id"]
        assert col.nullable is False

    def test_visit_started_at_is_not_nullable(self):
        col = Visit.__table__.columns["started_at"]
        assert col.nullable is False


class TestModelsInit:
    """Tests for models package re-exports."""

    def test_models_init_exports_user(self):
        from app.models import User as ExportedUser
        assert ExportedUser is User

    def test_models_init_exports_place(self):
        from app.models import Place as ExportedPlace
        assert ExportedPlace is Place

    def test_models_init_exports_area(self):
        from app.models import Area as ExportedArea
        assert ExportedArea is Area

    def test_models_init_exports_visit(self):
        from app.models import Visit as ExportedVisit
        assert ExportedVisit is Visit

    def test_models_init_exports_base(self):
        from app.models import Base as ExportedBase
        assert ExportedBase is Base


class TestModelRelationships:
    """Tests for foreign key relationships between models."""

    def test_all_models_registered_in_metadata(self):
        table_names = set(Base.metadata.tables.keys())
        assert "users" in table_names
        assert "places" in table_names
        assert "areas" in table_names
        assert "visits" in table_names

    def test_visit_user_id_references_users_table(self):
        visit_table = Visit.__table__
        user_fks = [
            fk for col in visit_table.columns
            for fk in col.foreign_keys
            if fk.target_fullname == "users.id"
        ]
        assert len(user_fks) == 1

    def test_visit_place_id_references_places_table(self):
        visit_table = Visit.__table__
        place_fks = [
            fk for col in visit_table.columns
            for fk in col.foreign_keys
            if fk.target_fullname == "places.id"
        ]
        assert len(place_fks) == 1

    def test_visit_area_id_references_areas_table(self):
        visit_table = Visit.__table__
        area_fks = [
            fk for col in visit_table.columns
            for fk in col.foreign_keys
            if fk.target_fullname == "areas.id"
        ]
        assert len(area_fks) == 1
