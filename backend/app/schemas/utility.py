"""Utility endpoint request and response schemas.

Defines Pydantic models for the utility API contract:
- UserStatsResponse: Aggregate visit statistics
- AchievementResponse: Single achievement with progress
- JournalEntryResponse: Journal entry combining visit and note data
- JournalNoteRequest: Request body for creating/updating a journal note
- HeatmapAreaResponse: Single area with visited status for exploration map
- HeatmapResponse: Full heatmap with area list and exploration metrics
- PassportStampResponse: Single neighborhood stamp in a city passport
- CityPassportResponse: City passport with stamps and completion status
"""

import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserStatsResponse(BaseModel):
    """Aggregate visit statistics for the current user.

    Attributes:
        places_count: Total number of distinct places visited.
        cities_count: Total number of distinct cities visited.
        countries_count: Total number of distinct countries visited.
        total_duration_seconds: Sum of all visit durations in seconds.
    """

    model_config = ConfigDict(from_attributes=True)

    places_count: int
    cities_count: int
    countries_count: int
    total_duration_seconds: int


class AchievementResponse(BaseModel):
    """Single achievement with current progress.

    Attributes:
        id: Achievement identifier (e.g., "wanderer", "foodie").
        name: Human-readable achievement name.
        description: Description of what the achievement requires.
        category: Achievement category ("explorer", "habits", "categories").
        progress: Current count toward the threshold.
        threshold: Number required to earn the achievement.
        earned: Whether the achievement has been earned.
        earned_at: Timestamp when the achievement was earned (nullable).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    category: str
    progress: int
    threshold: int
    earned: bool
    earned_at: Optional[datetime.datetime] = None


class JournalEntryResponse(BaseModel):
    """Journal entry combining visit data with optional user note.

    Attributes:
        visit_id: Visit primary key.
        place_id: Place primary key.
        place_name: Place display name (denormalized).
        area_id: Area primary key (nullable).
        city: City name (nullable).
        started_at: When the visit began.
        duration_seconds: Visit duration in seconds (nullable).
        note: User-authored text note (nullable).
        photo_url: URL/path to user photo (nullable).
    """

    model_config = ConfigDict(from_attributes=True)

    visit_id: int
    place_id: int
    place_name: str
    area_id: Optional[int] = None
    city: Optional[str] = None
    started_at: datetime.datetime
    duration_seconds: Optional[int] = None
    note: Optional[str] = None
    photo_url: Optional[str] = None


class JournalNoteRequest(BaseModel):
    """Request body for creating or updating a journal note.

    Attributes:
        text: Optional note text (max 1000 characters).
        photo_url: Optional URL/path to a photo.
    """

    text: Optional[str] = Field(default=None, max_length=1000)
    photo_url: Optional[str] = None


class HeatmapAreaResponse(BaseModel):
    """Single area with visited status for the exploration heatmap.

    Attributes:
        id: Area primary key.
        name: Human-readable area name.
        city: City the area belongs to.
        boundary_geojson: GeoJSON representation of the area boundary.
        visited: Whether the user has visited this area.
        visited_at: When the user first visited this area (nullable).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str
    boundary_geojson: Any
    visited: bool
    visited_at: Optional[datetime.datetime] = None


class HeatmapResponse(BaseModel):
    """Full heatmap response with area list and exploration metrics.

    Attributes:
        areas: List of areas with visited status.
        total_areas: Total number of areas in the scope.
        visited_areas: Number of areas the user has visited.
        explored_pct: Exploration percentage (0.0 to 100.0).
    """

    model_config = ConfigDict(from_attributes=True)

    areas: list[HeatmapAreaResponse]
    total_areas: int
    visited_areas: int
    explored_pct: float


class PassportStampResponse(BaseModel):
    """Single neighborhood stamp in a city passport.

    Attributes:
        area_id: Area primary key.
        name: Neighborhood name.
        visited: Whether the user has earned this stamp.
        visited_at: When the stamp was earned (nullable).
    """

    model_config = ConfigDict(from_attributes=True)

    area_id: int
    name: str
    visited: bool
    visited_at: Optional[datetime.datetime] = None


class CityPassportResponse(BaseModel):
    """City passport with neighborhood stamps and completion status.

    Attributes:
        city: City name.
        total_neighborhoods: Total number of neighborhoods in the city.
        visited_count: Number of neighborhoods the user has stamped.
        stamps: List of neighborhood stamps.
        badge_earned: Whether the user has earned the city completion badge.
        explored_pct: Exploration percentage (0.0 to 100.0).
    """

    model_config = ConfigDict(from_attributes=True)

    city: str
    total_neighborhoods: int
    visited_count: int
    stamps: list[PassportStampResponse]
    badge_earned: bool
    explored_pct: float
