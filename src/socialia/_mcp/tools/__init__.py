#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-01-27
# File: src/socialia/_mcp/tools/__init__.py

"""MCP tool registration for Socialia."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import-time typing only
    from fastmcp import FastMCP

try:
    from fastmcp import FastMCP
except ImportError:  # optional [mcp] extra; imported only under HAS_MCP
    FastMCP = None  # type: ignore[assignment]


def register_all_tools(mcp: FastMCP) -> None:
    """
    Register all MCP tools with the server.

    This function enables thin wrapper delegation from other packages
    (e.g., scitex) to use socialia's tools as a single source of truth.

    Usage:
        from socialia._mcp.tools import register_all_tools
        register_all_tools(mcp)
    """
    from . import analytics, social

    # Register tools from each module
    social.register_tools(mcp)
    analytics.register_tools(mcp)


__all__ = ["register_all_tools"]

# EOF
