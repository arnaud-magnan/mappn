"""Area ORM model.

Represents a geographic area (district, neighborhood, zone) with a polygon
boundary. Uses PostGIS Geography POLYGON for meter-accurate containment queries.
"""

from typing import Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Area(Base):
    """Geographic area model with polygon boundary.

    Attributes:
        id: Integer primary key for stable FK references.
        name: Human-readable area name.
        city: City this area belongs to.
        boundary: PostGIS Geography POLYGON defining the area boundary.
        zone_type: Classification of the area (e.g., "district", "neighborhood").
        busyness_score: Aggregate busyness score for the area (nullable).
    """

    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    boundary: Mapped[Any] = mapped_column(
        Geography(geometry_type="POLYGON", srid=4326),
        nullable=False,
    )
    zone_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    busyness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    visits: Mapped[list["Visit"]] = relationship("Visit", back_populates="area")

    def __repr__(self) -> str:
        return f"<Area(id={self.id}, name='{self.name}', zone_type='{self.zone_type}')>"
