#!/usr/bin/env python3
"""Feed and check CLI command handlers for socialia."""

import json
import sys

from .. import __version__
from ..twitter import Twitter
from ..linkedin import LinkedIn
from ..reddit import Reddit
from ..slack import Slack
from ..youtube import YouTube
import scitex_logging as slogging
log = slogging.getLogger(__name__)


def get_client(platform: str):
    """Get platform client instance."""
    if platform == "twitter":
        return Twitter()
    elif platform == "linkedin":
        return LinkedIn()
    elif platform == "reddit":
        return Reddit()
    elif platform == "slack":
        return Slack()
    elif platform == "youtube":
        return YouTube()
    else:
        raise ValueError(f"Unsupported platform: {platform}")


def cmd_feed(args, output_json: bool = False) -> int:
    """Handle feed command - get recent posts from platforms."""
    platforms = []
    if hasattr(args, "platform") and args.platform:
        platforms = [args.platform]
    else:
        # Check all configured platforms
        platforms = ["twitter", "linkedin", "reddit", "slack", "youtube"]

    limit = getattr(args, "limit", 5)
    mentions_only = getattr(args, "mentions", False)
    replies_only = getattr(args, "replies", False)
    detail = getattr(args, "detail", False)
    results = {}

    for platform in platforms:
        client = get_client(platform)
        validate_read = getattr(client, "validate_read_credentials", None)
        can_read = (
            validate_read()
            if callable(validate_read)
            else client.validate_credentials()
        )
        if not can_read:
            # Skip unconfigured platforms silently (unless specifically requested)
            if hasattr(args, "platform") and args.platform:
                results[platform] = {"success": False, "error": "Not configured"}
            continue

        if replies_only:
            if hasattr(client, "replies"):
                result = client.replies(limit=limit)
            else:
                result = {"success": False, "error": "Replies not supported"}
        elif mentions_only:
            result = client.mentions(limit=limit)
        else:
            result = client.feed(limit=limit)
        results[platform] = result

    if output_json:
        sys.stdout.write(json.dumps(results, indent=2) + "\n")
    else:
        for platform, result in results.items():
            log.info(f"\n{platform.upper()}")
            log.info("─" * 40)
            if not result.get("success"):
                log.info(f"  ⚠️  {result.get('error', 'Unknown error')}")
                continue

            # Get posts/tweets/mentions/replies
            items = (
                result.get("posts")
                or result.get("tweets")
                or result.get("mentions")
                or result.get("replies")
                or []
            )
            if not items:
                log.info("  No recent posts")
                continue

            for i, item in enumerate(items[:limit]):
                full_text = item.get("text", item.get("title", ""))
                if detail:
                    text = full_text.replace("\n", "\n    ")
                else:
                    text = full_text[:80].replace("\n", " ")
                    if len(full_text) > 77:
                        text = text[:77] + "..."
                likes = item.get("likes", item.get("score", ""))
                retweets = item.get("retweets", "")
                created = (
                    item.get("created_at", "")[:10] if item.get("created_at") else ""
                )
                # Show author for replies/mentions
                author = item.get("author_username", "")
                if author:
                    log.info(f"  • @{author}: {text}")
                else:
                    log.info(f"  • {text}")
                metrics = []
                if created:
                    metrics.append(created)
                if likes:
                    metrics.append(f"❤️ {likes}")
                if retweets:
                    metrics.append(f"🔁 {retweets}")
                if metrics:
                    log.info(f"    {' · '.join(metrics)}")
                if detail:
                    url = item.get("url", "")
                    if url:
                        log.info(f"    🔗 {url}")
                if i < len(items[:limit]) - 1:
                    log.info("")  # Blank line between posts

    return 0


def cmd_check(args, output_json: bool = False) -> int:
    """Handle check command - verify connections to all platforms."""
    platforms = []
    if hasattr(args, "platform") and args.platform:
        platforms = [args.platform]
    else:
        platforms = ["twitter", "linkedin", "reddit", "youtube"]

    results = {}
    for platform in platforms:
        client = get_client(platform)
        results[platform] = client.check()

    if output_json:
        sys.stdout.write(json.dumps(results, indent=2) + "\n")
    else:
        log.info(f"Socialia v{__version__} - Connection Check")
        log.info("=" * 50)
        for platform, result in results.items():
            status = result.get("status", "unknown")
            if status == "connected":
                user = result.get("user", {})
                name = user.get("name") or user.get("username") or user.get("title", "")
                log.info(f"\n✅ {platform.upper()}: Connected")
                if name:
                    log.info(f"   User: {name}")
                url = user.get("url", "")
                if url:
                    log.info(f"   URL: {url}")
            elif status == "not_configured":
                log.info(f"\n⚪ {platform.upper()}: Not configured")
            else:
                error = result.get("error", "Unknown error")
                log.info(f"\n❌ {platform.upper()}: Error")
                log.info(f"   {error}")

    return 0


def cmd_me(args, output_json: bool = False) -> int:
    """Handle me command - get user info for a platform."""
    client = get_client(args.platform)
    result = client.me()

    if output_json:
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
    elif result.get("success"):
        log.info(f"{args.platform.upper()} User Info")
        log.info("─" * 30)
        for key, value in result.items():
            if key != "success":
                log.info(f"  {key}: {value}")
    else:
        log.error(f"Error: {result.get('error')}")
        return 1

    return 0
