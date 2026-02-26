"""Tests for the scraping pipeline workers.

Tests cover:
- ARQ WorkerSettings configuration (cron jobs)
- scrape_popular_times() task logic with mocked populartimes
- scrape_live_busyness() task logic with mocked responses
- Activity-based priority scoring
- Failure resilience (per-place try/except, retry marking)
- Throughput delay enforcement
- Worker creates its own AsyncSession (not request-scoped)
- fetch_place_busyness() abstraction layer
"""

from __future__ import annotations

import os

# Set environment variables before any app imports so get_settings() works.
# These are test-only values; no real connections are made for unit tests.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")

# Clear the lru_cache on get_settings so our env vars take effect
from app.config import get_settings
get_settings.cache_clear()

import asyncio
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.scraping import (
    WorkerSettings,
    fetch_place_busyness,
    fetch_live_busyness,
    scrape_popular_times,
    scrape_live_busyness,
    compute_priority_score,
    SCRAPE_DELAY_SECONDS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_place_row(
    place_id: int,
    google_place_id: str,
    name: str = "Test Place",
    busyness_data: dict | None = None,
    busyness_updated_at: datetime.datetime | None = None,
) -> MagicMock:
    """Create a mock Place-like object with the columns the worker reads."""
    place = MagicMock()
    place.id = place_id
    place.google_place_id = google_place_id
    place.name = name
    place.busyness_data = busyness_data
    place.busyness_updated_at = busyness_updated_at
    return place


def _sample_populartimes_response() -> dict:
    """Return a realistic populartimes.get_id() response."""
    day_data = [0, 0, 0, 5, 10, 25, 45, 60, 75, 80, 70, 55, 40, 35, 30, 40, 55, 70, 80, 65, 45, 25, 10, 0]
    return {
        "populartimes": [
            {"name": "Monday", "data": day_data},
            {"name": "Tuesday", "data": day_data},
            {"name": "Wednesday", "data": day_data},
            {"name": "Thursday", "data": day_data},
            {"name": "Friday", "data": day_data},
            {"name": "Saturday", "data": day_data},
            {"name": "Sunday", "data": day_data},
        ],
        "current_popularity": 65,
        "time_spent": [15, 30],
    }


# ---------------------------------------------------------------------------
# WorkerSettings Configuration Tests
# ---------------------------------------------------------------------------


class TestWorkerSettings:
    """Verify ARQ WorkerSettings has the correct cron jobs defined."""

    def test_worker_settings_has_cron_jobs(self):
        assert hasattr(WorkerSettings, "cron_jobs"), (
            "WorkerSettings must define cron_jobs attribute"
        )

    def test_cron_jobs_is_iterable(self):
        cron_jobs = WorkerSettings.cron_jobs
        assert hasattr(cron_jobs, "__iter__"), "cron_jobs must be iterable"

    def test_cron_jobs_contains_popular_times_weekly(self):
        """scrape_popular_times should run weekly (on a specific weekday)."""
        cron_jobs = WorkerSettings.cron_jobs
        # ARQ prefixes cron job names with "cron:" by default
        job_names = [job.name for job in cron_jobs]
        assert any("scrape_popular_times" in name for name in job_names), (
            f"cron_jobs must include scrape_popular_times, got: {job_names}"
        )

    def test_cron_jobs_contains_live_busyness_every_15_min(self):
        """scrape_live_busyness should run every 15 minutes."""
        cron_jobs = WorkerSettings.cron_jobs
        job_names = [job.name for job in cron_jobs]
        assert any("scrape_live_busyness" in name for name in job_names), (
            f"cron_jobs must include scrape_live_busyness, got: {job_names}"
        )

    def test_popular_times_cron_has_weekday_set(self):
        """The popular times job should have a weekday constraint (weekly)."""
        cron_jobs = WorkerSettings.cron_jobs
        for job in cron_jobs:
            if "scrape_popular_times" in job.name:
                # weekday should be set (not None) to indicate weekly schedule
                assert job.weekday is not None, (
                    "scrape_popular_times must have weekday set for weekly execution"
                )
                break
        else:
            pytest.fail("scrape_popular_times cron job not found")

    def test_live_busyness_cron_has_minute_set(self):
        """The live busyness job should run at specific minutes (every 15 min)."""
        cron_jobs = WorkerSettings.cron_jobs
        for job in cron_jobs:
            if "scrape_live_busyness" in job.name:
                # minute should be a set/frozenset of {0, 15, 30, 45}
                assert job.minute is not None, (
                    "scrape_live_busyness must have minute set for 15-min interval"
                )
                break
        else:
            pytest.fail("scrape_live_busyness cron job not found")

    def test_worker_settings_has_redis_settings(self):
        assert hasattr(WorkerSettings, "redis_settings"), (
            "WorkerSettings must define redis_settings"
        )

    def test_worker_settings_has_functions(self):
        """WorkerSettings should also list ad-hoc callable functions."""
        assert hasattr(WorkerSettings, "functions"), (
            "WorkerSettings must define functions list"
        )


# ---------------------------------------------------------------------------
# fetch_place_busyness Abstraction Tests
# ---------------------------------------------------------------------------


class TestFetchPlaceBusyness:
    """Tests for the abstracted scraping function."""

    @patch("app.workers.scraping.populartimes")
    def test_fetch_place_busyness_calls_populartimes_get_id(self, mock_pt):
        """The abstraction should delegate to populartimes.get_id()."""
        mock_pt.get_id.return_value = _sample_populartimes_response()
        result = fetch_place_busyness("ChIJ_test_id_123")
        mock_pt.get_id.assert_called_once()
        assert result is not None

    @patch("app.workers.scraping.populartimes")
    def test_fetch_place_busyness_returns_structured_data(self, mock_pt):
        """Result should contain popular_times and current_popularity."""
        mock_pt.get_id.return_value = _sample_populartimes_response()
        result = fetch_place_busyness("ChIJ_test_id_123")
        assert "popular_times" in result
        assert "current_popularity" in result

    @patch("app.workers.scraping.populartimes")
    def test_fetch_place_busyness_returns_none_on_failure(self, mock_pt):
        """Should return None when the underlying library raises an exception."""
        mock_pt.get_id.side_effect = Exception("API error")
        result = fetch_place_busyness("ChIJ_test_id_123")
        assert result is None

    @patch("app.workers.scraping.populartimes")
    def test_fetch_live_busyness_returns_current_popularity(self, mock_pt):
        """fetch_live_busyness should extract current_popularity."""
        mock_pt.get_id.return_value = _sample_populartimes_response()
        result = fetch_live_busyness("ChIJ_test_id_123")
        assert result == 65

    @patch("app.workers.scraping.populartimes")
    def test_fetch_live_busyness_returns_none_on_failure(self, mock_pt):
        mock_pt.get_id.side_effect = Exception("API error")
        result = fetch_live_busyness("ChIJ_test_id_123")
        assert result is None

    @patch("app.workers.scraping.populartimes")
    def test_fetch_live_busyness_returns_none_when_no_current(self, mock_pt):
        """If populartimes response has no current_popularity, return None."""
        response = _sample_populartimes_response()
        del response["current_popularity"]
        mock_pt.get_id.return_value = response
        result = fetch_live_busyness("ChIJ_test_id_123")
        assert result is None


# ---------------------------------------------------------------------------
# Priority Scoring Tests
# ---------------------------------------------------------------------------


class TestPriorityScoring:
    """Tests for activity-based priority scoring."""

    def test_active_place_has_higher_priority_than_inactive(self):
        """A place with recent activity should score higher."""
        active_score = compute_priority_score(activity_count=10)
        inactive_score = compute_priority_score(activity_count=0)
        assert active_score > inactive_score

    def test_active_place_priority_at_least_3x_inactive(self):
        """Places with activity in last 24h must be scraped >= 3x more."""
        active_score = compute_priority_score(activity_count=1)
        inactive_score = compute_priority_score(activity_count=0)
        assert active_score >= 3 * inactive_score, (
            f"Active score ({active_score}) must be >= 3x inactive score ({inactive_score})"
        )

    def test_more_activity_means_higher_priority(self):
        """More activity should increase priority score."""
        low_activity = compute_priority_score(activity_count=1)
        high_activity = compute_priority_score(activity_count=50)
        assert high_activity >= low_activity

    def test_zero_activity_returns_baseline(self):
        """Zero activity should return baseline priority (> 0)."""
        score = compute_priority_score(activity_count=0)
        assert score > 0, "Even inactive places should have non-zero priority"


# ---------------------------------------------------------------------------
# scrape_popular_times Task Tests
# ---------------------------------------------------------------------------


class TestScrapePopularTimes:
    """Tests for the scrape_popular_times ARQ task."""

    @pytest.mark.asyncio
    async def test_scrape_popular_times_updates_busyness_data(self):
        """Should update Place.busyness_data and busyness_updated_at."""
        place = _make_place_row(1, "ChIJ_place_1")
        mock_session = AsyncMock()
        # Mock query result returning one place
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [place]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        sample_popular_times = _sample_populartimes_response()["populartimes"]

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_place_busyness") as mock_fetch,
            patch("app.workers.scraping.asyncio") as mock_asyncio,
            patch("app.workers.scraping._get_activity_counts") as mock_activity,
        ):
            mock_fetch.return_value = {
                "popular_times": sample_popular_times,
                "current_popularity": 65,
                "time_spent": [15, 30],
            }
            mock_activity.return_value = {1: 5}
            # Make asyncio.sleep a no-op
            mock_asyncio.sleep = AsyncMock()

            await scrape_popular_times(ctx)

        # Verify the session committed the changes
        mock_session.commit.assert_called()

        # Verify place field values were actually updated
        assert place.busyness_data is not None, (
            "busyness_data should have been set on the place"
        )
        assert "popular_times" in place.busyness_data, (
            "busyness_data must contain 'popular_times' key"
        )
        assert place.busyness_data["popular_times"] == sample_popular_times, (
            "popular_times data should match the fetched value"
        )
        assert place.busyness_data.get("current_popularity") == 65, (
            "current_popularity should be 65"
        )
        assert place.busyness_data.get("time_spent") == [15, 30], (
            "time_spent should be [15, 30]"
        )
        assert place.busyness_updated_at is not None, (
            "busyness_updated_at must be set after successful scrape"
        )
        # busyness_updated_at should be a recent datetime
        assert isinstance(place.busyness_updated_at, datetime.datetime), (
            "busyness_updated_at should be a datetime instance"
        )

    @pytest.mark.asyncio
    async def test_scrape_popular_times_handles_individual_failure(self):
        """A failure scraping one place should not stop others."""
        place1 = _make_place_row(1, "ChIJ_fail")
        place2 = _make_place_row(2, "ChIJ_success")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [place1, place2]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        call_count = 0

        def side_effect(google_place_id):
            nonlocal call_count
            call_count += 1
            if google_place_id == "ChIJ_fail":
                return None  # Simulate failure
            return {
                "popular_times": _sample_populartimes_response()["populartimes"],
                "current_popularity": 50,
                "time_spent": [10, 20],
            }

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_place_busyness", side_effect=side_effect),
            patch("app.workers.scraping.asyncio") as mock_asyncio,
            patch("app.workers.scraping._get_activity_counts") as mock_activity,
        ):
            mock_asyncio.sleep = AsyncMock()
            mock_activity.return_value = {}

            await scrape_popular_times(ctx)

        # Both places should have been attempted
        assert call_count == 2, "Both places should be attempted even if one fails"
        # Session should have committed (at least for the successful place)
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_scrape_popular_times_exception_triggers_rollback(self):
        """An exception during processing should trigger session.rollback() and not stop other places."""
        place1 = _make_place_row(1, "ChIJ_explode")
        place2 = _make_place_row(2, "ChIJ_ok")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [place1, place2]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        call_count = 0

        def fetch_side_effect(google_place_id):
            nonlocal call_count
            call_count += 1
            # Return valid data for both places -- the exception will come
            # from session.commit() for the first place.
            return {
                "popular_times": _sample_populartimes_response()["populartimes"],
                "current_popularity": 50,
                "time_spent": [10, 20],
            }

        # Make commit raise an exception on the first call, succeed on the second
        commit_call_count = 0

        async def commit_side_effect():
            nonlocal commit_call_count
            commit_call_count += 1
            if commit_call_count == 1:
                raise RuntimeError("Simulated DB error during commit")
            return None

        mock_session.commit = AsyncMock(side_effect=commit_side_effect)

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_place_busyness", side_effect=fetch_side_effect),
            patch("app.workers.scraping.asyncio") as mock_asyncio,
            patch("app.workers.scraping._get_activity_counts") as mock_activity,
        ):
            mock_asyncio.sleep = AsyncMock()
            mock_activity.return_value = {}

            # Should NOT raise -- exceptions are caught per-place
            await scrape_popular_times(ctx)

        # Both places should have been attempted (fetch called for both)
        assert call_count == 2, (
            f"Both places should be attempted even if first raises; got {call_count}"
        )
        # session.rollback() should have been called for the failed place
        mock_session.rollback.assert_called()
        # The second place should have committed successfully
        assert commit_call_count == 2, (
            "commit should have been called twice (once failing, once succeeding)"
        )
        # The second place should have its busyness_data updated
        assert place2.busyness_data is not None, (
            "Second place should have busyness_data set despite first place failing"
        )
        assert place2.busyness_updated_at is not None, (
            "Second place should have busyness_updated_at set"
        )

    @pytest.mark.asyncio
    async def test_scrape_popular_times_orders_by_priority(self):
        """Places should be processed in priority order (high activity first)."""
        place_low = _make_place_row(1, "ChIJ_low")
        place_high = _make_place_row(2, "ChIJ_high")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        # Return in arbitrary order
        mock_result.scalars.return_value.all.return_value = [place_low, place_high]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        scrape_order = []

        def track_fetch(google_place_id):
            scrape_order.append(google_place_id)
            return {
                "popular_times": _sample_populartimes_response()["populartimes"],
                "current_popularity": 50,
                "time_spent": [10, 20],
            }

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_place_busyness", side_effect=track_fetch),
            patch("app.workers.scraping.asyncio") as mock_asyncio,
            patch("app.workers.scraping._get_activity_counts") as mock_activity,
        ):
            mock_asyncio.sleep = AsyncMock()
            # place_high (id=2) has more activity
            mock_activity.return_value = {2: 20, 1: 0}

            await scrape_popular_times(ctx)

        # High-activity place should be scraped first
        assert scrape_order[0] == "ChIJ_high", (
            f"Expected high-activity place first, got order: {scrape_order}"
        )

    @pytest.mark.asyncio
    async def test_scrape_popular_times_respects_delay(self):
        """Should sleep between place scrapes to respect throughput limit."""
        place = _make_place_row(1, "ChIJ_place_1")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [place]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_place_busyness") as mock_fetch,
            patch("app.workers.scraping.asyncio") as mock_asyncio,
            patch("app.workers.scraping._get_activity_counts") as mock_activity,
        ):
            mock_fetch.return_value = {
                "popular_times": [],
                "current_popularity": None,
                "time_spent": None,
            }
            mock_activity.return_value = {}
            mock_asyncio.sleep = AsyncMock()

            await scrape_popular_times(ctx)

        # asyncio.sleep should have been called with the configured delay
        mock_asyncio.sleep.assert_called()
        call_args = mock_asyncio.sleep.call_args_list
        for call in call_args:
            delay = call[0][0]
            assert delay >= SCRAPE_DELAY_SECONDS, (
                f"Delay {delay}s is less than required {SCRAPE_DELAY_SECONDS}s"
            )


