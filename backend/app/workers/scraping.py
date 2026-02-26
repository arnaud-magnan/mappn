"""ARQ scraping pipeline workers for Google Maps Popular Times data.

This module defines one scheduled task:

**scrape_popular_times**: Weekly scrape of popular times histograms for
places that don't have data yet, ordered by activity-based priority.

The scraping call is abstracted behind ``fetch_place_busyness()`` which
uses the Outscraper SDK to fetch data from Google Maps.

Each place is scraped only once. Once ``busyness_data`` is populated,
the place is skipped in subsequent runs.

Workers create their own ``AsyncSession`` via ``AsyncSessionLocal`` -- they
are independent from the FastAPI request lifecycle.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.place import Place

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Delay between individual place scrapes to respect 100 places/hour
# throughput limit.  100 places/hour = 1 place per 36 seconds.
SCRAPE_DELAY_SECONDS: float = 36.0

# Redis key prefix for tracking recent GPS pings per place (set by visit
# tracking service).  Keys follow the pattern:  activity:place:<place_id>
_ACTIVITY_KEY_PREFIX = "activity:place:"

# ---------------------------------------------------------------------------
# Scraping abstraction layer (Outscraper)
# ---------------------------------------------------------------------------

try:
    from outscraper import ApiClient as OutscraperClient  # type: ignore[import-untyped]
except ImportError:
    OutscraperClient = None  # type: ignore[assignment]
    logger.warning(
        "outscraper library not installed; scraping functions will return None"
    )


def fetch_place_busyness(google_place_id: str) -> dict[str, Any] | None:
    """Fetch full popular times data for a place via Outscraper.

    Returns a dict with keys:
        - ``popular_times``: list of 7 day objects with hourly data
        - ``current_popularity``: int or None
        - ``time_spent``: [min, max] minutes or None

    Returns ``None`` on any failure.
    """
    try:
        if OutscraperClient is None:
            logger.error("outscraper library not available")
            return None

        settings = get_settings()
        client = OutscraperClient(api_key=settings.outscraper_api_key)
        results = client.google_maps_search([google_place_id], limit=1, language="en")

        if not results or not results[0]:
            logger.warning("No results from outscraper for %s", google_place_id)
            return None

        place_data = results[0][0] if isinstance(results[0], list) else results[0]

        # Transform outscraper popular_times to our canonical format
        # Outscraper: [{"day": 1..7, "popular_times": [{"hour": 0-23, "percentage": 0-100, ...}]}]
        # Ours: [{"day": 0..6, "hours": [24 ints]}]
        raw_pt = place_data.get("popular_times")
        popular_times = []
        if raw_pt:
            for day_data in raw_pt:
                hours = [0] * 24
                for entry in day_data.get("popular_times", []):
                    hour = entry.get("hour", 0)
                    if 0 <= hour < 24:
                        hours[hour] = entry.get("percentage", 0)
                # Outscraper uses 1=Monday..7=Sunday; convert to 0=Monday..6=Sunday
                day_index = day_data.get("day", 1) - 1
                popular_times.append({
                    "day": day_index,
                    "hours": hours,
                })

        return {
            "popular_times": popular_times,
            "current_popularity": place_data.get("current_popularity"),
            "time_spent": None,
        }
    except Exception:
        logger.exception(
            "Failed to fetch popular times for place %s", google_place_id
        )
        return None


# ---------------------------------------------------------------------------
# Priority scoring
# ---------------------------------------------------------------------------


def compute_priority_score(activity_count: int) -> int:
    """Compute a priority score for a place based on recent user activity.

    Places with any activity in the last 24 hours receive a score >= 3x
    the baseline score of inactive places, ensuring they are scraped at
    least 3 times more frequently.

    Parameters
    ----------
    activity_count:
        Number of user activity events (GPS pings, views) near this place
        in the last 24 hours.

    Returns
    -------
    int
        Priority score (higher = scrape sooner).  Minimum is 1 (baseline).
    """
    baseline = 1
    if activity_count <= 0:
        return baseline
    # Active places get at least 3x baseline, scaling up with more activity
    return max(3 * baseline, baseline + activity_count)


# ---------------------------------------------------------------------------
# Activity tracking helpers
# ---------------------------------------------------------------------------


async def _get_activity_counts(
    redis_client: Any,
) -> dict[int, int]:
    """Query Redis for per-place activity counts in the last 24 hours.

    Scans for keys matching the ``activity:place:<id>`` pattern and returns
    a mapping of place_id to activity count.
    """
    counts: dict[int, int] = {}

    try:
        # Scan activity keys
        async for key in redis_client.scan_iter(f"{_ACTIVITY_KEY_PREFIX}*"):
            try:
                place_id_str = key.replace(_ACTIVITY_KEY_PREFIX, "")
                place_id = int(place_id_str)
                value = await redis_client.get(key)
                counts[place_id] = int(value) if value else 1
            except (ValueError, TypeError):
                continue
    except Exception:
        logger.exception("Error scanning Redis for activity counts")

    return counts


# ---------------------------------------------------------------------------
# ARQ task: scrape_popular_times (weekly)
# ---------------------------------------------------------------------------


async def scrape_popular_times(ctx: dict) -> None:
    """Scrape popular times histograms for all places, ordered by priority.

    This task runs weekly.  It queries all places from the database,
    computes an activity-based priority score for each, and processes
    them in descending priority order.  For each place it:

    1. Calls ``fetch_place_busyness()`` to get the full histogram.
    2. Updates ``Place.busyness_data`` (JSONB) and ``busyness_updated_at``.
    3. Sleeps ``SCRAPE_DELAY_SECONDS`` to respect the throughput limit.

    Individual failures are caught, logged, and do not interrupt processing
    of remaining places.
    """
    logger.info("Starting weekly popular times scrape")

    redis_client = ctx.get("redis")

    async with AsyncSessionLocal() as session:
        # Fetch only places without popular times data
        result = await session.execute(
            select(Place).where(Place.busyness_data.is_(None))
        )
        places = result.scalars().all()

        if not places:
            logger.info("No new places to scrape (all have busyness data)")
            return

        # Get activity counts for priority scoring
        activity_counts: dict[int, int] = {}
        if redis_client:
            activity_counts = await _get_activity_counts(redis_client)

        # Sort by priority (descending)
        sorted_places = sorted(
            places,
            key=lambda p: compute_priority_score(activity_counts.get(p.id, 0)),
            reverse=True,
        )

        scraped = 0
        failed = 0

        for place in sorted_places:
            try:
                data = fetch_place_busyness(place.google_place_id)

                if data is None:
                    logger.warning(
                        "Failed to scrape popular times for place %d (%s) "
                        "-- will retry next cycle",
                        place.id,
                        place.name,
                    )
                    failed += 1
                    # Continue to next place (failure resilience)
                    await asyncio.sleep(SCRAPE_DELAY_SECONDS)
                    continue

                # Update busyness_data JSONB
                existing = place.busyness_data or {}
                existing["popular_times"] = data.get("popular_times", [])
                if data.get("current_popularity") is not None:
                    existing["current_popularity"] = data["current_popularity"]
                if data.get("time_spent") is not None:
                    existing["time_spent"] = data["time_spent"]

                place.busyness_data = existing
                place.busyness_updated_at = datetime.now(timezone.utc)

                await session.commit()
                scraped += 1

                logger.debug(
                    "Scraped popular times for place %d (%s)", place.id, place.name
                )

            except Exception:
                logger.exception(
                    "Unexpected error scraping place %d (%s) -- continuing",
                    place.id,
                    place.name,
                )
                failed += 1
                # Rollback the failed transaction to keep session usable
                await session.rollback()

            # Respect throughput limit
            await asyncio.sleep(SCRAPE_DELAY_SECONDS)

        logger.info(
            "Weekly popular times scrape complete: %d scraped, %d failed out of %d total",
            scraped,
            failed,
            len(sorted_places),
        )


# ---------------------------------------------------------------------------
# ARQ WorkerSettings
# ---------------------------------------------------------------------------


def _get_redis_settings() -> RedisSettings:
    """Build ARQ RedisSettings from application config.

    Returns default localhost settings if application config is not yet
    available (e.g. during test collection or early imports).
    """
    try:
        settings = get_settings()
        return RedisSettings.from_dsn(settings.redis_url)
    except Exception:
        logger.debug(
            "Could not load redis_url from settings; using default RedisSettings"
        )
        return RedisSettings()


class _LazyRedisSettings:
    """Descriptor that lazily evaluates redis_settings on first access.

    This avoids reading application settings at module import time, which
    is fragile when the module is imported in test environments or before
    environment variables are configured.  The result is cached after
    first evaluation.

    The descriptor stores the resolved value directly in the owner class's
    ``__dict__`` so that ARQ's ``get_kwargs()`` (which reads ``__dict__``)
    can find it on subsequent accesses.
    """

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    def __get__(self, obj: object, objtype: type | None = None) -> RedisSettings:
        value = _get_redis_settings()
        # Store in the class __dict__ so future accesses (including ARQ's
        # get_kwargs which reads __dict__ directly) find the resolved value.
        if objtype is not None:
            setattr(objtype, self._name, value)
        return value


class WorkerSettings:
    """ARQ worker configuration for the scraping pipeline.

    ``redis_settings`` is lazily evaluated on first access so that module
    imports do not require environment variables to be set.

    Run with::

        python -m arq app.workers.scraping.WorkerSettings
    """

    functions = [scrape_popular_times]

    cron_jobs = [
        # Weekly popular times scrape -- runs every Sunday at 03:00 UTC
        # Only targets places without existing busyness_data.
        cron(
            scrape_popular_times,
            weekday={6},  # Sunday
            hour={3},
            minute={0},
            timeout=7200,  # 2 hours max
        ),
    ]

    redis_settings = _LazyRedisSettings()

    max_jobs = 10
    job_timeout = 3600  # 1 hour default timeout
