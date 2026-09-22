#!/usr/bin/env python3
"""
Example 02: Post to LinkedIn

Demonstrates:
- LinkedIn posting via Python API
- Token validation
- Different visibility options

Usage:
    python 02_post_linkedin.py --dry-run   # Preview without posting
    python 02_post_linkedin.py             # Real post (requires token)

Environment:
    SOCIALIA_LINKEDIN_ACCESS_TOKEN
"""

import argparse
import scitex as stx

from socialia import LinkedIn


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    parser = argparse.ArgumentParser(description="Post to LinkedIn")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without posting"
    )
    parser.add_argument(
        "--visibility",
        choices=["PUBLIC", "CONNECTIONS"],
        default="PUBLIC",
        help="Post visibility",
    )
    args = parser.parse_args()

    # Create client
    linkedin = LinkedIn()

    # Check credentials
    if not linkedin.validate_credentials():
        logger.error("ERROR: LinkedIn credentials not configured")
        logger.info("Set environment variable:")
        logger.info("  SOCIALIA_LINKEDIN_ACCESS_TOKEN")
        return 1

    # Content to post
    text = """Professional update from Socialia!

Testing the LinkedIn API integration. This tool helps automate social media management for research and development teams.

#automation #python #api"""

    if args.dry_run:
        logger.info("=== DRY RUN ===")
        logger.info("Platform: LinkedIn")
        logger.info(f"Visibility: {args.visibility}")
        logger.info(f"Text ({len(text)} chars):")
        logger.info(text[:200] + "..." if len(text) > 200 else text)
        logger.info("Credentials: Valid")
        return 0

    # Post
    result = linkedin.post(text, visibility=args.visibility)

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
