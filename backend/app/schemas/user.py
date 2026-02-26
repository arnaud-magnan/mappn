"""User response schema.

Defines Pydantic model for user data returned by the API.
"""

import datetime

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """User profile response.

    Fields align with the User ORM model columns exposed to clients.
    password_hash is intentionally excluded for security.

    Attributes:
        id: User primary key.
        username: Display name.
        email: Email address.
        xp: Experience points.
        level: User level.
        created_at: Account creation timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    xp: int
    level: int
    created_at: datetime.datetime
