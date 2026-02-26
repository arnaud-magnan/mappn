"""Async Redis client and helper functions for UserPresence tracking
and authentication rate limiting.

The module provides:
- ``get_redis_client()``: Factory for a shared async Redis connection.
- ``set_user_presence()`` / ``get_user_presence()`` / ``delete_user_presence()``:
  JSON-serialised UserPresence CRUD with configurable TTL.
- ``increment_rate_limit()``: Sliding-window counter for auth rate limiting.

All public Redis operations catch ``redis.asyncio.RedisError`` and either
return a graceful fallback or raise :class:`~app.core.exceptions.AppException`.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis client singleton
# ---------------------------------------------------------------------------

_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Return the shared async Redis client, creating it on first call.

    The client connects using ``Settings.redis_url``.
    """
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client


async def close_redis_client() -> None:
    """Close the shared Redis client (call during app shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


# ---------------------------------------------------------------------------
# UserPresence helpers
# ---------------------------------------------------------------------------

# Default TTL for user presence entries (30 minutes).  If a user stops
# sending GPS pings the presence entry expires automatically.
_PRESENCE_TTL_SECONDS = 1800

_PRESENCE_KEY_PREFIX = "presence:"


def _presence_key(user_id: int, place_id: int) -> str:
    """Build the Redis key for a user+place presence entry."""
    return f"{_PRESENCE_KEY_PREFIX}{user_id}:{place_id}"


async def set_user_presence(
    user_id: int,
    place_id: int,
    data: dict[str, Any],
    ttl_seconds: int = _PRESENCE_TTL_SECONDS,
) -> None:
    """Store a UserPresence record in Redis as JSON with a TTL.

    Parameters
    ----------
    user_id:
        The user's database ID.
    place_id:
        The place's database ID.
    data:
        Arbitrary presence data (e.g. ``first_seen``, ``last_seen``,
        ``reading_count``).  Values are JSON-serialised; ``datetime``
        objects are converted to ISO-8601 strings.
    ttl_seconds:
        Key expiry in seconds (default 1800 = 30 minutes).

    Raises
    ------
    AppException
        When Redis is unavailable.
    """
    try:
        client = await get_redis_client()
        key = _presence_key(user_id, place_id)
        serializable = _prepare_for_json(data)
        await client.setex(key, ttl_seconds, json.dumps(serializable))
    except aioredis.RedisError as exc:
        logger.error("Redis error in set_user_presence: %s", exc)
        raise AppException("Redis service unavailable") from exc


async def get_user_presence(
    user_id: int,
    place_id: int,
) -> dict[str, Any] | None:
    """Retrieve a UserPresence record from Redis.

    Returns ``None`` if the key does not exist, has expired, or if Redis
    is unavailable (graceful fallback).
    """
    try:
        client = await get_redis_client()
        key = _presence_key(user_id, place_id)
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except aioredis.RedisError as exc:
        logger.error("Redis error in get_user_presence: %s", exc)
        return None


async def delete_user_presence(user_id: int, place_id: int) -> None:
    """Delete a UserPresence record from Redis.

    Raises
    ------
    AppException
        When Redis is unavailable.
    """
    try:
        client = await get_redis_client()
        key = _presence_key(user_id, place_id)
        await client.delete(key)
    except aioredis.RedisError as exc:
        logger.error("Redis error in delete_user_presence: %s", exc)
        raise AppException("Redis service unavailable") from exc


# ---------------------------------------------------------------------------
# Refresh token JTI blacklist helpers
# ---------------------------------------------------------------------------

_JTI_BLACKLIST_KEY_PREFIX = "jti_blacklist:"


async def blacklist_jti(jti: str, ttl_seconds: int) -> None:
    """Add a refresh token JTI to the blacklist.

    The blacklisted JTI is stored in Redis with a TTL equal to the refresh
    token lifetime, so it automatically expires when the token would have
    expired anyway.

    Parameters
    ----------
    jti:
        The JWT ID claim value from the refresh token.
    ttl_seconds:
        Time-to-live in seconds (should match the refresh token lifetime).

    Raises
    ------
    AppException
        When Redis is unavailable.
    """
    try:
        client = await get_redis_client()
        key = f"{_JTI_BLACKLIST_KEY_PREFIX}{jti}"
        await client.setex(key, ttl_seconds, "1")
    except aioredis.RedisError as exc:
        logger.error("Redis error in blacklist_jti: %s", exc)
        raise AppException("Redis service unavailable") from exc


async def is_jti_blacklisted(jti: str) -> bool:
    """Check whether a refresh token JTI has been blacklisted.

    Returns ``False`` (allow) when Redis is unavailable to fail open,
    matching the rate limiter's fail-open behaviour.
    """
    try:
        client = await get_redis_client()
        key = f"{_JTI_BLACKLIST_KEY_PREFIX}{jti}"
        return await client.exists(key) > 0
    except aioredis.RedisError as exc:
        logger.error("Redis error in is_jti_blacklisted: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Rate limiting helpers
# ---------------------------------------------------------------------------

_RATE_LIMIT_KEY_PREFIX = "ratelimit:"


async def increment_rate_limit(
    key_identifier: str,
    window_seconds: int = 300,
) -> int:
    """Increment a rate-limit counter and return the new count.

    Uses a Redis key with a TTL equal to *window_seconds* so the counter
    auto-resets after the window expires.

    Parameters
    ----------
    key_identifier:
        Unique identifier for the rate-limit bucket (e.g. an IP address
        or ``"auth:<ip>"``).
    window_seconds:
        The sliding-window duration in seconds (default 300 = 5 minutes).

    Returns
    -------
    int
        The counter value **after** incrementing.
    """
    try:
        client = await get_redis_client()
        key = f"{_RATE_LIMIT_KEY_PREFIX}{key_identifier}"
        count = await client.incr(key)
        # Only set TTL on the first increment (when count == 1) so the window
        # does not reset on every request.
        if count == 1:
            await client.expire(key, window_seconds)
        return count
    except aioredis.RedisError as exc:
        logger.error("Redis error in increment_rate_limit: %s", exc)
        raise AppException("Redis service unavailable") from exc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _prepare_for_json(data: dict[str, Any]) -> dict[str, Any]:
    """Convert non-JSON-serialisable values (e.g. datetime) to strings."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result
