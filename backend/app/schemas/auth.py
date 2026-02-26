"""Authentication request and response schemas.

Defines Pydantic models for the auth API contract:
- RegisterRequest: User registration with field-level validation
- LoginRequest: User login credentials
- TokenResponse: JWT token pair response
"""

from pydantic import BaseModel, ConfigDict, field_validator


class RegisterRequest(BaseModel):
    """User registration request.

    Validates:
        - email: Must contain @ symbol and have content before and after it
        - username: Minimum 3 characters
        - password: Minimum 8 characters
    """

    email: str
    username: str
    password: str

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        """Validate that email contains @ with content on both sides."""
        if not v or "@" not in v:
            raise ValueError("Invalid email format: must contain @ symbol")
        parts = v.split("@")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("Invalid email format: must have content before and after @")
        if "." not in parts[1]:
            raise ValueError("Invalid email format: domain must contain a dot")
        return v

    @field_validator("username")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        """Validate that username is at least 3 characters."""
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        """Validate that password is at least 8 characters."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    """User login request.

    Attributes:
        email: User's email address.
        password: User's password.
    """

    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token pair response.

    Returned after successful login, registration, or token refresh.

    Attributes:
        access_token: Short-lived JWT for API access.
        refresh_token: Long-lived JWT for obtaining new access tokens.
        token_type: Token type, always "bearer".
        expires_in: Access token lifetime in seconds.
    """

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
