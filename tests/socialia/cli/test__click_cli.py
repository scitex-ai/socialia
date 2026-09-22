"""Tests for socialia CLI (Click-based, post-audit migration).

Parser-shape tests (argparse-only) have been removed. Behavior is tested via
the public ``main(argv)`` entry point, which now wraps Click + a backward-compat
argv-rewrite shim so deprecated subcommand names still work.
"""

import pytest

from socialia.cli import main


# --- dry-run --------------------------------------------------------------


class TestCLIDryRun:
    def test_post_dry_run_twitter_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["post", "twitter", "Test message", "--dry-run"])
        # Assert
        assert result == 0

    def test_post_dry_run_twitter_output_mentions_dry_run_banner(self, capsys):
        # Arrange
        main(["post", "twitter", "Test message", "--dry-run"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "DRY RUN" in out

    def test_post_dry_run_twitter_output_mentions_twitter_platform(self, capsys):
        # Arrange
        main(["post", "twitter", "Test message", "--dry-run"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "twitter" in out.lower()

    def test_post_dry_run_linkedin_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["post", "linkedin", "Test message", "--dry-run"])
        # Assert
        assert result == 0

    def test_post_dry_run_linkedin_output_mentions_dry_run_banner(self, capsys):
        # Arrange
        main(["post", "linkedin", "Test message", "--dry-run"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "DRY RUN" in out

    def test_post_dry_run_linkedin_output_mentions_linkedin_platform(
        self, capsys
    ):
        # Arrange
        main(["post", "linkedin", "Test message", "--dry-run"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "linkedin" in out.lower()


# --- main / no-command ----------------------------------------------------


class TestCLINoCommand:
    def test_main_without_arguments_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main([])
        # Assert
        assert result == 0

    def test_main_without_arguments_renders_help_text(self, capsys):
        # Arrange
        main([])
        # Act
        out = capsys.readouterr().out.lower()
        # Assert
        assert "usage:" in out or "socialia" in out

    def test_help_recursive_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["--help-recursive"])
        # Assert
        assert result == 0

    def test_help_recursive_output_includes_post_subcommand(self, capsys):
        # Arrange
        main(["--help-recursive"])
        # Act
        out = capsys.readouterr().out.lower()
        # Assert
        assert "post" in out

    def test_help_recursive_output_includes_delete_post_subcommand(self, capsys):
        # Arrange
        main(["--help-recursive"])
        # Act
        out = capsys.readouterr().out.lower()
        # Assert
        assert "delete-post" in out


# --- show-status -----------------------------------------------------------


class TestCLIStatus:
    def test_show_status_canonical_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["show-status"])
        # Assert
        assert result == 0

    def test_show_status_canonical_output_mentions_socialia(self, capsys):
        # Arrange
        main(["show-status"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "Socialia" in out or "socialia" in out.lower()

    def test_status_deprecated_alias_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["status"])
        # Assert
        assert result == 0


# --- mcp list-tools --------------------------------------------------------


class TestCLIMCPListTools:
    def test_mcp_list_tools_returns_exit_zero(self, capsys):
        # Arrange
        pytest.importorskip("fastmcp", reason="fastmcp not installed")
        # Act
        result = main(["mcp", "list-tools"])
        # Assert
        assert result == 0

    def test_mcp_list_tools_output_mentions_mcp_or_tools(self, capsys):
        # Arrange
        pytest.importorskip("fastmcp", reason="fastmcp not installed")
        main(["mcp", "list-tools"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "MCP" in out or "Tools" in out


# --- completion -----------------------------------------------------------


class TestCLICompletion:
    def test_show_completion_bash_canonical_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["show-completion-bash"])
        # Assert
        assert result == 0

    def test_show_completion_bash_output_mentions_argcomplete_or_compdef(
        self, capsys
    ):
        # Arrange
        main(["show-completion-bash"])
        # Act
        out = capsys.readouterr().out.lower()
        # Assert
        assert "argcomplete" in out or "compdef" in out

    def test_completion_bash_deprecated_alias_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["completion", "bash"])
        # Assert
        assert result == 0

    def test_show_completion_zsh_canonical_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["show-completion-zsh"])
        # Assert
        assert result == 0

    def test_show_completion_zsh_output_mentions_compdef_or_bashcompinit(
        self, capsys
    ):
        # Arrange
        main(["show-completion-zsh"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "compdef" in out or "bashcompinit" in out

    def test_completion_status_alias_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["completion", "status"])
        # Assert
        assert result == 0

    def test_completion_status_alias_output_contains_status_header(self, capsys):
        # Arrange
        main(["completion", "status"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "Completion Status" in out


# --- deprecation aliases ---------------------------------------------------


class TestCLIDeprecationAliases:
    """Verify backward-compat shim covers the renamed subcommands."""

    @pytest.mark.parametrize(
        "argv",
        [
            ["delete", "twitter", "123", "--dry-run"],
            ["setup"],
            ["check", "twitter"],
            ["me", "twitter"],
            ["analytics", "realtime"],
            ["analytics", "pageviews"],
            ["analytics", "sources"],
            ["mcp", "installation"],
            ["schedule", "run"],
            ["schedule", "daemon", "--dry-run"],
            ["completion", "bash"],
            ["completion", "zsh"],
            ["completion", "status"],
            ["org", "status", "/tmp/nonexistent.org"],
            ["youtube", "config", "--scitex"],
            ["grow", "twitter", "auto", "test", "--dry-run"],
            ["grow", "twitter", "user", "ywatanabe"],
        ],
    )
    def test_deprecated_alias_argv_does_not_raise_unexpected_exception(
        self, argv
    ):
        # Arrange
        # We don't assert on exit code; some require live creds.
        completed_without_unexpected_exception = False
        # Act
        try:
            main(argv)
            completed_without_unexpected_exception = True
        except SystemExit:
            completed_without_unexpected_exception = True
        # Assert
        assert completed_without_unexpected_exception
