"""Place ORM model.

Represents a geographic place enriched with busyness data from Google Maps
Popular Times. Uses PostGIS Geography POINT for meter-accurate spatial queries.
"""

import datetime
from typing import Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Place(Base):
    """Geographic place model with busyness data.

    Attributes:
        id: Integer primary key for stable FK references.
        google_place_id: Google Maps place identifier for scraping.
        name: Human-readable place name.
        category: Place type (e.g., "restaurant", "park", "cafe").
        coordinates: PostGIS Geography POINT (lon, lat) with SRID 4326.
        address: Street address.
        city: City name.
        country: Country name or code.
        busyness_data: JSONB containing popular_times histogram and live busyness.
        busyness_updated_at: When busyness data was last scraped/updated.
    """

    __tablename__ = "places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_place_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    coordinates: Mapped[Any] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    busyness_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    busyness_updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    visits: Mapped[list["Visit"]] = relationship("Visit", back_populates="place")

    def __repr__(self) -> str:
        return f"<Place(id={self.id}, name='{self.name}', category='{self.category}')>"
