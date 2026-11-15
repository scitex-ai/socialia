"""Real CLI/MCP route controls use an empty owned credential environment."""

import asyncio
import os

import pytest


_PLATFORMS = ["twitter", "linkedin", "reddit", "slack", "youtube"]


@pytest.fixture(autouse=True)
def _empty_status_context(tmp_path):
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


def _expected(platform, command="check-platforms"):
    return {
        platform: {"success": False, "platform": platform,
                   "status": "not_configured", "error": "Missing credentials"},
        "cli_command": f"socialia {command} {platform} --json",
    }


@pytest.mark.parametrize("platform", _PLATFORMS)
def test_status_handler_uses_the_platform_specific_check_route(platform):
    # Arrange
    from socialia._mcp.handlers import social_status
    expected = _expected(platform)
    # Act
    result = social_status(platform)
    # Assert
    assert result == expected


@pytest.mark.parametrize("platform", _PLATFORMS)
def test_registered_status_tool_returns_the_requested_platform_check(platform):
    # Arrange
    fastmcp = pytest.importorskip("fastmcp")
    from socialia._mcp.tools.social import register_tools
    server = fastmcp.FastMCP("owned-status-route")
    register_tools(server)
    expected = _expected(platform)

    async def invoke():
        async with fastmcp.Client(server) as client:
            response = await client.call_tool("social_status", {"platform": platform})
            return response.structured_content

    # Act
    result = asyncio.run(invoke())
    # Assert
    assert result == expected


def test_legacy_check_alias_remains_available():
    # Arrange
    from socialia._mcp.handlers import run_cli
    expected = _expected("slack", command="check")
    # Act
    result = run_cli("check", "slack", "--json")
    # Assert
    assert result == expected
