"""Tests for socialia scheduler module.

Each scheduler API now accepts an explicit ``schedule_file=`` kwarg
(see ``feat(injection)`` commit), so tests can point the file at
``tmp_path`` without monkey-patching module globals.
"""

import json
from datetime import datetime, timedelta

import pytest

from socialia.scheduler import (
    cancel_scheduled,
    list_scheduled,
    parse_schedule_time,
    run_due_jobs,
    schedule_post,
)


# --- Helpers ----------------------------------------------------------------


@pytest.fixture
def schedule_file(tmp_path):
    """Per-test scheduler JSON file under tmp_path."""
    sf = tmp_path / "scheduled.json"
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text("[]")
    return sf


# --- parse_schedule_time ----------------------------------------------------


class TestParseScheduleTime:
    def test_relative_hours_format_returns_datetime_near_target(self):
        # Arrange
        expected = datetime.now() + timedelta(hours=1)
        # Act
        result = parse_schedule_time("+1h")
        # Assert
        assert abs((result - expected).total_seconds()) < 2

    def test_relative_minutes_format_returns_datetime_near_target(self):
        # Arrange
        expected = datetime.now() + timedelta(minutes=30)
        # Act
        result = parse_schedule_time("+30m")
        # Assert
        assert abs((result - expected).total_seconds()) < 2

    def test_time_only_format_resolves_to_target_hour(self):
        # Arrange
        target_hh = 10
        # Act
        result = parse_schedule_time("10:00")
        # Assert
        assert result.hour == target_hh

    def test_time_only_format_resolves_to_target_minute(self):
        # Arrange
        target_mm = 0
        # Act
        result = parse_schedule_time("10:00")
        # Assert
        assert result.minute == target_mm

    def test_full_datetime_format_returns_target_year(self):
        # Arrange
        target = "2026-01-25 14:30"
        # Act
        result = parse_schedule_time(target)
        # Assert
        assert result.year == 2026

    def test_full_datetime_format_returns_target_month(self):
        # Arrange
        target = "2026-01-25 14:30"
        # Act
        result = parse_schedule_time(target)
        # Assert
        assert result.month == 1

    def test_full_datetime_format_returns_target_day(self):
        # Arrange
        target = "2026-01-25 14:30"
        # Act
        result = parse_schedule_time(target)
        # Assert
        assert result.day == 25

    def test_full_datetime_format_returns_target_hour(self):
        # Arrange
        target = "2026-01-25 14:30"
        # Act
        result = parse_schedule_time(target)
        # Assert
        assert result.hour == 14

    def test_full_datetime_format_returns_target_minute(self):
        # Arrange
        target = "2026-01-25 14:30"
        # Act
        result = parse_schedule_time(target)
        # Assert
        assert result.minute == 30

    def test_invalid_format_raises_value_error(self):
        # Arrange
        bad_input = "invalid-time-format"
        # Act
        ctx = pytest.raises(ValueError)
        # Assert
        with ctx:
            parse_schedule_time(bad_input)


# --- schedule_post ----------------------------------------------------------


class TestSchedulePost:
    def test_schedule_post_with_valid_time_marks_success_true(self, schedule_file):
        # Arrange
        # (schedule_file fixture sets up an empty scheduled.json)
        # Act
        result = schedule_post(
            "twitter", "Test post", "+1h", schedule_file=schedule_file
        )
        # Assert
        assert result["success"] is True

    def test_schedule_post_with_valid_time_returns_job_id(self, schedule_file):
        # Arrange
        # (schedule_file fixture sets up an empty scheduled.json)
        # Act
        result = schedule_post(
            "twitter", "Test post", "+1h", schedule_file=schedule_file
        )
        # Assert
        assert "job_id" in result

    def test_schedule_post_with_valid_time_returns_scheduled_for(self, schedule_file):
        # Arrange
        # (schedule_file fixture sets up an empty scheduled.json)
        # Act
        result = schedule_post(
            "twitter", "Test post", "+1h", schedule_file=schedule_file
        )
        # Assert
        assert "scheduled_for" in result

    def test_schedule_post_with_invalid_time_marks_success_false(self, schedule_file):
        # Arrange
        # (schedule_file fixture sets up an empty scheduled.json)
        # Act
        result = schedule_post(
            "twitter", "Test", "invalid", schedule_file=schedule_file
        )
        # Assert
        assert result["success"] is False

    def test_schedule_post_with_invalid_time_returns_error_key(self, schedule_file):
        # Arrange
        # (schedule_file fixture sets up an empty scheduled.json)
        # Act
        result = schedule_post(
            "twitter", "Test", "invalid", schedule_file=schedule_file
        )
        # Assert
        assert "error" in result


# --- list_scheduled --------------------------------------------------------


