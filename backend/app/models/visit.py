"""Visit ORM model.

Represents a confirmed visit by a user to a place. Created automatically
when server-side visit tracking detects the user remained within the
geofence radius for the minimum dwell time.
"""

import datetime
from typing import Optional

from sqlalchemy import Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Visit(Base):
    """Confirmed visit record.

    Attributes:
        id: Integer primary key.
        user_id: FK to users.id (the visiting user).
        place_id: FK to places.id (the visited place).
        area_id: FK to areas.id (the area containing the place, nullable).
        started_at: When the visit began (first GPS reading within geofence).
        ended_at: When the visit ended (nullable if still in progress).
        duration_seconds: Total visit duration in seconds.
    """

    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True,
    )
    place_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("places.id"), nullable=False, index=True,
    )
    area_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("areas.id"), nullable=True,
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="visits")
    place: Mapped["Place"] = relationship("Place", back_populates="visits")
    area: Mapped[Optional["Area"]] = relationship("Area", back_populates="visits")

    def __repr__(self) -> str:
        return (
            f"<Visit(id={self.id}, user_id={self.user_id}, "
            f"place_id={self.place_id}, duration={self.duration_seconds}s)>"
        )
