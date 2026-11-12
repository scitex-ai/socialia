"""Socialia - Unified social media management: posting, analytics, and insights."""

from __future__ import annotations

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _v

    try:
        __version__ = _v("socialia")
    except PackageNotFoundError:
        __version__ = "0.0.0+local"
    del _v, PackageNotFoundError
except ImportError:  # pragma: no cover — only on ancient Pythons
    __version__ = "0.0.0+local"
# Public names retain their providers while deferring optional startup work.
_LAZY_ATTRS: dict[str, str] = {
    "Twitter": "twitter",
    "LinkedIn": "linkedin",
    "Reddit": "reddit",
    "Slack": "slack",
    "YouTube": "youtube",
    "GoogleAnalytics": "analytics",
    "move_to_scheduled": "org_files",
    "move_to_posted": "org_files",
    "ensure_project_dirs": "org_files",
    "PLATFORM_STRATEGIES": "_server",
}


def __getattr__(name: str):
    """Load and cache a public provider on first attribute access."""
    module_name = _LAZY_ATTRS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    try:
        value = getattr(import_module(f".{module_name}", __name__), name)
    except ImportError:
        if name != "PLATFORM_STRATEGIES":
            raise
        value = {}  # Preserve the legacy optional-MCP fallback.
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose public names without loading their providers."""
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
    # Version
    "__version__",
]
