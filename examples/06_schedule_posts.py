#!/usr/bin/env python3
"""
Example 06: Schedule Posts

Demonstrates:
- Scheduling posts for later
- Listing pending scheduled posts
- Cancelling scheduled posts
- Running the scheduler daemon

Usage:
    python 06_schedule_posts.py               # Demo schedule workflow
    python 06_schedule_posts.py --list        # List scheduled posts
    python 06_schedule_posts.py --cancel ID   # Cancel a scheduled post

CLI Equivalents:
    socialia post twitter "Hello!" --schedule "10:00"
    socialia post twitter "Hello!" --schedule "+1h"
    socialia post twitter "Hello!" --schedule "2026-01-25 14:30"
    socialia schedule list
    socialia schedule cancel <job_id>
    socialia schedule daemon --interval 60
"""

import argparse
import scitex as stx
from datetime import datetime, timedelta

from socialia.scheduler import (
    schedule_post,
    list_scheduled,
    cancel_scheduled,
)


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    parser = argparse.ArgumentParser(description="Schedule posts demo")
    parser.add_argument("--list", action="store_true", help="List scheduled posts")
    parser.add_argument("--cancel", metavar="ID", help="Cancel a scheduled post")
    parser.add_argument(
        "--demo", action="store_true", help="Demo scheduling (creates test job)"
    )
    args = parser.parse_args()

    if args.cancel:
        # Cancel a scheduled post
        result = cancel_scheduled(args.cancel)
        if result["success"]:
            logger.info(f"Cancelled: {args.cancel}")
        else:
            logger.error(f"ERROR: {result['error']}")
        return 0 if result["success"] else 1

    if args.list:
        # List scheduled posts
        jobs = list_scheduled()
        if not jobs:
            logger.info("No scheduled posts pending.")
            return 0

        logger.info("=== Scheduled Posts ===")
        for job in jobs:
            logger.info(f"\nID: {job['id']}")
            logger.info(f"  Platform: {job['platform']}")
            logger.info(f"  Scheduled: {job['scheduled_for']}")
            logger.info(f"  Text: {job['text'][:50]}{'...' if len(job['text']) > 50 else ''}")
            if job.get("kwargs"):
                for k, v in job["kwargs"].items():
                    if v:
                        logger.info(f"  {k}: {v}")

        logger.info(f"\nTotal: {len(jobs)} pending")
        return 0

    if args.demo:
        # Demo: Schedule a post for 5 minutes from now
        future_time = datetime.now() + timedelta(minutes=5)
        time_str = future_time.strftime("%Y-%m-%d %H:%M")

        logger.info("=== Schedule Demo ===")
        logger.info(f"Scheduling test post for: {time_str}")
        logger.info("")

        result = schedule_post(
            platform="twitter",
            text="[TEST] Scheduled post from Socialia example script.",
            schedule_time=time_str,
        )

        if result["success"]:
            logger.info("Scheduled successfully!")
            logger.info(f"  Job ID: {result['job_id']}")
            logger.info(f"  Time: {result['scheduled_for']}")
            logger.info("")
            logger.info("To execute scheduled posts, run:")
            logger.info("  socialia schedule daemon")
            logger.info("")
            logger.info("To cancel this test post:")
            logger.info(f"  socialia schedule cancel {result['job_id']}")
            logger.info("  # or")
            logger.info(f"  python 06_schedule_posts.py --cancel {result['job_id']}")
            return 0
        else:
            logger.error(f"ERROR: {result['error']}")
            return 1

    # Default: Show help
    logger.info("Schedule Posts Example")
    logger.info("======================")
    logger.info("")
    logger.info("Available time formats:")
    logger.info('  "10:00"              - Today at 10:00 (or tomorrow if passed)')
    logger.info('  "2026-01-25 14:30"   - Specific date and time')
    logger.info('  "+1h"                - 1 hour from now')
    logger.info('  "+30m"               - 30 minutes from now')
    logger.info("")
    logger.info("Commands:")
    logger.info("  --demo     Create a test scheduled post")
    logger.info("  --list     List all pending scheduled posts")
    logger.info("  --cancel   Cancel a scheduled post by ID")
    logger.info("")
    logger.info("CLI usage:")
    logger.info('  socialia post twitter "Hello!" --schedule "+1h"')
    logger.info("  socialia schedule list")
    logger.info("  socialia schedule daemon  # Run to execute scheduled posts")

    return 0


if __name__ == "__main__":
    main()
