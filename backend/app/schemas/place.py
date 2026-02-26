"""Place request and response schemas.

Defines Pydantic models for the places API contract:
- PlaceResponse: Summary place data for list results (nearby search)
- PlaceDetailResponse: Full place data including busyness
- NearbyQueryParams: GET query parameters for nearby search
- ForecastResponse: Busyness forecast result
"""

import datetime
from typing import Any, Optional

from fastapi import Query
from pydantic import BaseModel, ConfigDict


class PlaceResponse(BaseModel):
    """Place summary for list results (e.g., nearby search).

    Attributes:
        id: Place primary key.
        name: Place display name.
        category: Place type (e.g., "restaurant", "park").
        lat: Latitude coordinate.
        lon: Longitude coordinate.
        address: Street address (nullable).
        current_busyness: Current live busyness level 0-100 (nullable).
        busyness_stale: Whether busyness data is older than 7 days.
        busyness_updated_at: When busyness data was last updated (nullable).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    lat: float
    lon: float
    address: Optional[str] = None
    current_busyness: Optional[int] = None
    busyness_stale: bool = False
    busyness_updated_at: Optional[datetime.datetime] = None


class PlaceDetailResponse(BaseModel):
    """Full place detail including busyness data.

    Attributes:
        id: Place primary key.
        name: Place display name.
        category: Place type.
        lat: Latitude coordinate.
        lon: Longitude coordinate.
        address: Street address (nullable).
        city: City name (nullable).
        country: Country name (nullable).
        busyness_data: JSONB popular_times and current_popularity (nullable).
        busyness_updated_at: When busyness data was last updated (nullable).
        busyness_stale: Whether busyness data is older than 7 days.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    lat: float
    lon: float
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    busyness_data: Optional[dict[str, Any]] = None
    busyness_updated_at: Optional[datetime.datetime] = None
    busyness_stale: bool = False


class NearbyQueryParams(BaseModel):
    """Query parameters for GET /places/nearby.

    Uses FastAPI Query() annotations for GET parameter binding.
    This schema is intended for use with Depends() on GET endpoints,
    NOT as a request body.

    Attributes:
        lat: Latitude of the search center.
        lon: Longitude of the search center.
        radius_m: Search radius in meters (default 500).
        category: Optional category filter.
    """

    lat: float = Query(..., description="Latitude of the search center")
    lon: float = Query(..., description="Longitude of the search center")
    radius_m: int = Query(500, description="Search radius in meters", ge=1)
    category: Optional[str] = Query(None, description="Category filter (e.g., 'restaurant')")


class ForecastResponse(BaseModel):
    """Busyness forecast for a specific day and hour.

    Attributes:
        place_id: Place primary key.
        day: Day of week (0=Monday, 6=Sunday).
        hour: Hour of day (0-23).
        predicted_busyness: Predicted busyness level 0-100.
        data_stale: Whether the underlying data is older than 7 days.
    """

    model_config = ConfigDict(from_attributes=True)

    place_id: int
    day: int
    hour: int
    predicted_busyness: int
    data_stale: bool = False
