#!/usr/bin/env python3
"""Tests for org mode draft management."""

from datetime import datetime, timedelta

import pytest

from socialia.org import OrgDraft, OrgDraftManager, OrgParser


# --- Shared fixtures --------------------------------------------------------


@pytest.fixture
def sample_org_content():
    """Sample org file content for testing."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    return f"""#+TITLE: Test Drafts
#+AUTHOR: test

* Drafts [0/3]

** TODO [#A] Future Post
   SCHEDULED: <{tomorrow} 10:00>
   :PROPERTIES:
   :PLATFORM: twitter
   :ID: draft-001
   :END:

This is a future post.

** TODO [#B] Due Post
   SCHEDULED: <{yesterday} 10:00>
   :PROPERTIES:
   :PLATFORM: twitter
   :ID: draft-002
   :END:

This post is due.

** DONE [#C] Completed Post
   SCHEDULED: <{yesterday} 09:00>
   :PROPERTIES:
   :PLATFORM: linkedin
   :ID: draft-003
   :END:

This was already posted.

* Archive
# Completed posts go here
"""


@pytest.fixture
def org_file(sample_org_content, tmp_path):
    """Create a temporary org file."""
    filepath = tmp_path / "test_drafts.org"
    filepath.write_text(sample_org_content)
    return filepath


@pytest.fixture
def parsed_drafts(org_file):
    """Parsed drafts from the shared sample org file."""
    return OrgParser(org_file).parse()


# --- OrgParser -------------------------------------------------------------


class TestOrgParser:
    def test_parse_returns_three_drafts_for_sample_content(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        count = len(parsed_drafts)
        # Assert
        assert count == 3

    def test_parse_first_draft_headline_is_future_post(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        headline = parsed_drafts[0].headline
        # Assert
        assert headline == "Future Post"

    def test_parse_second_draft_headline_is_due_post(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        headline = parsed_drafts[1].headline
        # Assert
        assert headline == "Due Post"

    def test_parse_third_draft_headline_is_completed_post(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        headline = parsed_drafts[2].headline
        # Assert
        assert headline == "Completed Post"

    def test_parse_first_draft_status_is_todo(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        status = parsed_drafts[0].status
        # Assert
        assert status == "TODO"

    def test_parse_second_draft_status_is_todo(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        status = parsed_drafts[1].status
        # Assert
        assert status == "TODO"

    def test_parse_third_draft_status_is_done(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        status = parsed_drafts[2].status
        # Assert
        assert status == "DONE"

    def test_parse_first_draft_priority_is_a(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        priority = parsed_drafts[0].priority
        # Assert
        assert priority == "A"

    def test_parse_second_draft_priority_is_b(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        priority = parsed_drafts[1].priority
        # Assert
        assert priority == "B"

    def test_parse_third_draft_priority_is_c(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        priority = parsed_drafts[2].priority
        # Assert
        assert priority == "C"

    def test_parse_first_draft_platform_is_twitter(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        platform = parsed_drafts[0].platform
        # Assert
        assert platform == "twitter"

    def test_parse_second_draft_platform_is_twitter(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        platform = parsed_drafts[1].platform
        # Assert
        assert platform == "twitter"

    def test_parse_third_draft_platform_is_linkedin(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        platform = parsed_drafts[2].platform
        # Assert
        assert platform == "linkedin"

    def test_parse_first_draft_has_scheduled_timestamp_present(
        self, parsed_drafts
    ):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        scheduled = parsed_drafts[0].scheduled
        # Assert
        assert scheduled is not None

    def test_parse_first_draft_scheduled_hour_matches_sample(
        self, parsed_drafts
    ):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        hour = parsed_drafts[0].scheduled.hour
        # Assert
        assert hour == 10

    def test_parse_first_draft_scheduled_minute_matches_sample(
        self, parsed_drafts
    ):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        minute = parsed_drafts[0].scheduled.minute
        # Assert
        assert minute == 0

    def test_parse_first_draft_content_includes_future_post_phrase(
        self, parsed_drafts
    ):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        content = parsed_drafts[0].content.lower()
        # Assert
        assert "future post" in content

    def test_parse_second_draft_content_includes_due_phrase(self, parsed_drafts):
        # Arrange
        # (drafts already parsed by fixture)
        # Act
        content = parsed_drafts[1].content.lower()
        # Assert
        assert "due" in content

    def test_parse_skips_level_one_headings_returns_only_level_two(
        self, tmp_path
    ):
        # Arrange
        content = """* Level One
This should be skipped.

** TODO Level Two
   :PROPERTIES:
   :PLATFORM: twitter
   :END:

This should be parsed.
"""
        filepath = tmp_path / "test.org"
        filepath.write_text(content)
        parser = OrgParser(filepath)
        # Act
        drafts = parser.parse()
        # Assert
        assert len(drafts) == 1

    def test_parse_skips_level_one_headings_keeps_correct_headline(
        self, tmp_path
    ):
        # Arrange
        content = """* Level One
This should be skipped.

** TODO Level Two
   :PROPERTIES:
   :PLATFORM: twitter
   :END:

This should be parsed.
"""
        filepath = tmp_path / "test.org"
        filepath.write_text(content)
        parser = OrgParser(filepath)
        # Act
        drafts = parser.parse()
        # Assert
        assert drafts[0].headline == "Level Two"


# --- OrgDraft --------------------------------------------------------------


def _draft(**overrides) -> OrgDraft:
    """Build a default OrgDraft for property-table testing."""
    base = dict(
        headline="Test",
        status="TODO",
        priority="A",
        scheduled=None,
        platform="twitter",
        draft_id="001",
        content="Test content",
        line_number=0,
    )
    base.update(overrides)
    return OrgDraft(**base)


class TestOrgDraftIsPending:
    def test_is_pending_true_for_todo_status(self):
        # Arrange
        draft = _draft(status="TODO")
        # Act
        result = draft.is_pending
        # Assert
        assert result is True

    def test_is_pending_false_for_done_status(self):
        # Arrange
        draft = _draft(status="DONE")
        # Act
        result = draft.is_pending
        # Assert
        assert result is False


class TestOrgDraftIsDue:
    def test_is_due_true_for_past_todo(self):
        # Arrange
        past = datetime.now() - timedelta(hours=1)
        draft = _draft(status="TODO", scheduled=past)
        # Act
        result = draft.is_due
        # Assert
        assert result is True

    def test_is_due_false_for_future_todo(self):
        # Arrange
        future = datetime.now() + timedelta(hours=1)
        draft = _draft(status="TODO", scheduled=future)
        # Act
        result = draft.is_due
        # Assert
        assert result is False

    def test_is_due_false_for_done_in_the_past(self):
        # Arrange
        past = datetime.now() - timedelta(hours=1)
        draft = _draft(status="DONE", scheduled=past)
        # Act
        result = draft.is_due
        # Assert
        assert result is False


# --- OrgDraftManager -------------------------------------------------------


class TestOrgDraftManager:
    def test_list_drafts_returns_all_three_entries(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        drafts = manager.list_drafts()
        # Assert
        assert len(drafts) == 3

    def test_list_drafts_filter_todo_returns_two_entries(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        pending = manager.list_drafts(status="TODO")
        # Assert
        assert len(pending) == 2

    def test_list_drafts_filter_done_returns_one_entry(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        done = manager.list_drafts(status="DONE")
        # Assert
        assert len(done) == 1

    def test_get_pending_returns_two_entries(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        pending = manager.get_pending()
        # Assert
        assert len(pending) == 2

    def test_get_pending_returns_only_todo_status_entries(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        pending = manager.get_pending()
        # Assert
        assert all(d.status == "TODO" for d in pending)

    def test_get_due_returns_one_entry_for_yesterday_schedule(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        due = manager.get_due()
        # Assert
        assert len(due) == 1

    def test_get_due_returns_due_post_headline(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        due = manager.get_due()
        # Assert
        assert due[0].headline == "Due Post"

    def test_get_scheduled_returns_one_future_entry(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        scheduled = manager.get_scheduled()
        # Assert
        assert len(scheduled) == 1

    def test_get_scheduled_returns_future_post_headline(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        scheduled = manager.get_scheduled()
        # Assert
        assert scheduled[0].headline == "Future Post"

    def test_status_report_total_is_three(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        report = manager.status_report()
        # Assert
        assert report["total"] == 3

    def test_status_report_pending_is_two(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        report = manager.status_report()
        # Assert
        assert report["pending"] == 2

    def test_status_report_done_is_one(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        report = manager.status_report()
        # Assert
        assert report["done"] == 1

    def test_status_report_due_now_is_one(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        report = manager.status_report()
        # Assert
        assert report["due_now"] == 1

    def test_status_report_scheduled_is_one(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        # Act
        report = manager.status_report()
        # Assert
        assert report["scheduled"] == 1

    def test_post_draft_dry_run_marks_success_true(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        draft = manager.get_pending()[0]
        # Act
        result = manager.post_draft(draft, dry_run=True)
        # Assert
        assert result["success"] is True

    def test_post_draft_dry_run_marks_dry_run_flag_true(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        draft = manager.get_pending()[0]
        # Act
        result = manager.post_draft(draft, dry_run=True)
        # Assert
        assert result["dry_run"] is True

    def test_post_draft_dry_run_returns_platform_from_draft(self, org_file):
        # Arrange
        manager = OrgDraftManager(org_file)
        draft = manager.get_pending()[0]
        # Act
        result = manager.post_draft(draft, dry_run=True)
        # Assert
        assert result["platform"] == "twitter"


# --- org CLI subcommands ---------------------------------------------------


class TestOrgCLI:
    def test_org_status_command_returns_exit_zero(self, org_file):
        # Arrange
        from socialia.cli import main
        # Act
        result = main(["org", "status", str(org_file)])
        # Assert
        assert result == 0

    def test_org_list_command_returns_exit_zero(self, org_file):
        # Arrange
        from socialia.cli import main
        # Act
        result = main(["org", "list", str(org_file)])
        # Assert
        assert result == 0

    def test_org_schedule_dry_run_returns_exit_zero(self, org_file):
        # Arrange
        from socialia.cli import main
        # Act
        result = main(["org", "schedule", str(org_file), "--dry-run"])
        # Assert
        assert result == 0

    def test_org_post_dry_run_returns_exit_zero(self, org_file):
        # Arrange
        from socialia.cli import main
        # Act
        result = main(["org", "post", str(org_file), "--dry-run"])
        # Assert
        assert result == 0

    def test_org_init_command_returns_exit_zero(self, tmp_path):
        # Arrange
        from socialia.cli import main
        filepath = tmp_path / "new_drafts.org"
        # Act
        result = main(["org", "init", str(filepath)])
        # Assert
        assert result == 0

    def test_org_init_creates_target_org_file(self, tmp_path):
        # Arrange
        from socialia.cli import main
        filepath = tmp_path / "new_drafts.org"
        # Act
        main(["org", "init", str(filepath)])
        # Assert
        assert filepath.exists()

    def test_org_init_writes_title_directive_into_file(self, tmp_path):
        # Arrange
        from socialia.cli import main
        filepath = tmp_path / "new_drafts.org"
        main(["org", "init", str(filepath)])
        # Act
        content = filepath.read_text()
        # Assert
        assert "#+TITLE:" in content

    def test_org_init_writes_todo_keyword_into_file(self, tmp_path):
        # Arrange
        from socialia.cli import main
        filepath = tmp_path / "new_drafts.org"
        main(["org", "init", str(filepath)])
        # Act
        content = filepath.read_text()
        # Assert
        assert "TODO" in content
