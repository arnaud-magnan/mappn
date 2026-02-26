"""Pydantic schemas package.

Re-exports all request and response schemas for the API contract.
"""

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.place import (
    ForecastResponse,
    NearbyQueryParams,
    PlaceDetailResponse,
    PlaceResponse,
)
from app.schemas.user import UserResponse
from app.schemas.visit import (
    ConfirmedVisitInfo,
    GPSPingRequest,
    GPSPingResponse,
    NearbyPlaceInfo,
    VisitResponse,
)

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "PlaceResponse",
    "PlaceDetailResponse",
    "NearbyQueryParams",
    "ForecastResponse",
    "GPSPingRequest",
    "GPSPingResponse",
    "VisitResponse",
    "NearbyPlaceInfo",
    "ConfirmedVisitInfo",
    "UserResponse",
]
