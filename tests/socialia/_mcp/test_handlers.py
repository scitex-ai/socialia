"""Tests for socialia._mcp.handlers — CLI-delegating tool handlers."""

from __future__ import annotations

from socialia._mcp import handlers


def test_run_cli_records_reproducible_command_for_dry_run():
    # Arrange — a dry-run post needs no credentials and exits zero.
    argv = ("post", "twitter", "Hello", "--dry-run")
    # Act
    result = handlers.run_cli(*argv)
    # Assert
    assert result["success"] is True and result["cli_command"] == (
        "socialia post twitter Hello --dry-run"
    )


def test_social_post_delegates_dry_run_through_cli():
    # Arrange — handler builds the argv a user would type.
    # Act
    result = handlers.social_post("twitter", "Hello", dry_run=True)
    # Assert
    assert result["success"] is True and result["cli_command"] == (
        "socialia post twitter Hello --dry-run"
    )
