#!/usr/bin/env python3
"""
Example 04: Google Analytics Integration

Demonstrates:
- Tracking custom events
- Querying page views
- Getting traffic sources

Usage:
    python 04_analytics.py

Environment:
    SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID  - Required for tracking
    SOCIALIA_GOOGLE_ANALYTICS_API_SECRET      - Required for tracking
    SOCIALIA_GOOGLE_ANALYTICS_PROPERTY_ID     - Optional, for Data API queries
"""

import scitex as stx
from socialia import GoogleAnalytics


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    ga = GoogleAnalytics()

    logger.info("=== Google Analytics Demo ===\n")

    # 1. Track a custom event
    logger.info("1. Tracking custom event...")
    result = ga.track_event(
        "example_demo",
        params={
            "demo_type": "analytics",
            "source": "socialia_examples",
        },
    )
    if result["success"]:
        logger.info("   Event tracked successfully")
    else:
        logger.info(f"   Event tracking failed: {result.get('error', 'Unknown')}")

    # 2. Get page views (requires Data API setup)
    logger.info("\n2. Querying page views...")
    result = ga.get_page_views(start_date="7daysAgo", end_date="today")
    if result["success"]:
        logger.info(f"   Date range: {result['date_range']}")
        pages = result.get("pages", [])
        if pages:
            logger.info("   Top pages:")
            for page in pages[:5]:
                logger.info(f"     {page['path']}: {page['page_views']} views")
        else:
            logger.info("   No page data available")
    else:
        logger.info(f"   Query failed: {result.get('error', 'Unknown')}")

    # 3. Get traffic sources
    logger.info("\n3. Querying traffic sources...")
    result = ga.get_traffic_sources(start_date="7daysAgo", end_date="today")
    if result["success"]:
        sources = result.get("sources", [])
        if sources:
            logger.info("   Top sources:")
            for src in sources[:5]:
                logger.info(f"     {src['source']}/{src['medium']}: {src['sessions']} sessions")
        else:
            logger.info("   No source data available")
    else:
        logger.info(f"   Query failed: {result.get('error', 'Unknown')}")

    logger.info("\n=== Demo Complete ===")
    return 0


if __name__ == "__main__":
    main()
