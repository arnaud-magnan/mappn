"""Visit request and response schemas.

Defines Pydantic models for the visits API contract:
- GPSPingRequest: GPS location ping with accuracy
- GPSPingResponse: Response with nearby places and confirmed visits
- VisitResponse: Confirmed visit details
- NearbyPlaceInfo: Nested schema for nearby place in ping response
- ConfirmedVisitInfo: Nested schema for confirmed visit in ping response
"""

import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NearbyPlaceInfo(BaseModel):
    """Info about a nearby place detected in a GPS ping.

    Attributes:
        place_id: Place primary key.
        name: Place display name.
        distance_m: Distance from the user in meters.
    """

    place_id: int
    name: str
    distance_m: float


class ConfirmedVisitInfo(BaseModel):
    """Info about a visit confirmed by this GPS ping.

    Attributes:
        visit_id: Visit primary key.
        place_id: Place primary key.
        duration_seconds: Total visit duration in seconds.
    """

    visit_id: int
    place_id: int
    duration_seconds: int


class GPSPingRequest(BaseModel):
    """GPS location ping request.

    Sent by mobile apps at regular intervals for visit tracking.

    Attributes:
        lat: Latitude coordinate.
        lon: Longitude coordinate.
        accuracy: GPS accuracy in meters (lower is better).
        timestamp: When the GPS reading was taken.
    """

    lat: float
    lon: float
    accuracy: float
    timestamp: datetime.datetime


class GPSPingResponse(BaseModel):
    """Response to a GPS ping.

    Contains nearby places, any visits confirmed by this ping,
    and rejection status if GPS accuracy is insufficient.

    Attributes:
        nearby_places: List of places within geofence radius.
        confirmed_visits: List of visits confirmed by this ping.
        rejected: Whether the ping was rejected (e.g., accuracy too low).
        rejection_reason: Human-readable reason for rejection (nullable).
    """

    nearby_places: list[NearbyPlaceInfo]
    confirmed_visits: list[ConfirmedVisitInfo]
    rejected: bool
    rejection_reason: Optional[str] = None


class VisitResponse(BaseModel):
    """Confirmed visit detail for visit history.

    Attributes:
        id: Visit primary key.
        place_id: Place primary key.
        place_name: Place display name (denormalized for convenience).
        area_id: Area primary key (nullable).
        started_at: When the visit began.
        ended_at: When the visit ended (nullable if still in progress).
        duration_seconds: Total visit duration in seconds (nullable).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    place_id: int
    place_name: str
    area_id: Optional[int] = None
    started_at: datetime.datetime
    ended_at: Optional[datetime.datetime] = None
    duration_seconds: Optional[int] = None
