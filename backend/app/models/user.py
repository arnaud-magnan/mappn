"""User ORM model.

Represents a user account shared across both Mappn apps (Utility and Game).
Supports future FK references from game/social entity tables via integer PK.
"""

import datetime
from typing import Any

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """User account model.

    Attributes:
        id: Integer primary key for stable FK references.
        username: Unique display name (minimum 3 characters enforced at API layer).
        email: Unique email address (format enforced at API layer).
        password_hash: Bcrypt hash of the user's password.
        xp: Experience points, defaults to 0.
        level: User level, defaults to 1.
        created_at: Timestamp of account creation.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    visits: Mapped[list["Visit"]] = relationship("Visit", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
