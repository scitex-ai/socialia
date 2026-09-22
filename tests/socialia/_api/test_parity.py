"""Tests for the public sync Python API (`socialia._api`, §6 parity surface)."""

import socialia
from socialia import _api as api


# --- lazy exports ----------------------------------------------------------


class TestLazyExports:
    def test_top_level_exposes_parity_names(self):
        # Arrange
        # (no setup)
        # Act
        missing = [n for n in api.__all__ if not callable(getattr(socialia, n))]
        # Assert
        assert missing == []


# --- behavior --------------------------------------------------------------


class TestSyncApi:
    def test_get_usage_mentions_twitter_strategy(self):
        # Arrange
        # (no setup)
        # Act
        guide = socialia.get_usage()
        # Assert
        assert "Twitter" in guide

    def test_social_status_result_carries_cli_command(self):
        # Arrange
        # (no setup — status without credentials returns a failure dict)
        # Act
        out = socialia.social_status("twitter")
        # Assert
        assert out["cli_command"] == "socialia status twitter"
