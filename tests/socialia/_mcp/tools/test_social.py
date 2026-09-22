"""Tests for socialia._mcp.tools.social — social tool registration."""

from __future__ import annotations

import pytest

pytest.importorskip("fastmcp", reason="fastmcp not installed")

from socialia._mcp.tools import social


class _FakeMCP:
    """Minimal stand-in for FastMCP's tool registry (no server started)."""

    def __init__(self):
        self.registered = []

    def tool(self):
        def deco(fn):
            self.registered.append(fn.__name__)
            return fn

        return deco


def test_social_tools_register_expected_tool_names():
    # Arrange — a recording registry instead of a live MCP server.
    mcp = _FakeMCP()
    # Act
    social.register_tools(mcp)
    # Assert
    assert {"social_post", "social_delete", "social_status"} <= set(mcp.registered)
