"""JournalNote ORM model.

Represents a user-authored note (text and/or photo reference) attached to a
confirmed visit. Each visit may have at most one journal note.
"""

import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JournalNote(Base):
    """Journal note attached to a visit.

    Attributes:
        id: Integer primary key.
        visit_id: FK to visits.id (the visit this note belongs to).
        user_id: FK to users.id (the author).
        text: Optional note text (max 1000 characters).
        photo_url: Optional URL/path to a photo stored on-device.
        created_at: When the note was created (server default now()).
    """

    __tablename__ = "journal_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    visit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("visits.id"), nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False,
    )
    text: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    visit: Mapped["Visit"] = relationship("Visit")
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<JournalNote(id={self.id}, visit_id={self.visit_id}, "
            f"user_id={self.user_id})>"
        )
