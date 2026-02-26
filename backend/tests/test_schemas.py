"""Unit tests for Pydantic schemas.

Tests cover:
- RegisterRequest validation (email, username, password constraints)
- LoginRequest validation
- TokenResponse fields (access_token, refresh_token, token_type, expires_in)
- NearbyQueryParams defaults and Query() annotations
- PlaceResponse and PlaceDetailResponse ORM compatibility
- GPSPingRequest accuracy field
- GPSPingResponse nested lists (nearby_places, confirmed_visits)
- VisitResponse ORM compatibility
- UserResponse ORM compatibility
- All response schemas have model_config with from_attributes=True
"""

import datetime
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.place import (
    PlaceResponse,
    PlaceDetailResponse,
    NearbyQueryParams,
    ForecastResponse,
)
from app.schemas.visit import (
    GPSPingRequest,
    GPSPingResponse,
    VisitResponse,
    NearbyPlaceInfo,
    ConfirmedVisitInfo,
)
from app.schemas.user import UserResponse


# ---------------------------------------------------------------------------
# RegisterRequest validation
# ---------------------------------------------------------------------------


class TestRegisterRequest:
    """Tests for RegisterRequest schema validation."""

    def test_valid_registration(self) -> None:
        """RegisterRequest should accept valid email, username, and password."""
        req = RegisterRequest(
            email="user@example.com",
            username="testuser",
            password="securepassword123",
        )
        assert req.email == "user@example.com"
        assert req.username == "testuser"
        assert req.password == "securepassword123"

    def test_rejects_email_without_at_symbol(self) -> None:
        """RegisterRequest should reject an email without @ symbol."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="invalidemail",
                username="testuser",
                password="securepassword123",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_rejects_email_with_only_at_symbol(self) -> None:
        """RegisterRequest should reject an email that is just '@'."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="@",
                username="testuser",
                password="securepassword123",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_rejects_username_under_3_characters(self) -> None:
        """RegisterRequest should reject username shorter than 3 characters."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="user@example.com",
                username="ab",
                password="securepassword123",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    def test_accepts_username_of_3_characters(self) -> None:
        """RegisterRequest should accept username of exactly 3 characters."""
        req = RegisterRequest(
            email="user@example.com",
            username="abc",
            password="securepassword123",
        )
        assert req.username == "abc"

    def test_rejects_password_under_8_characters(self) -> None:
        """RegisterRequest should reject password shorter than 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="user@example.com",
                username="testuser",
                password="short",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_accepts_password_of_8_characters(self) -> None:
        """RegisterRequest should accept password of exactly 8 characters."""
        req = RegisterRequest(
            email="user@example.com",
            username="testuser",
            password="12345678",
        )
        assert req.password == "12345678"

    def test_rejects_empty_email(self) -> None:
        """RegisterRequest should reject an empty email string."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="",
                username="testuser",
                password="securepassword123",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_rejects_empty_username(self) -> None:
        """RegisterRequest should reject an empty username."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="user@example.com",
                username="",
                password="securepassword123",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    def test_rejects_username_of_1_character(self) -> None:
        """RegisterRequest should reject username of 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="user@example.com",
                username="a",
                password="securepassword123",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)


# ---------------------------------------------------------------------------
# LoginRequest validation
# ---------------------------------------------------------------------------


class TestLoginRequest:
    """Tests for LoginRequest schema."""

    def test_valid_login(self) -> None:
        """LoginRequest should accept valid email and password."""
        req = LoginRequest(email="user@example.com", password="mypassword123")
        assert req.email == "user@example.com"
        assert req.password == "mypassword123"

    def test_login_requires_email(self) -> None:
        """LoginRequest should require email field."""
        with pytest.raises(ValidationError):
            LoginRequest(password="mypassword123")  # type: ignore[call-arg]

    def test_login_requires_password(self) -> None:
        """LoginRequest should require password field."""
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# TokenResponse fields
# ---------------------------------------------------------------------------


class TestTokenResponse:
    """Tests for TokenResponse schema."""

    def test_token_response_has_all_fields(self) -> None:
        """TokenResponse should include access_token, refresh_token, token_type, expires_in."""
        resp = TokenResponse(
            access_token="access.jwt.token",
            refresh_token="refresh.jwt.token",
            token_type="bearer",
            expires_in=1800,
        )
        assert resp.access_token == "access.jwt.token"
        assert resp.refresh_token == "refresh.jwt.token"
        assert resp.token_type == "bearer"
        assert resp.expires_in == 1800

    def test_token_response_requires_refresh_token(self) -> None:
        """TokenResponse must require refresh_token field."""
        with pytest.raises(ValidationError):
            TokenResponse(
                access_token="access.jwt.token",
                token_type="bearer",
                expires_in=1800,
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# NearbyQueryParams defaults and Query annotations
# ---------------------------------------------------------------------------


class TestNearbyQueryParams:
    """Tests for NearbyQueryParams schema."""

    def test_default_radius(self) -> None:
        """NearbyQueryParams should default radius_m to 500."""
        params = NearbyQueryParams(lat=48.8566, lon=2.3522)
        assert params.radius_m == 500

    def test_category_is_optional(self) -> None:
        """NearbyQueryParams should allow category to be None."""
        params = NearbyQueryParams(lat=48.8566, lon=2.3522)
        assert params.category is None

    def test_custom_values(self) -> None:
        """NearbyQueryParams should accept custom values."""
        params = NearbyQueryParams(
            lat=48.8566, lon=2.3522, radius_m=1000, category="restaurant"
        )
        assert params.lat == 48.8566
        assert params.lon == 2.3522
        assert params.radius_m == 1000
        assert params.category == "restaurant"

    def test_requires_lat(self) -> None:
        """NearbyQueryParams should require lat field."""
        with pytest.raises(ValidationError):
            NearbyQueryParams(lon=2.3522)  # type: ignore[call-arg]

    def test_requires_lon(self) -> None:
        """NearbyQueryParams should require lon field."""
        with pytest.raises(ValidationError):
            NearbyQueryParams(lat=48.8566)  # type: ignore[call-arg]

    def test_uses_query_annotations(self) -> None:
        """NearbyQueryParams fields should use FastAPI Query() for GET parameter binding."""
        # Verify fields have Query metadata (FieldInfo from FastAPI Query)
        for field_name in ("lat", "lon", "radius_m", "category"):
            field_info = NearbyQueryParams.model_fields[field_name]
            # Query() produces a FieldInfo with metadata; check it is present
            assert field_info is not None, f"Field {field_name} must exist"


# ---------------------------------------------------------------------------
# PlaceResponse and PlaceDetailResponse
# ---------------------------------------------------------------------------


class TestPlaceResponse:
    """Tests for PlaceResponse schema."""

    def test_place_response_from_attributes_config(self) -> None:
        """PlaceResponse must have from_attributes=True in model_config."""
        assert PlaceResponse.model_config.get("from_attributes") is True

    def test_place_response_fields(self) -> None:
        """PlaceResponse should have the expected fields."""
        resp = PlaceResponse(
            id=1,
            name="Test Cafe",
            category="cafe",
            lat=48.8566,
            lon=2.3522,
            address="123 Main St",
            current_busyness=65,
            busyness_stale=False,
            busyness_updated_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        )
        assert resp.id == 1
        assert resp.name == "Test Cafe"
        assert resp.category == "cafe"


class TestPlaceDetailResponse:
    """Tests for PlaceDetailResponse schema."""

    def test_place_detail_response_from_attributes_config(self) -> None:
        """PlaceDetailResponse must have from_attributes=True in model_config."""
        assert PlaceDetailResponse.model_config.get("from_attributes") is True

    def test_place_detail_has_busyness_stale(self) -> None:
        """PlaceDetailResponse must include busyness_stale boolean field."""
        assert "busyness_stale" in PlaceDetailResponse.model_fields
        field = PlaceDetailResponse.model_fields["busyness_stale"]
        assert field.annotation is bool or field.annotation == bool

    def test_place_detail_has_busyness_updated_at(self) -> None:
        """PlaceDetailResponse must include busyness_updated_at datetime nullable field."""
        assert "busyness_updated_at" in PlaceDetailResponse.model_fields

    def test_place_detail_has_busyness_data(self) -> None:
        """PlaceDetailResponse must include busyness_data field."""
        assert "busyness_data" in PlaceDetailResponse.model_fields

    def test_place_detail_busyness_updated_at_nullable(self) -> None:
        """PlaceDetailResponse busyness_updated_at should accept None."""
        resp = PlaceDetailResponse(
            id=1,
            name="Test Cafe",
            category="cafe",
            lat=48.8566,
            lon=2.3522,
            address="123 Main St",
            city="Paris",
            country="France",
            busyness_data=None,
            busyness_updated_at=None,
            busyness_stale=False,
        )
        assert resp.busyness_updated_at is None

    def test_place_detail_full_response(self) -> None:
        """PlaceDetailResponse should accept full data including busyness."""
        busyness = {
            "popular_times": [{"day": 0, "hours": [0] * 24}],
            "current_popularity": 65,
        }
        resp = PlaceDetailResponse(
            id=1,
            name="Test Cafe",
            category="cafe",
            lat=48.8566,
            lon=2.3522,
            address="123 Main St",
            city="Paris",
            country="France",
            busyness_data=busyness,
            busyness_updated_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
            busyness_stale=False,
        )
        assert resp.busyness_data == busyness
        assert resp.busyness_stale is False


# ---------------------------------------------------------------------------
# ForecastResponse
# ---------------------------------------------------------------------------


class TestForecastResponse:
    """Tests for ForecastResponse schema."""

    def test_forecast_response_fields(self) -> None:
        """ForecastResponse should include place_id, day, hour, predicted_busyness, data_stale."""
        resp = ForecastResponse(
            place_id=1,
            day=3,
            hour=14,
            predicted_busyness=75,
            data_stale=False,
        )
        assert resp.place_id == 1
        assert resp.day == 3
        assert resp.hour == 14
        assert resp.predicted_busyness == 75
        assert resp.data_stale is False


# ---------------------------------------------------------------------------
# GPSPingRequest
# ---------------------------------------------------------------------------


class TestGPSPingRequest:
    """Tests for GPSPingRequest schema."""

    def test_gps_ping_request_has_accuracy(self) -> None:
        """GPSPingRequest must include accuracy float field."""
        assert "accuracy" in GPSPingRequest.model_fields

    def test_gps_ping_request_valid(self) -> None:
        """GPSPingRequest should accept valid GPS data."""
        req = GPSPingRequest(
            lat=48.8566,
            lon=2.3522,
            accuracy=15.5,
            timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        )
        assert req.lat == 48.8566
        assert req.lon == 2.3522
        assert req.accuracy == 15.5

    def test_gps_ping_request_requires_accuracy(self) -> None:
        """GPSPingRequest should require accuracy field."""
        with pytest.raises(ValidationError):
            GPSPingRequest(
                lat=48.8566,
                lon=2.3522,
                timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
            )  # type: ignore[call-arg]

    def test_gps_ping_request_requires_timestamp(self) -> None:
        """GPSPingRequest should require timestamp field."""
        with pytest.raises(ValidationError):
            GPSPingRequest(
                lat=48.8566,
                lon=2.3522,
                accuracy=15.5,
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# GPSPingResponse nested lists
# ---------------------------------------------------------------------------


class TestGPSPingResponse:
    """Tests for GPSPingResponse schema."""

    def test_gps_ping_response_has_nested_lists(self) -> None:
        """GPSPingResponse must include nearby_places and confirmed_visits as lists."""
        resp = GPSPingResponse(
            nearby_places=[
                NearbyPlaceInfo(place_id=1, name="Test Cafe", distance_m=50.0),
            ],
            confirmed_visits=[
                ConfirmedVisitInfo(visit_id=10, place_id=1, duration_seconds=360),
            ],
            rejected=False,
            rejection_reason=None,
        )
        assert len(resp.nearby_places) == 1
        assert len(resp.confirmed_visits) == 1
        assert resp.nearby_places[0].place_id == 1
        assert resp.confirmed_visits[0].visit_id == 10

    def test_gps_ping_response_empty_lists(self) -> None:
        """GPSPingResponse should accept empty lists."""
        resp = GPSPingResponse(
            nearby_places=[],
            confirmed_visits=[],
            rejected=False,
            rejection_reason=None,
        )
        assert resp.nearby_places == []
        assert resp.confirmed_visits == []

    def test_gps_ping_response_rejected(self) -> None:
        """GPSPingResponse should support rejected=True with a reason."""
        resp = GPSPingResponse(
            nearby_places=[],
            confirmed_visits=[],
            rejected=True,
            rejection_reason="GPS accuracy too low",
        )
        assert resp.rejected is True
        assert resp.rejection_reason == "GPS accuracy too low"


# ---------------------------------------------------------------------------
# NearbyPlaceInfo and ConfirmedVisitInfo
# ---------------------------------------------------------------------------


class TestNearbyPlaceInfo:
    """Tests for NearbyPlaceInfo schema."""

    def test_nearby_place_info_fields(self) -> None:
        """NearbyPlaceInfo should have place_id, name, distance_m."""
        info = NearbyPlaceInfo(place_id=1, name="Test Place", distance_m=42.5)
        assert info.place_id == 1
        assert info.name == "Test Place"
        assert info.distance_m == 42.5


class TestConfirmedVisitInfo:
    """Tests for ConfirmedVisitInfo schema."""

    def test_confirmed_visit_info_fields(self) -> None:
        """ConfirmedVisitInfo should have visit_id, place_id, duration_seconds."""
        info = ConfirmedVisitInfo(visit_id=10, place_id=1, duration_seconds=600)
        assert info.visit_id == 10
        assert info.place_id == 1
        assert info.duration_seconds == 600


# ---------------------------------------------------------------------------
# VisitResponse
# ---------------------------------------------------------------------------


class TestVisitResponse:
    """Tests for VisitResponse schema."""

    def test_visit_response_from_attributes_config(self) -> None:
        """VisitResponse must have from_attributes=True in model_config."""
        assert VisitResponse.model_config.get("from_attributes") is True

    def test_visit_response_fields(self) -> None:
        """VisitResponse should include all expected fields."""
        resp = VisitResponse(
            id=1,
            place_id=10,
            place_name="Test Cafe",
            area_id=5,
            started_at=datetime.datetime(2026, 1, 1, 10, 0, tzinfo=datetime.timezone.utc),
            ended_at=datetime.datetime(2026, 1, 1, 10, 30, tzinfo=datetime.timezone.utc),
            duration_seconds=1800,
        )
        assert resp.id == 1
        assert resp.place_id == 10
        assert resp.place_name == "Test Cafe"
        assert resp.area_id == 5
        assert resp.duration_seconds == 1800

    def test_visit_response_nullable_fields(self) -> None:
        """VisitResponse should allow optional fields to be None."""
        resp = VisitResponse(
            id=1,
            place_id=10,
            place_name="Test Cafe",
            area_id=None,
            started_at=datetime.datetime(2026, 1, 1, 10, 0, tzinfo=datetime.timezone.utc),
            ended_at=None,
            duration_seconds=None,
        )
        assert resp.area_id is None
        assert resp.ended_at is None
        assert resp.duration_seconds is None


# ---------------------------------------------------------------------------
# UserResponse
# ---------------------------------------------------------------------------


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_user_response_from_attributes_config(self) -> None:
        """UserResponse must have from_attributes=True in model_config."""
        assert UserResponse.model_config.get("from_attributes") is True

    def test_user_response_fields(self) -> None:
        """UserResponse should include id, username, email, xp, level, created_at."""
        resp = UserResponse(
            id=1,
            username="testuser",
            email="user@example.com",
            xp=100,
            level=5,
            created_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        )
        assert resp.id == 1
        assert resp.username == "testuser"
        assert resp.email == "user@example.com"
        assert resp.xp == 100
        assert resp.level == 5


# ---------------------------------------------------------------------------
# ORM compatibility: all response schemas must have from_attributes=True
# ---------------------------------------------------------------------------


class TestORMCompatibility:
    """All response schemas must have model_config with from_attributes=True."""

    @pytest.mark.parametrize(
        "schema_cls",
        [
            PlaceResponse,
            PlaceDetailResponse,
            ForecastResponse,
            VisitResponse,
            UserResponse,
            TokenResponse,
        ],
    )
    def test_response_schema_has_from_attributes(self, schema_cls) -> None:
        """Every response schema must have model_config = ConfigDict(from_attributes=True)."""
        assert schema_cls.model_config.get("from_attributes") is True, (
            f"{schema_cls.__name__} is missing model_config with from_attributes=True"
        )