# ---------------------------------------------------------------------------
# scrape_live_busyness Task Tests
# ---------------------------------------------------------------------------


class TestScrapeLiveBusyness:
    """Tests for the scrape_live_busyness ARQ task."""

    @pytest.mark.asyncio
    async def test_scrape_live_busyness_targets_active_places_only(self):
        """Should only query places with recent user activity (GPS pings in last 30 min)."""
        active_place = _make_place_row(1, "ChIJ_active", busyness_data={"popular_times": []})

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [active_place]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_live_busyness") as mock_fetch,
            patch("app.workers.scraping.asyncio") as mock_asyncio,
            patch("app.workers.scraping._get_active_place_ids") as mock_active,
        ):
            mock_fetch.return_value = 72
            mock_asyncio.sleep = AsyncMock()
            mock_active.return_value = {1}

            await scrape_live_busyness(ctx)

        # Verify the fetch was called for the active place
        mock_fetch.assert_called_once_with("ChIJ_active")
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_scrape_live_busyness_updates_current_popularity(self):
        """Should update the current_popularity field in busyness_data JSONB."""
        existing_data = {
            "popular_times": [{"day": 0, "hours": [0] * 24}],
            "current_popularity": 30,
        }
        place = _make_place_row(1, "ChIJ_live", busyness_data=existing_data)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [place]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_live_busyness") as mock_fetch,
            patch("app.workers.scraping.asyncio") as mock_asyncio,
            patch("app.workers.scraping._get_active_place_ids") as mock_active,
        ):
            mock_fetch.return_value = 85
            mock_asyncio.sleep = AsyncMock()
            mock_active.return_value = {1}

            await scrape_live_busyness(ctx)

        # Verify commit was called
        mock_session.commit.assert_called()

        # Verify place field values were actually updated
        assert place.busyness_data is not None, (
            "busyness_data should have been set on the place"
        )
        assert place.busyness_data["current_popularity"] == 85, (
            "current_popularity should be updated to 85 (was 30)"
        )
        # Verify original popular_times data was preserved
        assert place.busyness_data["popular_times"] == [{"day": 0, "hours": [0] * 24}], (
            "popular_times data should be preserved when only updating live busyness"
        )
        assert place.busyness_updated_at is not None, (
            "busyness_updated_at must be set after successful refresh"
        )
        assert isinstance(place.busyness_updated_at, datetime.datetime), (
            "busyness_updated_at should be a datetime instance"
        )

    @pytest.mark.asyncio
    async def test_scrape_live_busyness_handles_failure(self):
        """Failed live busyness scrape should not stop other places."""
        place1 = _make_place_row(1, "ChIJ_fail_live", busyness_data={})
        place2 = _make_place_row(2, "ChIJ_ok_live", busyness_data={})

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [place1, place2]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        call_count = 0

        def side_effect(google_place_id):
            nonlocal call_count
            call_count += 1
            if google_place_id == "ChIJ_fail_live":
                return None  # Simulate failure
            return 50

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_live_busyness", side_effect=side_effect),
            patch("app.workers.scraping.asyncio") as mock_asyncio,
            patch("app.workers.scraping._get_active_place_ids") as mock_active,
        ):
            mock_asyncio.sleep = AsyncMock()
            mock_active.return_value = {1, 2}

            await scrape_live_busyness(ctx)

        assert call_count == 2, "Both places should be attempted"

    @pytest.mark.asyncio
    async def test_scrape_live_busyness_exception_triggers_rollback(self):
        """An exception during processing should trigger session.rollback() and not stop other places."""
        place1 = _make_place_row(1, "ChIJ_explode_live", busyness_data={})
        place2 = _make_place_row(2, "ChIJ_ok_live", busyness_data={"popular_times": []})

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [place1, place2]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        fetch_call_count = 0

        def fetch_side_effect(google_place_id):
            nonlocal fetch_call_count
            fetch_call_count += 1
            # Return valid data for both -- exception comes from commit
            return 72

        # Make commit raise on the first call, succeed on the second
        commit_call_count = 0

        async def commit_side_effect():
            nonlocal commit_call_count
            commit_call_count += 1
            if commit_call_count == 1:
                raise RuntimeError("Simulated DB error during live busyness commit")
            return None

        mock_session.commit = AsyncMock(side_effect=commit_side_effect)

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_live_busyness", side_effect=fetch_side_effect),
            patch("app.workers.scraping.asyncio") as mock_asyncio,
            patch("app.workers.scraping._get_active_place_ids") as mock_active,
        ):
            mock_asyncio.sleep = AsyncMock()
            mock_active.return_value = {1, 2}

            # Should NOT raise -- exceptions are caught per-place
            await scrape_live_busyness(ctx)

        # Both places should have been attempted
        assert fetch_call_count == 2, (
            f"Both places should be attempted even if first raises; got {fetch_call_count}"
        )
        # session.rollback() should have been called for the failed place
        mock_session.rollback.assert_called()
        # The second place should have committed successfully
        assert commit_call_count == 2, (
            "commit should have been called twice (once failing, once succeeding)"
        )
        # The second place should have its current_popularity updated
        assert place2.busyness_data is not None, (
            "Second place should have busyness_data set despite first place failing"
        )
        assert place2.busyness_data.get("current_popularity") == 72, (
            "Second place should have current_popularity = 72"
        )
        assert place2.busyness_updated_at is not None, (
            "Second place should have busyness_updated_at set"
        )

    @pytest.mark.asyncio
    async def test_scrape_live_busyness_skips_when_no_active_places(self):
        """When there are no active places, the task should complete without scraping."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session),
            patch("app.workers.scraping.fetch_live_busyness") as mock_fetch,
            patch("app.workers.scraping._get_active_place_ids") as mock_active,
        ):
            mock_active.return_value = set()

            await scrape_live_busyness(ctx)

        mock_fetch.assert_not_called()


# ---------------------------------------------------------------------------
# Worker Session Independence Tests
# ---------------------------------------------------------------------------


class TestWorkerSessionIndependence:
    """Verify the worker creates its own AsyncSession."""

    @pytest.mark.asyncio
    async def test_scrape_popular_times_uses_own_session(self):
        """Worker must create its own AsyncSessionLocal, not depend on request scope."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session) as mock_factory,
            patch("app.workers.scraping._get_activity_counts") as mock_activity,
        ):
            mock_activity.return_value = {}
            await scrape_popular_times(ctx)

        # AsyncSessionLocal should have been called (creating a new session)
        mock_factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_live_busyness_uses_own_session(self):
        """Worker must create its own AsyncSessionLocal when there are active places."""
        place = _make_place_row(1, "ChIJ_session_test", busyness_data={})

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [place]
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ctx = {"redis": AsyncMock()}

        with (
            patch("app.workers.scraping.AsyncSessionLocal", return_value=mock_session) as mock_factory,
            patch("app.workers.scraping._get_active_place_ids") as mock_active,
            patch("app.workers.scraping.fetch_live_busyness") as mock_fetch,
            patch("app.workers.scraping.asyncio") as mock_asyncio,
        ):
            mock_active.return_value = {1}
            mock_fetch.return_value = 50
            mock_asyncio.sleep = AsyncMock()
            await scrape_live_busyness(ctx)

        # AsyncSessionLocal should have been called (creating a new session)
        mock_factory.assert_called_once()


# ---------------------------------------------------------------------------
# Throughput Enforcement Tests
# ---------------------------------------------------------------------------


class TestThroughputEnforcement:
    """Verify the pipeline respects 100 places/hour throughput limit."""

    def test_scrape_delay_is_at_least_36_seconds(self):
        """100 places/hour = 1 place per 36 seconds minimum."""
        assert SCRAPE_DELAY_SECONDS >= 36, (
            f"SCRAPE_DELAY_SECONDS ({SCRAPE_DELAY_SECONDS}) must be >= 36 "
            "for 100 places/hour throughput limit"
        )
