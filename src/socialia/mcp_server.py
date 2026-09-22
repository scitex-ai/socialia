#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-01-27
# File: src/socialia/mcp_server.py

"""
Socialia MCP Server - Backwards Compatibility Module.

This module is kept for backwards compatibility.
The implementation has been migrated to FastMCP in _server.py.

For new code, use:
    from socialia._server import mcp, run_server
    from socialia._mcp.tools import register_all_tools
"""

from __future__ import annotations

# Check if FastMCP is available
import sys

from scitex_dev import try_import_optional

import scitex_logging as slogging

log = slogging.getLogger(__name__)

fastmcp = try_import_optional("fastmcp", extra="mcp", pkg="fastmcp")
HAS_MCP = fastmcp is not None
del fastmcp

# Re-export from new location for backwards compatibility
if HAS_MCP:
    from socialia._server import mcp, run_server, PLATFORM_STRATEGIES

    # Legacy entry point
    async def main():
        """Legacy async main entry point."""
        run_server()

    create_server = lambda: mcp  # noqa: E731
else:
    mcp = None
    run_server = None
    PLATFORM_STRATEGIES = ""

    async def main():
        """Stub when MCP not installed."""
        import sys

        log.error("Error: MCP package not installed. Run: pip install socialia[mcp]")
        sys.exit(1)

    create_server = lambda: None  # noqa: E731

if __name__ == "__main__":
    if HAS_MCP:
        run_server()

# EOF
