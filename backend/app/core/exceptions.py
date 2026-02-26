"""Custom exception classes and FastAPI exception handlers.

All custom exceptions inherit from :class:`AppException` and produce a
consistent JSON error response with the following shape::

    {
        "status_code": 401,
        "error_type": "credentials_error",
        "message": "Could not validate credentials"
    }

Register the handlers on a FastAPI app by calling
:func:`register_exception_handlers`.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------


class AppException(Exception):
    """Base class for all application-specific exceptions.

    Subclasses must set ``status_code``, ``error_type``, and a default
    ``message``.
    """

    status_code: int = 500
    error_type: str = "internal_error"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Serialise the exception to the standard error response dict."""
        return {
            "status_code": self.status_code,
            "error_type": self.error_type,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Concrete exceptions
# ---------------------------------------------------------------------------


class CredentialsException(AppException):
    """Raised when authentication credentials are invalid or expired."""

    status_code = 401
    error_type = "credentials_error"
    message = "Could not validate credentials"


class DuplicateEntityException(AppException):
    """Raised when attempting to create an entity that already exists."""

    status_code = 409
    error_type = "duplicate_entity"
    message = "Entity already exists"


class EntityNotFoundException(AppException):
    """Raised when a requested entity cannot be found."""

    status_code = 404
    error_type = "not_found"
    message = "Entity not found"


class GPSAccuracyException(AppException):
    """Raised when GPS accuracy is worse than the required threshold."""

    status_code = 422
    error_type = "gps_accuracy_error"
    message = "GPS accuracy is insufficient"


class RateLimitException(AppException):
    """Raised when a rate limit has been exceeded."""

    status_code = 429
    error_type = "rate_limit_exceeded"
    message = "Too many requests. Please try again later."


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


async def _app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle all :class:`AppException` subclasses with a consistent JSON body."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "status_code": 500,
            "error_type": "internal_error",
            "message": "An unexpected error occurred",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on *app*.

    Call this during application startup (e.g. in ``main.py``)::

        from app.core.exceptions import register_exception_handlers
        register_exception_handlers(app)
    """
    app.add_exception_handler(AppException, _app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_exception_handler)
