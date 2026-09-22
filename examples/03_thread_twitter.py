#!/usr/bin/env python3
"""
Example 03: Post a Twitter Thread

Demonstrates:
- Thread posting (multiple connected tweets)
- Handling partial failures
- Thread content from file

Usage:
    python 03_thread_twitter.py --dry-run   # Preview without posting
    python 03_thread_twitter.py             # Real post (requires credentials)

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
    parser = argparse.ArgumentParser(description="Post a Twitter thread")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without posting"
    )
    args = parser.parse_args()

    # Create client
    twitter = Twitter()

    # Check credentials
    if not twitter.validate_credentials():
        logger.error("ERROR: Twitter credentials not configured")
        return 1

    # Thread content
    tweets = [
        "1/3 Thread about Socialia - a unified social media management tool",
        "2/3 Features:\n- Multi-platform posting (Twitter, LinkedIn)\n- Thread support\n- CLI and Python API\n- MCP server for AI integration",
        "3/3 Built for researchers and developers who need programmatic social media access.\n\nGitHub: https://github.com/ywatanabe1989/socialia",
    ]

    if args.dry_run:
        logger.info("=== DRY RUN (Thread) ===")
        logger.info("Platform: Twitter")
        logger.info(f"Posts: {len(tweets)}")
        for i, tweet in enumerate(tweets, 1):
            logger.info(f"\n--- Tweet {i} ({len(tweet)} chars) ---")
            logger.info(tweet)
        return 0

    # Post thread
    result = twitter.post_thread(tweets)

    if result["success"]:
        logger.info(f"Thread posted! ({len(result['ids'])} tweets)")
        for url in result["urls"]:
            logger.info(f"  {url}")
        return 0
    else:
        logger.error(f"ERROR: {result['error']}")
        if "partial_ids" in result:
            logger.info(f"Partial success: {len(result['partial_ids'])} tweets posted")
        return 1


if __name__ == "__main__":
    main()