class TestListScheduled:
    def test_list_returns_empty_list_when_no_jobs_recorded(self, schedule_file):
        # Arrange
        # (schedule_file already contains "[]")
        # Act
        result = list_scheduled(schedule_file=schedule_file)
        # Assert
        assert result == []

    def test_list_returns_one_entry_when_one_pending_job_exists(self, schedule_file):
        # Arrange
        jobs = [
            {
                "id": "test-123",
                "platform": "twitter",
                "text": "Test",
                "scheduled_for": "2026-01-25 10:00:00",
                "created_at": "2026-01-22 09:00:00",
                "status": "pending",
                "kwargs": {},
            }
        ]
        schedule_file.write_text(json.dumps(jobs))
        # Act
        result = list_scheduled(schedule_file=schedule_file)
        # Assert
        assert len(result) == 1

    def test_list_returns_pending_job_with_expected_id(self, schedule_file):
        # Arrange
        jobs = [
            {
                "id": "test-123",
                "platform": "twitter",
                "text": "Test",
                "scheduled_for": "2026-01-25 10:00:00",
                "created_at": "2026-01-22 09:00:00",
                "status": "pending",
                "kwargs": {},
            }
        ]
        schedule_file.write_text(json.dumps(jobs))
        # Act
        result = list_scheduled(schedule_file=schedule_file)
        # Assert
        assert result[0]["id"] == "test-123"


# --- cancel_scheduled ------------------------------------------------------


class TestCancelScheduled:
    def test_cancel_nonexistent_job_marks_success_false(self, schedule_file):
        # Arrange
        # (schedule_file already contains "[]")
        # Act
        result = cancel_scheduled("nonexistent-id", schedule_file=schedule_file)
        # Assert
        assert result["success"] is False

    def test_cancel_nonexistent_job_error_mentions_not_found(self, schedule_file):
        # Arrange
        # (schedule_file already contains "[]")
        # Act
        result = cancel_scheduled("nonexistent-id", schedule_file=schedule_file)
        # Assert
        assert "not found" in result["error"].lower()

    def test_cancel_existing_job_marks_success_true(self, schedule_file):
        # Arrange
        jobs = [
            {
                "id": "test-123",
                "platform": "twitter",
                "text": "Test",
                "scheduled_for": "2026-01-25 10:00:00",
                "created_at": "2026-01-22 09:00:00",
                "status": "pending",
                "kwargs": {},
            }
        ]
        schedule_file.write_text(json.dumps(jobs))
        # Act
        result = cancel_scheduled("test-123", schedule_file=schedule_file)
        # Assert
        assert result["success"] is True

    def test_cancel_existing_job_removes_it_from_pending_listing(self, schedule_file):
        # Arrange
        jobs = [
            {
                "id": "test-123",
                "platform": "twitter",
                "text": "Test",
                "scheduled_for": "2026-01-25 10:00:00",
                "created_at": "2026-01-22 09:00:00",
                "status": "pending",
                "kwargs": {},
            }
        ]
        schedule_file.write_text(json.dumps(jobs))
        cancel_scheduled("test-123", schedule_file=schedule_file)
        # Act
        remaining = list_scheduled(schedule_file=schedule_file)
        # Assert
        assert len(remaining) == 0


# --- run_due_jobs ----------------------------------------------------------


class TestRunDueJobs:
    def test_run_due_jobs_returns_empty_list_when_no_jobs_recorded(self, schedule_file):
        # Arrange
        # (schedule_file already contains "[]")
        # Act
        results = run_due_jobs(schedule_file=schedule_file)
        # Assert
        assert results == []

    def test_run_due_jobs_skips_jobs_scheduled_for_the_future(self, schedule_file):
        # Arrange
        future_time = (datetime.now() + timedelta(hours=24)).isoformat()
        jobs = [
            {
                "id": "future-job",
                "platform": "twitter",
                "text": "Future post",
                "scheduled_for": future_time,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "kwargs": {},
            }
        ]
        schedule_file.write_text(json.dumps(jobs))
        # Act
        results = run_due_jobs(schedule_file=schedule_file)
        # Assert
        assert results == []

    def test_run_due_jobs_leaves_future_jobs_in_pending_listing(self, schedule_file):
        # Arrange
        future_time = (datetime.now() + timedelta(hours=24)).isoformat()
        jobs = [
            {
                "id": "future-job",
                "platform": "twitter",
                "text": "Future post",
                "scheduled_for": future_time,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "kwargs": {},
            }
        ]
        schedule_file.write_text(json.dumps(jobs))
        run_due_jobs(schedule_file=schedule_file)
        # Act
        remaining = list_scheduled(schedule_file=schedule_file)
        # Assert
        assert len(remaining) == 1
