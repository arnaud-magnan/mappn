"""Forecast service for busyness prediction from histogram data.

Provides busyness prediction by looking up the popular_times histogram
stored in the Place's busyness_data JSONB column. The histogram contains
hourly busyness values (0-100) for each day of the week.

Expected busyness_data structure::

    {
        "popular_times": [
            {"day": 0, "hours": [0, 0, 0, 5, 10, 25, ...]},  # 24 values per day
            {"day": 1, "hours": [...]},
            ...
            {"day": 6, "hours": [...]}
        ],
        "current_popularity": 65,
        "time_spent": [15, 30]
    }
"""

from __future__ import annotations

from typing import Any, Optional


def predict_busyness(
    busyness_data: Optional[dict[str, Any]],
    day: int,
    hour: int,
) -> Optional[int]:
    """Predict busyness level for a given day and hour from histogram data.

    Looks up the predicted busyness value from the popular_times histogram:
    ``busyness_data["popular_times"][day_index]["hours"][hour]``

    The popular_times list is indexed by finding the entry where ``day``
    matches the requested day value.

    Args:
        busyness_data: JSONB busyness data from the Place model.
            Must contain a ``popular_times`` list with day/hours entries.
        day: Day of week (0=Monday, 6=Sunday).
        hour: Hour of day (0-23).

    Returns:
        Predicted busyness level (0-100), or None if the data is
        unavailable or the requested day/hour is not found.
    """
    if busyness_data is None:
        return None

    popular_times = busyness_data.get("popular_times")
    if not popular_times or not isinstance(popular_times, list):
        return None

    # Find the entry for the requested day
    for day_entry in popular_times:
        if not isinstance(day_entry, dict):
            continue
        if day_entry.get("day") == day:
            hours = day_entry.get("hours")
            if not hours or not isinstance(hours, list):
                return None
            if 0 <= hour < len(hours):
                value = hours[hour]
                return int(value) if value is not None else None
            return None

    return None
