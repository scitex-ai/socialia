#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-01-27
# File: src/socialia/_mcp/tools/__init__.py

"""MCP tool registration for Socialia."""

from __future__ import annotations

# PS-233: fastmcp lives in the optional [mcp] extra — guard the import so
# lean installs keep working. Annotation-only use below (this module has
# `from __future__ import annotations`), so None is safe.
try:
    from fastmcp import FastMCP
except ImportError:  # lean install without socialia[mcp]
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
