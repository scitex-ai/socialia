#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-01-27
# File: src/socialia/_mcp/tools/analytics.py

"""Analytics MCP tools for Google Analytics."""

from __future__ import annotations

from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError as exc:
    raise ImportError(
        "socialia[mcp] is required for MCP tools: pip install socialia[mcp]"
    ) from exc

from ..handlers import analytics_pageviews as _analytics_pageviews
from ..handlers import analytics_realtime as _analytics_realtime
from ..handlers import analytics_sources as _analytics_sources
from ..handlers import analytics_track as _analytics_track


def register_tools(mcp: FastMCP) -> None:
    """Register analytics tools."""

    @mcp.tool()
    def social_analytics_track(
        event_name: str,
        params: Optional[dict] = None,
    ) -> dict:
        """Use when the user asks to track, log, or send a custom event (signup, click, conversion, download) to Google Analytics — drop-in replacement for raw GA4 Measurement Protocol POST calls to /mp/collect. CLI: socialia analytics track <event_name>"""
        return _analytics_track(event_name, params)

    @mcp.tool()
    def social_analytics_pageviews(
        start_date: str = "7daysAgo",
        end_date: str = "today",
        path: Optional[str] = None,
    ) -> dict:
        """Use when the user asks for page view metrics, visit counts, or traffic to specific pages/paths from Google Analytics — drop-in replacement for google-analytics-data (BetaAnalyticsDataClient.run_report) queries on screenPageViews metrics. CLI: socialia analytics pageviews"""
        return _analytics_pageviews(start_date, end_date, path)

    @mcp.tool()
    def social_analytics_sources(
        start_date: str = "7daysAgo",
        end_date: str = "today",
    ) -> dict:
        """Use when the user asks where visitors are coming from — traffic sources, referrers, campaigns, or acquisition channels (organic/direct/social/referral) — drop-in replacement for google-analytics-data SDK run_report calls on sessionSource/sessionMedium dimensions. CLI: socialia analytics sources"""
        return _analytics_sources(start_date, end_date)

    @mcp.tool()
    def social_analytics_realtime() -> dict:
        """Use when the user asks how many users are on the site right now, for live/realtime/current active visitor counts — drop-in replacement for google-analytics-data SDK run_realtime_report calls on activeUsers. CLI: socialia analytics realtime"""
        return _analytics_realtime()


# EOF
