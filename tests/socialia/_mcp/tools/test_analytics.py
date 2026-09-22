"""Tests for socialia._mcp.tools.analytics — analytics tool registration."""

from __future__ import annotations

import pytest

pytest.importorskip("fastmcp", reason="fastmcp not installed")

from socialia._mcp.tools import analytics


class _FakeMCP:
    """Minimal stand-in for FastMCP's tool registry (no server started)."""

    def __init__(self):
        self.registered = []

    def tool(self):
        def deco(fn):
            self.registered.append(fn.__name__)
            return fn

        return deco


def test_analytics_tools_register_expected_tool_names():
    # Arrange — a recording registry instead of a live MCP server.
    mcp = _FakeMCP()
    # Act
    analytics.register_tools(mcp)
    # Assert
    assert {
        "social_analytics_track",
        "social_analytics_pageviews",
        "social_analytics_sources",
        "social_analytics_realtime",
    } <= set(mcp.registered)
