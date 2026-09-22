"""Socialia - Unified social media management: posting, analytics, and insights."""

from __future__ import annotations

# Cheap things only — no `from .X import Y` for heavy submodules (§10:
# `import socialia` must stay under 500ms; Click pays it per Tab press).
try:
    from importlib.metadata import version as _v, PackageNotFoundError
    try:
        __version__ = _v("socialia")
    except PackageNotFoundError:
        __version__ = "0.0.0+local"
    del _v, PackageNotFoundError
except ImportError:  # pragma: no cover — only on ancient Pythons
    __version__ = "0.0.0+local"

# Public-name → source-submodule map. ONE row per public symbol.
_LAZY_ATTRS: dict[str, str] = {
    # Platform clients
    "Twitter": "twitter",
    "LinkedIn": "linkedin",
    "Reddit": "reddit",
    "Slack": "slack",
    "YouTube": "youtube",
    "GoogleAnalytics": "analytics",
    # File management
    "move_to_scheduled": "org_files",
    "move_to_posted": "org_files",
    "ensure_project_dirs": "org_files",
    # MCP/content strategies
    "PLATFORM_STRATEGIES": "_server",
    # Public sync Python API (§6 parity surface — same names as MCP tools).
    # Lives in the `_api/` subpackage (PS-108b: keep the package root
    # grouped); re-exported here flat so `socialia.social_post` works.
    "social_post": "_api",
    "social_delete": "_api",
    "social_status": "_api",
    "analytics_track": "_api",
    "analytics_pageviews": "_api",
    "analytics_sources": "_api",
    "analytics_realtime": "_api",
    "get_usage": "_api",
}


def __getattr__(name: str):
    """PEP 562 lazy-loader: import on first access, cache, return."""
    mod_name = _LAZY_ATTRS.get(name)
    if mod_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    attr = getattr(import_module(f".{mod_name}", __name__), name)
    globals()[name] = attr  # cache; subsequent access skips this branch
    return attr


def __dir__() -> list[str]:
    return sorted(set(_LAZY_ATTRS) | set(globals()))


__all__ = [
    # Platform clients
    "Twitter",
    "LinkedIn",
    "Reddit",
    "Slack",
    "YouTube",
    "GoogleAnalytics",
    # File management
    "move_to_scheduled",
    "move_to_posted",
    "ensure_project_dirs",
    # MCP/Content strategies
    "PLATFORM_STRATEGIES",
    # Public sync Python API (§6 parity surface)
    "social_post",
    "social_delete",
    "social_status",
    "analytics_track",
    "analytics_pageviews",
    "analytics_sources",
    "analytics_realtime",
    "get_usage",
    # Version
    "__version__",
]
