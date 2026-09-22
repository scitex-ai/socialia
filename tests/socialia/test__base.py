"""Tests for socialia base module."""

import pytest

from socialia._base import _Base


class ConcretePoster(_Base):
    """Concrete implementation for testing."""

    platform_name = "test"

    def post(self, text: str, **kwargs) -> dict:
        return {"success": True, "id": "123", "text": text}

    def delete(self, post_id: str) -> dict:
        return {"success": True, "deleted": post_id}


class TestBase:
    """Test _Base base class."""

    def test_base_class_is_abstract_and_blocks_direct_instantiation(self):
        # Arrange
        ctx = pytest.raises(TypeError)
        # Act
        # (entering the context is the assert step below)
        # Assert
        with ctx:
            _Base()

    def test_concrete_subclass_post_reports_success_true(self):
        # Arrange
        poster = ConcretePoster()
        # Act
        result = poster.post("test")
        # Assert
        assert result["success"] is True

    def test_default_feed_returns_success_false(self):
        # Arrange
        poster = ConcretePoster()
        # Act
        result = poster.feed()
        # Assert
        assert result["success"] is False

    def test_default_feed_error_message_says_not_implemented(self):
        # Arrange
        poster = ConcretePoster()
        # Act
        result = poster.feed()
        # Assert
        assert "not implemented" in result["error"].lower()

    def test_default_mentions_returns_success_false(self):
        # Arrange
        poster = ConcretePoster()
        # Act
        result = poster.mentions()
        # Assert
        assert result["success"] is False

    def test_default_me_returns_success_false(self):
        # Arrange
        poster = ConcretePoster()
        # Act
        result = poster.me()
        # Assert
        assert result["success"] is False

    def test_default_check_reports_subclass_platform_name(self):
        # Arrange
        poster = ConcretePoster()
        # Act
        result = poster.check()
        # Assert
        assert result["platform"] == "test"


class TestBranding:
    """Test branding module."""

    def test_get_env_var_name_uses_current_env_prefix(self):
        # Arrange
        from socialia._branding import get_env_var_name, ENV_PREFIX
        # Act
        result = get_env_var_name("X_CONSUMER_KEY")
        # Assert
        assert result == f"{ENV_PREFIX}_X_CONSUMER_KEY"

    def test_get_env_returns_default_when_var_unset(self):
        # Arrange
        from socialia._branding import get_env
        # Act
        result = get_env(
            "TOTALLY_UNIQUE_NONEXISTENT_VAR_XYZ123",
            "default_value",
        )
        # Assert
        assert result == "default_value"

    def test_get_env_reads_socialia_prefixed_var(self, env_save_restore):
        # Arrange
        from socialia._branding import get_env
        env_save_restore.set("SOCIALIA_TEST_UNIQUE_VAR", "test_value")
        # Act
        result = get_env("TEST_UNIQUE_VAR")
        # Assert
        assert result == "test_value"

    def test_get_mcp_server_name_returns_nonempty_string(self):
        # Arrange
        from socialia._branding import get_mcp_server_name
        # Act
        name = get_mcp_server_name()
        # Assert
        assert isinstance(name, str) and len(name) > 0


class TestPlatformImports:
    """Test that all platform classes can be imported."""

    def test_top_level_module_exports_twitter_symbol(self):
        # Arrange
        from socialia import Twitter
        # Act
        klass = Twitter
        # Assert
        assert klass is not None

    def test_top_level_module_exports_linkedin_symbol(self):
        # Arrange
        from socialia import LinkedIn
        # Act
        klass = LinkedIn
        # Assert
        assert klass is not None

    def test_top_level_module_exports_reddit_symbol(self):
        # Arrange
        from socialia import Reddit
        # Act
        klass = Reddit
        # Assert
        assert klass is not None

    def test_top_level_module_exports_youtube_symbol(self):
        # Arrange
        from socialia import YouTube
        # Act
        klass = YouTube
        # Assert
        assert klass is not None

    def test_top_level_module_exports_google_analytics_symbol(self):
        # Arrange
        from socialia import GoogleAnalytics
        # Act
        klass = GoogleAnalytics
        # Assert
        assert klass is not None


class TestVersion:
    """Test version information."""

    def test_version_attribute_is_a_string(self):
        # Arrange
        from socialia import __version__
        # Act
        value = __version__
        # Assert
        assert isinstance(value, str)

    def test_version_string_is_nonempty(self):
        # Arrange
        from socialia import __version__
        # Act
        length = len(__version__)
        # Assert
        assert length > 0

    def test_version_has_at_least_two_dotted_parts(self):
        # Arrange
        from socialia import __version__
        # Act
        parts = __version__.split(".")
        # Assert
        assert len(parts) >= 2

    def test_version_major_and_minor_parts_are_numeric(self):
        # Arrange
        from socialia import __version__
        parts = __version__.split(".")
        # Act
        both_numeric = parts[0].isdigit() and parts[1].isdigit()
        # Assert
        assert both_numeric
