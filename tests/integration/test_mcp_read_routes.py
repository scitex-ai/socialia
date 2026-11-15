"""Real CLI/MCP route controls use an empty owned credential environment."""

import os

import pytest


_PLATFORMS = ["twitter", "linkedin", "reddit", "slack", "youtube"]


@pytest.fixture(autouse=True)
def _empty_read_context(tmp_path):
    """Own credential/file resolution and restore all touched environment keys."""
    keys = {
        "X_CONSUMER_KEY", "X_CONSUMER_KEY_SECRET", "X_ACCESSTOKEN",
        "X_ACCESSTOKEN_SECRET", "X_READ_BACKEND", "X_READ_USERNAME",
        "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET",
        "SLACK_BOT_TOKEN", "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME", "REDDIT_PASSWORD", "YOUTUBE_TOKEN_FILE",
        "YOUTUBE_CLIENT_SECRETS_FILE",
    }
    removed = {name for name in os.environ
               if name in keys or any(name.endswith("_" + key) for key in keys)
               or name in {"SOCIALIA_ENV_FILE", "SCITEX_SOCIAL_ENV_FILE"}}
    touched = removed | {"HOME", "SCITEX_DIR"}
    previous = {name: os.environ.get(name) for name in touched}
    home = tmp_path / "home"
    home.mkdir()
    for name in removed:
        os.environ.pop(name, None)
    os.environ.update(HOME=str(home), SCITEX_DIR=str(tmp_path / "state"))
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


@pytest.mark.parametrize("platform", _PLATFORMS)
@pytest.mark.parametrize("count", [1, 17])
def test_feed_handler_returns_platform_json_without_credentials(platform, count):
    # Arrange
    from socialia._mcp.handlers import social_feed
    expected = {
        platform: {"success": False, "error": "Not configured"},
        "cli_command": f"socialia feed {platform} --limit {count} --json",
    }
    # Act
    result = social_feed(platform, count=count)
    # Assert
    assert result == expected


@pytest.mark.parametrize("platform", _PLATFORMS)
def test_check_handler_returns_platform_json_without_credentials(platform):
    # Arrange
    from socialia._mcp.handlers import social_check
    expected = {
        platform: {"success": False, "platform": platform,
                   "status": "not_configured", "error": "Missing credentials"},
        "cli_command": f"socialia check-platforms {platform} --json",
    }
    # Act
    result = social_check(platform)
    # Assert
    assert result == expected
