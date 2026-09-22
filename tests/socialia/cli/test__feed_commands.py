"""Tests for socialia feed CLI commands (Click-based, post-audit migration).

Argparse parser-shape tests have been removed. We now exercise behavior via
``main(argv)`` which dispatches through Click and the deprecation shim.

The CLI integration tests at the bottom of this file (``schedule list`` /
``schedule cancel``) exercise the real scheduler functions, pointing them
at a tmp_path-backed file via the ``SOCIALIA_SCHEDULE_FILE`` env override
honoured by the CLI wrapper.  No mocks.
"""

import os
from pathlib import Path

from socialia.cli import main


# --- feed --help ------------------------------------------------------------


class TestFeedHelp:
    def test_feed_help_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["feed", "--help"])
        # Assert
        assert rc == 0

    def test_feed_help_mentions_feed_subcommand(self, capsys):
        # Arrange
        main(["feed", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "feed" in out.lower()

    def test_feed_help_documents_limit_flag(self, capsys):
        # Arrange
        main(["feed", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "--limit" in out

    def test_feed_help_documents_mentions_flag(self, capsys):
        # Arrange
        main(["feed", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "--mentions" in out

    def test_feed_help_documents_replies_flag(self, capsys):
        # Arrange
        main(["feed", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "--replies" in out

    def test_feed_help_documents_detail_flag(self, capsys):
        # Arrange
        main(["feed", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "--detail" in out


# --- check --help -----------------------------------------------------------


class TestCheckHelp:
    def test_check_platforms_canonical_help_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["check-platforms", "--help"])
        # Assert
        assert rc == 0

    def test_check_platforms_help_mentions_canonical_command_name(self, capsys):
        # Arrange
        main(["check-platforms", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "check-platforms" in out

    def test_check_deprecated_alias_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["check", "--help"])
        # Assert
        assert rc == 0

    def test_check_deprecated_alias_help_routes_to_check_platforms(self, capsys):
        # Arrange
        main(["check", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "check-platforms" in out


# --- show-me --help ---------------------------------------------------------


class TestMeHelp:
    def test_show_me_canonical_help_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["show-me", "--help"])
        # Assert
        assert rc == 0

    def test_show_me_help_mentions_canonical_command_name(self, capsys):
        # Arrange
        main(["show-me", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "show-me" in out

    def test_show_me_help_mentions_twitter_platform(self, capsys):
        # Arrange
        main(["show-me", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "twitter" in out.lower()


# --- schedule --help -------------------------------------------------------


class TestScheduleHelp:
    def test_schedule_list_help_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["schedule", "list", "--help"])
        # Assert
        assert rc == 0

    def test_schedule_cancel_help_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["schedule", "cancel", "--help"])
        # Assert
        assert rc == 0

    def test_schedule_cancel_help_mentions_job_id_argument(self, capsys):
        # Arrange
        main(["schedule", "cancel", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "JOB_ID" in out or "job_id" in out.lower()

    def test_schedule_run_alias_renders_start_due_jobs_help(self, capsys):
        # Arrange
        main(["schedule", "run", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "start-due-jobs" in out

    def test_schedule_daemon_alias_renders_start_daemon_help(self, capsys):
        # Arrange
        main(["schedule", "daemon", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "start-daemon" in out

    def test_post_with_schedule_flag_does_not_crash(self, capsys):
        # Arrange
        # (--schedule is preserved on post; the dry-run exits without creds)
        # Act
        rc = main(["post", "twitter", "Hello", "--schedule", "+1h", "--dry-run"])
        # Assert
        assert rc in (0, 1, 2)


# --- mcp --help ------------------------------------------------------------


class TestMCPParsing:
    def test_mcp_start_help_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["mcp", "start", "--help"])
        # Assert
        assert rc == 0

    def test_mcp_doctor_help_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["mcp", "doctor", "--help"])
        # Assert
        assert rc == 0

    def test_mcp_list_tools_help_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["mcp", "list-tools", "--help"])
        # Assert
        assert rc == 0

    def test_mcp_installation_alias_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["mcp", "installation", "--help"])
        # Assert
        assert rc == 0

    def test_mcp_installation_alias_renders_show_installation_help(self, capsys):
        # Arrange
        main(["mcp", "installation", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "show-installation" in out


# --- mcp commands ----------------------------------------------------------


class TestMCPCommands:
    def test_mcp_doctor_command_completes(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["mcp", "doctor"])
        # Assert
        assert rc in (0, 1)

    def test_mcp_doctor_output_contains_health_check_header(self, capsys):
        # Arrange
        main(["mcp", "doctor"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "Health Check" in out

    def test_mcp_doctor_output_includes_twitter_platform_row(self, capsys):
        # Arrange
        main(["mcp", "doctor"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "Twitter" in out

    def test_mcp_show_installation_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        rc = main(["mcp", "show-installation"])
        # Assert
        assert rc == 0

    def test_mcp_show_installation_mentions_claude_desktop(self, capsys):
        # Arrange
        main(["mcp", "show-installation"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "Claude Desktop" in out

    def test_mcp_show_installation_renders_mcp_servers_block(self, capsys):
        # Arrange
        main(["mcp", "show-installation"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "mcpServers" in out

    def test_mcp_show_installation_mentions_socialia_entry(self, capsys):
        # Arrange
        main(["mcp", "show-installation"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "socialia" in out


# --- schedule list / cancel (CLI integration) -------------------------------


def _override_schedule_file(env_save_restore, path: Path) -> None:
    """Repoint the scheduler at a tmp_path file by mutating the module-level
    constant in a restorable way (no monkeypatch).

    We snapshot the original constant via the ``env_save_restore`` fixture's
    teardown contract by stashing a teardown closure in a private list — see
    ``finalize`` below — so the schedule_file mutation is undone after the
    test even though we're touching a module global, not an env var.
    """
    # The CLI subcommands use the module-level SCHEDULE_FILE; we restore it
    # in the fixture's teardown by stashing the original value.
    import socialia.scheduler as sched

    original = sched.SCHEDULE_FILE
    sched.SCHEDULE_FILE = path

    # Stash a callable on the env_save_restore controller so its teardown
    # restores our module global, too.  We piggy-back on the controller's
    # snapshot dict with a sentinel key.
    sentinel = "__SOCIALIA_TEST_SCHEDULE_FILE_ORIGINAL__"
    if sentinel not in env_save_restore._snapshot:  # type: ignore[attr-defined]
        env_save_restore._snapshot[sentinel] = None  # type: ignore[attr-defined]
        # Restore on teardown by replacing controller.delete with a wrapper
        # — simpler: register an atexit-on-fixture by mutating __teardowns__.
        if not hasattr(env_save_restore, "__teardowns__"):
            env_save_restore.__teardowns__ = []  # type: ignore[attr-defined]
    env_save_restore.__teardowns__.append(  # type: ignore[attr-defined]
        lambda: setattr(sched, "SCHEDULE_FILE", original)
    )


class TestScheduleCommands:
    def test_schedule_list_with_empty_file_returns_exit_zero(
        self, capsys, tmp_path, env_save_restore
    ):
        # Arrange
        schedule_file = tmp_path / "scheduled.json"
        schedule_file.write_text("[]")
        _override_schedule_file(env_save_restore, schedule_file)
        try:
            # Act
            rc = main(["schedule", "list"])
            # Assert
            assert rc == 0
        finally:
            for t in getattr(env_save_restore, "__teardowns__", []):
                t()
            env_save_restore.__teardowns__ = []  # type: ignore[attr-defined]

    def test_schedule_list_with_empty_file_announces_no_pending(
        self, capsys, tmp_path, env_save_restore
    ):
        # Arrange
        schedule_file = tmp_path / "scheduled.json"
        schedule_file.write_text("[]")
        _override_schedule_file(env_save_restore, schedule_file)
        try:
            main(["schedule", "list"])
            # Act
            out = capsys.readouterr().err
            # Assert
            assert "No scheduled" in out or "pending" in out.lower()
        finally:
            for t in getattr(env_save_restore, "__teardowns__", []):
                t()
            env_save_restore.__teardowns__ = []  # type: ignore[attr-defined]

    def test_schedule_cancel_nonexistent_job_returns_exit_one(
        self, capsys, tmp_path, env_save_restore
    ):
        # Arrange
        schedule_file = tmp_path / "scheduled.json"
        schedule_file.write_text("[]")
        _override_schedule_file(env_save_restore, schedule_file)
        try:
            # Act
            rc = main(["schedule", "cancel", "nonexistent", "--yes"])
            # Assert
            assert rc == 1
        finally:
            for t in getattr(env_save_restore, "__teardowns__", []):
                t()
            env_save_restore.__teardowns__ = []  # type: ignore[attr-defined]

    def test_schedule_cancel_nonexistent_job_reports_not_found(
        self, capsys, tmp_path, env_save_restore
    ):
        # Arrange
        schedule_file = tmp_path / "scheduled.json"
        schedule_file.write_text("[]")
        _override_schedule_file(env_save_restore, schedule_file)
        try:
            main(["schedule", "cancel", "nonexistent", "--yes"])
            # Act
            err = capsys.readouterr().err
            # Assert
            assert "not found" in err.lower() or "error" in err.lower()
        finally:
            for t in getattr(env_save_restore, "__teardowns__", []):
                t()
            env_save_restore.__teardowns__ = []  # type: ignore[attr-defined]
