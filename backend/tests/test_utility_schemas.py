"""Unit tests for utility Pydantic schemas and JournalNote model.

Tests cover:
- JournalNote ORM model structure (columns, FKs, types, constraints)
- JournalNote import/export from models package
- UserStatsResponse fields and from_attributes config
- AchievementResponse fields including progress, threshold, earned, earned_at
- JournalEntryResponse fields including note and photo_url nullable
- JournalNoteRequest text max length validation (1000 chars)
- HeatmapAreaResponse fields including boundary_geojson and visited
- HeatmapResponse nested areas list with aggregates
- PassportStampResponse fields
- CityPassportResponse nested stamps with badge_earned
- All response schemas have model_config with from_attributes=True
"""

import datetime
from typing import Optional

import pytest
from pydantic import ValidationError
from sqlalchemy import Integer, String, DateTime

from app.db.base import Base


# ---------------------------------------------------------------------------
# JournalNote model tests
# ---------------------------------------------------------------------------


class TestJournalNoteModel:
    """Tests for the JournalNote ORM model."""

    def test_journal_note_inherits_from_base(self):
        from app.models.journal import JournalNote
        assert issubclass(JournalNote, Base)

    def test_journal_note_tablename(self):
        from app.models.journal import JournalNote
        assert JournalNote.__tablename__ == "journal_notes"

    def test_journal_note_has_all_columns(self):
        from app.models.journal import JournalNote
        columns = {c.name for c in JournalNote.__table__.columns}
        expected = {"id", "visit_id", "user_id", "text", "photo_url", "created_at"}
        assert expected == columns

    def test_journal_note_id_is_integer_primary_key(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["id"]
        assert col.primary_key is True
        assert isinstance(col.type, Integer)

    def test_journal_note_visit_id_has_foreign_key(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["visit_id"]
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "visits.id" in fk_targets

    def test_journal_note_visit_id_is_not_nullable(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["visit_id"]
        assert col.nullable is False

    def test_journal_note_user_id_has_foreign_key(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["user_id"]
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "users.id" in fk_targets

    def test_journal_note_user_id_is_not_nullable(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["user_id"]
        assert col.nullable is False

    def test_journal_note_text_is_nullable(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["text"]
        assert col.nullable is True

    def test_journal_note_text_max_length(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["text"]
        assert isinstance(col.type, String)
        assert col.type.length == 1000

    def test_journal_note_photo_url_is_nullable(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["photo_url"]
        assert col.nullable is True

    def test_journal_note_created_at_is_datetime_with_timezone(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["created_at"]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True

    def test_journal_note_created_at_is_not_nullable(self):
        from app.models.journal import JournalNote
        col = JournalNote.__table__.columns["created_at"]
        assert col.nullable is False


class TestJournalNoteModelInit:
    """Tests for JournalNote export in models __init__.py."""

    def test_models_init_exports_journal_note(self):
        from app.models import JournalNote
        from app.models.journal import JournalNote as DirectJournalNote
        assert JournalNote is DirectJournalNote

    def test_journal_note_in_all(self):
        import app.models as models_pkg
        assert "JournalNote" in models_pkg.__all__

    def test_journal_notes_registered_in_metadata(self):
        table_names = set(Base.metadata.tables.keys())
        assert "journal_notes" in table_names


# ---------------------------------------------------------------------------
# Utility schema tests
# ---------------------------------------------------------------------------


class TestUserStatsResponse:
    """Tests for UserStatsResponse schema."""

    def test_user_stats_response_from_attributes_config(self):
        from app.schemas.utility import UserStatsResponse
        assert UserStatsResponse.model_config.get("from_attributes") is True

    def test_user_stats_response_fields(self):
        from app.schemas.utility import UserStatsResponse
        resp = UserStatsResponse(
            places_count=10,
            cities_count=3,
            countries_count=2,
            total_duration_seconds=36000,
        )
        assert resp.places_count == 10
        assert resp.cities_count == 3
        assert resp.countries_count == 2
        assert resp.total_duration_seconds == 36000

    def test_user_stats_response_requires_all_fields(self):
        from app.schemas.utility import UserStatsResponse
        with pytest.raises(ValidationError):
            UserStatsResponse(places_count=10)  # type: ignore[call-arg]


class TestAchievementResponse:
    """Tests for AchievementResponse schema."""

    def test_achievement_response_from_attributes_config(self):
        from app.schemas.utility import AchievementResponse
        assert AchievementResponse.model_config.get("from_attributes") is True

    def test_achievement_response_fields(self):
        from app.schemas.utility import AchievementResponse
        resp = AchievementResponse(
            id="wanderer",
            name="Wanderer",
            description="Visit 10 distinct neighborhoods",
            category="explorer",
            progress=5,
            threshold=10,
            earned=False,
            earned_at=None,
        )
        assert resp.id == "wanderer"
        assert resp.name == "Wanderer"
        assert resp.description == "Visit 10 distinct neighborhoods"
        assert resp.category == "explorer"
        assert resp.progress == 5
        assert resp.threshold == 10
        assert resp.earned is False
        assert resp.earned_at is None

    def test_achievement_response_earned_with_timestamp(self):
        from app.schemas.utility import AchievementResponse
        now = datetime.datetime(2026, 1, 15, 12, 0, tzinfo=datetime.timezone.utc)
        resp = AchievementResponse(
            id="foodie",
            name="Foodie",
            description="Visit 50 restaurants",
            category="categories",
            progress=50,
            threshold=50,
            earned=True,
            earned_at=now,
        )
        assert resp.earned is True
        assert resp.earned_at == now


class TestJournalEntryResponse:
    """Tests for JournalEntryResponse schema."""

    def test_journal_entry_response_from_attributes_config(self):
        from app.schemas.utility import JournalEntryResponse
        assert JournalEntryResponse.model_config.get("from_attributes") is True

    def test_journal_entry_response_fields(self):
        from app.schemas.utility import JournalEntryResponse
        resp = JournalEntryResponse(
            visit_id=1,
            place_id=10,
            place_name="Test Cafe",
            area_id=5,
            city="Paris",
            started_at=datetime.datetime(2026, 1, 1, 10, 0, tzinfo=datetime.timezone.utc),
            duration_seconds=1800,
            note="Great coffee!",
            photo_url="https://example.com/photo.jpg",
        )
        assert resp.visit_id == 1
        assert resp.place_id == 10
        assert resp.place_name == "Test Cafe"
        assert resp.area_id == 5
        assert resp.city == "Paris"
        assert resp.duration_seconds == 1800
        assert resp.note == "Great coffee!"
        assert resp.photo_url == "https://example.com/photo.jpg"

    def test_journal_entry_response_nullable_fields(self):
        from app.schemas.utility import JournalEntryResponse
        resp = JournalEntryResponse(
            visit_id=1,
            place_id=10,
            place_name="Test Cafe",
            area_id=None,
            city=None,
            started_at=datetime.datetime(2026, 1, 1, 10, 0, tzinfo=datetime.timezone.utc),
            duration_seconds=None,
            note=None,
            photo_url=None,
        )
        assert resp.area_id is None
        assert resp.city is None
        assert resp.duration_seconds is None
        assert resp.note is None
        assert resp.photo_url is None


class TestJournalNoteRequest:
    """Tests for JournalNoteRequest schema."""

    def test_journal_note_request_valid(self):
        from app.schemas.utility import JournalNoteRequest
        req = JournalNoteRequest(text="A lovely visit", photo_url="https://example.com/photo.jpg")
        assert req.text == "A lovely visit"
        assert req.photo_url == "https://example.com/photo.jpg"

    def test_journal_note_request_text_optional(self):
        from app.schemas.utility import JournalNoteRequest
        req = JournalNoteRequest(photo_url="https://example.com/photo.jpg")
        assert req.text is None

    def test_journal_note_request_photo_url_optional(self):
        from app.schemas.utility import JournalNoteRequest
        req = JournalNoteRequest(text="Just a note")
        assert req.photo_url is None

    def test_journal_note_request_both_optional(self):
        from app.schemas.utility import JournalNoteRequest
        req = JournalNoteRequest()
        assert req.text is None
        assert req.photo_url is None

    def test_journal_note_request_text_max_length_1000(self):
        from app.schemas.utility import JournalNoteRequest
        # Exactly 1000 chars should be valid
        req = JournalNoteRequest(text="a" * 1000)
        assert len(req.text) == 1000

    def test_journal_note_request_rejects_text_over_1000(self):
        from app.schemas.utility import JournalNoteRequest
        with pytest.raises(ValidationError) as exc_info:
            JournalNoteRequest(text="a" * 1001)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("text",) for e in errors)


class TestHeatmapAreaResponse:
    """Tests for HeatmapAreaResponse schema."""

    def test_heatmap_area_response_from_attributes_config(self):
        from app.schemas.utility import HeatmapAreaResponse
        assert HeatmapAreaResponse.model_config.get("from_attributes") is True

    def test_heatmap_area_response_fields(self):
        from app.schemas.utility import HeatmapAreaResponse
        geojson = {"type": "Polygon", "coordinates": [[[2.35, 48.85], [2.36, 48.85], [2.36, 48.86], [2.35, 48.85]]]}
        resp = HeatmapAreaResponse(
            id=1,
            name="Presqu'ile",
            city="Lyon",
            boundary_geojson=geojson,
            visited=True,
            visited_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        )
        assert resp.id == 1
        assert resp.name == "Presqu'ile"
        assert resp.city == "Lyon"
        assert resp.boundary_geojson == geojson
        assert resp.visited is True
        assert resp.visited_at is not None

    def test_heatmap_area_response_unvisited(self):
        from app.schemas.utility import HeatmapAreaResponse
        resp = HeatmapAreaResponse(
            id=2,
            name="Croix-Rousse",
            city="Lyon",
            boundary_geojson={"type": "Polygon", "coordinates": []},
            visited=False,
            visited_at=None,
        )
        assert resp.visited is False
        assert resp.visited_at is None


class TestHeatmapResponse:
    """Tests for HeatmapResponse schema."""

    def test_heatmap_response_from_attributes_config(self):
        from app.schemas.utility import HeatmapResponse
        assert HeatmapResponse.model_config.get("from_attributes") is True

    def test_heatmap_response_fields(self):
        from app.schemas.utility import HeatmapResponse, HeatmapAreaResponse
        area = HeatmapAreaResponse(
            id=1,
            name="Presqu'ile",
            city="Lyon",
            boundary_geojson={"type": "Polygon", "coordinates": []},
            visited=True,
            visited_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        )
        resp = HeatmapResponse(
            areas=[area],
            total_areas=10,
            visited_areas=1,
            explored_pct=10.0,
        )
        assert len(resp.areas) == 1
        assert resp.total_areas == 10
        assert resp.visited_areas == 1
        assert resp.explored_pct == 10.0

    def test_heatmap_response_empty(self):
        from app.schemas.utility import HeatmapResponse
        resp = HeatmapResponse(
            areas=[],
            total_areas=0,
            visited_areas=0,
            explored_pct=0.0,
        )
        assert resp.areas == []
        assert resp.explored_pct == 0.0


class TestPassportStampResponse:
    """Tests for PassportStampResponse schema."""

    def test_passport_stamp_response_from_attributes_config(self):
        from app.schemas.utility import PassportStampResponse
        assert PassportStampResponse.model_config.get("from_attributes") is True

    def test_passport_stamp_response_fields(self):
        from app.schemas.utility import PassportStampResponse
        resp = PassportStampResponse(
            area_id=1,
            name="Presqu'ile",
            visited=True,
            visited_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        )
        assert resp.area_id == 1
        assert resp.name == "Presqu'ile"
        assert resp.visited is True
        assert resp.visited_at is not None

    def test_passport_stamp_response_unvisited(self):
        from app.schemas.utility import PassportStampResponse
        resp = PassportStampResponse(
            area_id=2,
            name="Croix-Rousse",
            visited=False,
            visited_at=None,
        )
        assert resp.visited is False
        assert resp.visited_at is None


class TestCityPassportResponse:
    """Tests for CityPassportResponse schema."""

    def test_city_passport_response_from_attributes_config(self):
        from app.schemas.utility import CityPassportResponse
        assert CityPassportResponse.model_config.get("from_attributes") is True

    def test_city_passport_response_fields(self):
        from app.schemas.utility import CityPassportResponse, PassportStampResponse
        stamp = PassportStampResponse(
            area_id=1,
            name="Presqu'ile",
            visited=True,
            visited_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        )
        resp = CityPassportResponse(
            city="Lyon",
            total_neighborhoods=20,
            visited_count=5,
            stamps=[stamp],
            badge_earned=False,
            explored_pct=25.0,
        )
        assert resp.city == "Lyon"
        assert resp.total_neighborhoods == 20
        assert resp.visited_count == 5
        assert len(resp.stamps) == 1
        assert resp.badge_earned is False
        assert resp.explored_pct == 25.0

    def test_city_passport_response_badge_earned(self):
        from app.schemas.utility import CityPassportResponse
        resp = CityPassportResponse(
            city="Lyon",
            total_neighborhoods=2,
            visited_count=2,
            stamps=[],
            badge_earned=True,
            explored_pct=100.0,
        )
        assert resp.badge_earned is True
        assert resp.explored_pct == 100.0


# ---------------------------------------------------------------------------
# ORM compatibility: all response schemas must have from_attributes=True
# ---------------------------------------------------------------------------


class TestUtilityORMCompatibility:
    """All utility response schemas must have model_config with from_attributes=True."""

    @pytest.mark.parametrize(
        "schema_name",
        [
            "UserStatsResponse",
            "AchievementResponse",
            "JournalEntryResponse",
            "HeatmapAreaResponse",
            "HeatmapResponse",
            "PassportStampResponse",
            "CityPassportResponse",
        ],
    )
    def test_response_schema_has_from_attributes(self, schema_name: str) -> None:
        """Every response schema must have model_config = ConfigDict(from_attributes=True)."""
        import app.schemas.utility as utility_mod
        schema_cls = getattr(utility_mod, schema_name)
        assert schema_cls.model_config.get("from_attributes") is True, (
            f"{schema_name} is missing model_config with from_attributes=True"
        )
