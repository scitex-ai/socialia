#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public synchronous Python API for socialia (§6 MCP-parity surface).

Each function here performs the same operation as its same-named MCP
tool (``social_post`` ↔ :func:`social_post`, …) and returns the same
result dict. The implementation delegates to
:mod:`socialia._mcp.handlers` — real, synchronous, dict-returning
functions — so the CLI (``socialia post …``), the MCP tool, and the
Python call below all share one code path.

Example:
    $ socialia post twitter Hello --dry-run
    >>> import socialia
    >>> socialia.social_post("twitter", "Hello", dry_run=True)["success"]
    True
"""

from __future__ import annotations

from typing import Any, Literal

__all__ = [
    "social_post",
    "social_delete",
    "social_status",
    "analytics_track",
    "analytics_pageviews",
    "analytics_sources",
    "analytics_realtime",
    "get_usage",
]

_Platform = Literal["twitter", "linkedin", "reddit", "slack", "youtube"]


def social_post(
    platform: _Platform,
    text: str,
    reply_to: str | None = None,
    image: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Post text/image content to a platform. Mirrors MCP ``social_post``.

    Example:
        $ socialia post twitter Hello --dry-run
        >>> import socialia
        >>> socialia.social_post("twitter", "Hello", dry_run=True)["success"]
        True
    """
    from socialia._mcp.handlers import social_post as _impl

    return _impl(platform, text, reply_to, image, dry_run)


def social_delete(platform: _Platform, post_id: str) -> dict[str, Any]:
    """Delete a post by ID. Mirrors MCP ``social_delete``.

    Example:
        $ socialia delete-post twitter 1234567890 --dry-run --yes
        >>> import socialia
        >>> out = socialia.social_delete("twitter", "1234567890")
        >>> sorted(out)
        ['cli_command', 'error', 'success']
    """
    from socialia._mcp.handlers import social_delete as _impl

    return _impl(platform, post_id)


def social_status(platform: _Platform) -> dict[str, Any]:
    """Check auth status for a platform. Mirrors MCP ``social_status``.

    Example:
        $ socialia show-status --json
        >>> import socialia
        >>> "cli_command" in socialia.social_status("twitter")
        True
    """
    from socialia._mcp.handlers import social_status as _impl

    return _impl(platform)


def analytics_track(event_name: str, params: dict | None = None) -> dict[str, Any]:
    """Track a custom GA event. Mirrors MCP ``social_analytics_track``.

    The MCP tool is named ``social_analytics_track`` (``<verb>_<api>``
    form); §6 accepts that as covering this API.

    Example:
        $ socialia analytics track signup
        >>> import socialia
        >>> "cli_command" in socialia.analytics_track("signup")
        True
    """
    from socialia._mcp.handlers import analytics_track as _impl

    return _impl(event_name, params)


def analytics_pageviews(
    start_date: str = "7daysAgo",
    end_date: str = "today",
    path: str | None = None,
) -> dict[str, Any]:
    """Get page-view metrics. Mirrors MCP ``social_analytics_pageviews``.

    Example:
        $ socialia analytics show-pageviews
        >>> import socialia
        >>> "cli_command" in socialia.analytics_pageviews()
        True
    """
    from socialia._mcp.handlers import analytics_pageviews as _impl

    return _impl(start_date, end_date, path)


def analytics_sources(
    start_date: str = "7daysAgo",
    end_date: str = "today",
) -> dict[str, Any]:
    """Get traffic sources. Mirrors MCP ``social_analytics_sources``.

    Example:
        $ socialia analytics show-sources
        >>> import socialia
        >>> "cli_command" in socialia.analytics_sources()
        True
    """
    from socialia._mcp.handlers import analytics_sources as _impl

    return _impl(start_date, end_date)


def analytics_realtime() -> dict[str, Any]:
    """Get realtime active users. Mirrors MCP ``social_analytics_realtime``.

    Example:
        $ socialia analytics show-realtime
        >>> import socialia
        >>> "cli_command" in socialia.analytics_realtime()
        True
    """
    from socialia._mcp.handlers import analytics_realtime as _impl

    return _impl()


def get_usage() -> str:
    """Return the platform content-strategies guide. Mirrors MCP ``get_usage``.

    Example:
        >>> import socialia
        >>> "Twitter" in socialia.get_usage()
        True
    """
    from socialia._server import MCP_INSTRUCTIONS

    return MCP_INSTRUCTIONS


# EOF
