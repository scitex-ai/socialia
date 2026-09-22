#!/usr/bin/env python3
"""
Example 05: Feed, Mentions, and Replies

Demonstrates:
- Fetching recent posts from your account
- Getting mentions (notifications)
- Getting replies to your posts (Twitter)
- Displaying detailed output

Usage:
    python 05_feed_and_replies.py           # Show feed
    python 05_feed_and_replies.py --mentions  # Show mentions
    python 05_feed_and_replies.py --replies   # Show replies (Twitter only)

Environment:
    SOCIALIA_X_CONSUMER_KEY
    SOCIALIA_X_CONSUMER_KEY_SECRET
    SOCIALIA_X_ACCESSTOKEN
    SOCIALIA_X_ACCESSTOKEN_SECRET
"""

import argparse
import scitex as stx

from socialia import Twitter


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    parser = argparse.ArgumentParser(description="Fetch feed, mentions, and replies")
    parser.add_argument("--mentions", action="store_true", help="Show mentions")
    parser.add_argument("--replies", action="store_true", help="Show replies (Twitter)")
    parser.add_argument("-l", "--limit", type=int, default=5, help="Number of posts")
    args = parser.parse_args()

    # Create client
    twitter = Twitter()

    # Check credentials
    if not twitter.validate_credentials():
        logger.error("ERROR: Twitter credentials not configured")
        logger.info("Set environment variables:")
        logger.info("  SOCIALIA_X_CONSUMER_KEY")
        logger.info("  SOCIALIA_X_CONSUMER_KEY_SECRET")
        logger.info("  SOCIALIA_X_ACCESSTOKEN")
        logger.info("  SOCIALIA_X_ACCESSTOKEN_SECRET")
        return 1

    # Get user info
    me = twitter.me()
    if me["success"]:
        logger.info(f"Logged in as: @{me['username']} ({me['name']})")
        logger.info("")

    if args.replies:
        # Get replies to your posts
        logger.info("=== Replies to Your Posts ===")
        result = twitter.replies(limit=args.limit)
    elif args.mentions:
        # Get mentions
        logger.info("=== Mentions ===")
        result = twitter.mentions(limit=args.limit)
    else:
        # Get recent feed
        logger.info("=== Recent Posts ===")
        result = twitter.feed(limit=args.limit)

    if result["success"]:
        posts = result.get("posts", result.get("tweets", []))
        if not posts:
            logger.info("No posts found.")
            return 0

        for i, post in enumerate(posts, 1):
            text = post.get("text", "")[:100]
            created = post.get("created_at", "")[:19]
            url = post.get("url", "")
            author = post.get("author_username", "")

            logger.info(f"{i}. {text}{'...' if len(post.get('text', '')) > 100 else ''}")
            if author:
                logger.info(f"   by @{author}")
            if created:
                logger.info(f"   {created}")
            if url:
                logger.info(f"   {url}")
            logger.info("")

        logger.info(f"Total: {len(posts)} posts")
        return 0
    else:
        logger.error(f"ERROR: {result['error']}")
        return 1


if __name__ == "__main__":
    main()
