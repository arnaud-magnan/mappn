"""FastAPI application entry point.

Creates the FastAPI app with:
- Lifespan context manager that initializes and shuts down the async DB engine,
  Redis connection, and ARQ connection pool.
- All API routers registered with appropriate prefixes: /auth, /places, /visits.
- GET /health endpoint returning 200 with {status: "ok"} (no auth required).
- CORS middleware configured for mobile app origins.
- Global exception handlers from core/exceptions.py for consistent error format.

Start with::

    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.places import router as places_router
from app.api.utility import router as utility_router
from app.api.visits import router as visits_router
from app.core.exceptions import register_exception_handlers
from app.core.redis import close_redis_client, get_redis_client
from app.db.session import engine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan context manager
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown resources.

    Startup:
        1. Initialize the async DB engine (already created at module level in
           db/session.py; verify connectivity here).
        2. Initialize the Redis connection via get_redis_client().
        3. Create an ARQ connection pool for enqueuing scraping jobs.

    Shutdown:
        1. Dispose the async DB engine (closes the connection pool).
        2. Close the Redis connection.
    """
    # -- Startup --
    logger.info("Starting Mappn API...")

    # 1. Verify DB engine connectivity (engine is created at import time
    #    in db/session.py; we just ensure it's usable).
    logger.info("Database engine ready (pool_size=%s)", engine.pool.size())

    # 2. Initialize Redis connection
    redis = await get_redis_client()
    logger.info("Redis connection established")

    # 3. Initialize ARQ connection pool for job enqueuing
    arq_pool = None
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        from app.config import get_settings

        settings = get_settings()
        arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        app.state.arq_pool = arq_pool
        logger.info("ARQ connection pool created")
    except Exception:
        logger.warning(
            "Failed to create ARQ connection pool; scraping job enqueuing "
            "will not be available",
            exc_info=True,
        )
        app.state.arq_pool = None

    yield

    # -- Shutdown (LIFO order: last initialized, first cleaned up) --
    logger.info("Shutting down Mappn API...")

    # 1. Close ARQ pool first (last initialized)
    if arq_pool is not None:
        await arq_pool.close()
        logger.info("ARQ connection pool closed")

    # 2. Close Redis connection
    await close_redis_client()
    logger.info("Redis connection closed")

    # 3. Dispose the async DB engine last (first initialized)
    await engine.dispose()
    logger.info("Database engine disposed")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Mappn API",
    description=(
        "Shared backend platform for the Mappn mobile apps. "
        "Provides authentication, places discovery with busyness data, "
        "and GPS-based visit tracking."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------

register_exception_handlers(app)


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:8080",  # Alternative local dev port
        "capacitor://localhost",  # Capacitor (iOS/Android)
        "ionic://localhost",  # Ionic mobile apps
        "http://localhost",  # Generic localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(places_router)
app.include_router(visits_router)
app.include_router(utility_router)


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint.

    Returns 200 with {status: "ok"} without authentication.
    Used for load balancer health probes and uptime monitoring.
    """
    return {"status": "ok"}
