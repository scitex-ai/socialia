#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-01-27
# File: src/socialia/_mcp/handlers.py

"""MCP tool handlers - shared logic for CLI delegation."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


def run_cli(*args: str) -> dict[str, Any]:
    """
    Run socialia CLI command and return result.

    This ensures all MCP operations are reproducible via CLI.
    """
    cmd = [sys.executable, "-m", "socialia.cli", "--json", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)

    cli_command = f"socialia {' '.join(args)}"

    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            data["cli_command"] = cli_command
            return data
        except json.JSONDecodeError:
            return {
                "success": True,
                "output": result.stdout,
                "cli_command": cli_command,
            }
    else:
        return {
            "success": False,
            "error": result.stderr or result.stdout,
            "cli_command": cli_command,
        }


# =============================================================================
# Social Media Handlers
# =============================================================================


def social_post(
    platform: str,
    text: str,
    reply_to: str | None = None,
    image: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Post content to social media."""
    args = ["post", platform, text]
    if reply_to:
        args.extend(["--reply-to", reply_to])
    if image:
        args.extend(["--image", image])
    if dry_run:
        args.append("--dry-run")
    return run_cli(*args)


def social_delete(platform: str, post_id: str) -> dict[str, Any]:
    """Delete a social media post."""
    return run_cli("delete", platform, post_id)


def social_status(platform: str) -> dict[str, Any]:
    """Check authentication status for a platform."""
    return run_cli("status", platform)


def social_feed(platform: str, count: int = 10) -> dict[str, Any]:
    """Get recent posts from feed."""
    return run_cli("feed", platform, "--limit", str(count), "--json")


def social_check(platform: str) -> dict[str, Any]:
    """Check connection status for the requested platform."""
    return run_cli("check-platforms", platform, "--json")


# =============================================================================
# Analytics Handlers
# =============================================================================


def analytics_track(event_name: str, params: dict | None = None) -> dict[str, Any]:
    """Track custom event in Google Analytics."""
    args = ["analytics", "track", event_name]
    if params:
        for key, value in params.items():
            args.extend(["--param", key, str(value)])
    return run_cli(*args)


def analytics_pageviews(
    start_date: str = "7daysAgo",
    end_date: str = "today",
    path: str | None = None,
) -> dict[str, Any]:
    """Get page view metrics from Google Analytics."""
    args = ["analytics", "pageviews"]
    if start_date:
        args.extend(["--start", start_date])
    if end_date:
        args.extend(["--end", end_date])
    if path:
        args.extend(["--path", path])
    return run_cli(*args)


def analytics_sources(
    start_date: str = "7daysAgo",
    end_date: str = "today",
) -> dict[str, Any]:
    """Get traffic sources from Google Analytics."""
    args = ["analytics", "sources"]
    if start_date:
        args.extend(["--start", start_date])
    if end_date:
        args.extend(["--end", end_date])
    return run_cli(*args)


def analytics_realtime() -> dict[str, Any]:
    """Get realtime active users from Google Analytics."""
    return run_cli("analytics", "realtime")


# EOF
