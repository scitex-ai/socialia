"""Public sync Python API subpackage (§6 MCP-parity surface).

Import via the flat top-level names — ``socialia.social_post``, … —
which stay stable regardless of this internal layout::

    import socialia
    socialia.social_post("twitter", "Hello", dry_run=True)
"""

from __future__ import annotations

from .parity import (
    analytics_pageviews,
    analytics_realtime,
    analytics_sources,
    analytics_track,
    get_usage,
    social_delete,
    social_post,
    social_status,
)

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
