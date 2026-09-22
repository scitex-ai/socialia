#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-01-27
# File: src/socialia/_mcp/tools/social.py

"""Social media MCP tools."""

from __future__ import annotations

from typing import Literal, Optional

try:
    from fastmcp import FastMCP
except ImportError as exc:
    raise ImportError(
        "socialia[mcp] is required for MCP tools: pip install socialia[mcp]"
    ) from exc

from ..handlers import social_delete as _social_delete
from ..handlers import social_post as _social_post
from ..handlers import social_status as _social_status


def register_tools(mcp: FastMCP) -> None:
    """Register social media tools."""

    @mcp.tool()
    def social_post(
        platform: Literal["twitter", "linkedin", "reddit", "slack", "youtube"],
        text: str,
        reply_to: Optional[str] = None,
        image: Optional[str] = None,
        dry_run: bool = False,
    ) -> dict:
        """Post text/image content to Twitter, LinkedIn, Reddit, Slack, or YouTube via a unified call — drop-in replacement for tweepy.Client.create_tweet, LinkedIn UGC API, PRAW submission, slack-sdk chat.postMessage, and YouTube Data API insert. Use whenever the user asks to "tweet X", "post this to LinkedIn", "submit to r/subreddit", "send a Slack message", "upload a YouTube short/video", or mentions social-media posting. CLI: socialia post <platform> <text>

        PLATFORM STRATEGIES:
        - twitter: 280 chars. Hook first, not announcements. 1-2 hashtags at end.
          Supports image attachment via `image` parameter (path to jpg/png/gif/webp).
        - linkedin: 3000 chars. First 2 lines critical. Short paragraphs. End with question.
        - reddit: Title is key. Value first, self-promo last. Check subreddit rules.
        - slack: Use channel mentions @here/@channel sparingly. Code blocks for technical content.
        - youtube: Keyword-rich title <60 chars. First 2 description lines shown in search.
        """
        return _social_post(platform, text, reply_to, image, dry_run)

    @mcp.tool()
    def social_delete(
        platform: Literal["twitter", "linkedin", "reddit", "slack", "youtube"],
        post_id: str,
    ) -> dict:
        """Use when the user asks to delete, retract, remove, or take down a tweet, LinkedIn post, Reddit post/comment, Slack message, or YouTube video by ID — drop-in replacement for platform-specific delete APIs (tweepy delete_tweet, LinkedIn UGC delete, PRAW .delete(), YouTube Data API videos.delete). CLI: socialia delete <platform> <post_id>"""
        return _social_delete(platform, post_id)

    @mcp.tool()
    def social_status(
        platform: Literal["twitter", "linkedin", "reddit", "slack", "youtube"],
    ) -> dict:
        """Use when the user asks to check if Twitter/LinkedIn/Reddit/Slack/YouTube OAuth credentials are configured and the token is valid before posting, or to verify "am I logged in" / "is auth working" — drop-in replacement for manually calling each platform's /me or verify_credentials endpoint. CLI: socialia status <platform>"""
        return _social_status(platform)


# EOF
