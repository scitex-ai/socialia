#!/usr/bin/env python3
"""
Example 01: Post to Twitter/X

Demonstrates:
- Basic posting via Python API
- Credential validation
- Dry-run mode for testing

Usage:
    python 01_post_twitter.py --dry-run   # Preview without posting
    python 01_post_twitter.py             # Real post (requires credentials)

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
    parser = argparse.ArgumentParser(description="Post to Twitter/X")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without posting"
    )
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

    # Content to post
    text = "Hello from Socialia! Testing the Python API."

    if args.dry_run:
        logger.info("=== DRY RUN ===")
        logger.info("Platform: Twitter")
        logger.info(f"Text ({len(text)} chars): {text}")
        logger.info("Credentials: Valid")
        return 0

    # Post
    result = twitter.post(text)

    if result["success"]:
        logger.info("Posted successfully!")
        logger.info(f"ID: {result['id']}")
        logger.info(f"URL: {result['url']}")
        return 0
    else:
        logger.error(f"ERROR: {result['error']}")
        return 1


if __name__ == "__main__":
    main()
