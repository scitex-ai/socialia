#!/usr/bin/env python3
"""CLI commands for Twitter growth - discover and follow users."""

import json
import sys

from ..twitter import Twitter
import scitex_logging as slogging
log = slogging.getLogger(__name__)


def cmd_grow(args, output_json: bool = False) -> int:
    """Handle grow command - discover and follow users."""
    if args.platform != "twitter":
        log.error(f"Error: grow command only supports twitter (got: {args.platform})")
        return 1

    client = Twitter()

    if args.grow_command == "discover":
        result = client.discover_users(
            args.query,
            limit=args.limit,
            min_followers=args.min_followers,
        )
        if output_json:
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
        elif result["success"]:
            log.info(f"Found {result['count']} users for: {args.query}\n")
            for user in result.get("users", []):
                log.info(f"@{user['username']} ({user['followers']} followers)")
                if user.get("description"):
                    desc = user["description"][:80]
                    log.info(f"  {desc}{'...' if len(user.get('description', '')) > 80 else ''}")
                log.info("")
        else:
            log.error(f"Error: {result['error']}")
            return 1

    elif args.grow_command == "follow":
        # Handle scheduled follow
        schedule_time = getattr(args, "schedule", None)
        repeat_interval = getattr(args, "repeat", None)

        if schedule_time:
            from ..scheduler import schedule_grow

            result = schedule_grow(
                platform=args.platform,
                query=args.query,
                schedule_time=schedule_time,
                limit=args.limit,
                min_followers=args.min_followers,
                repeat_interval=repeat_interval,
            )
            if output_json:
                sys.stdout.write(json.dumps(result, indent=2) + "\n")
            elif result["success"]:
                log.info(f"Scheduled grow job for {result['scheduled_for']}")
                log.info(f"  Query: {args.query}")
                log.info(f"  Limit: {args.limit} users")
                log.info(f"  Job ID: {result['job_id']}")
                if repeat_interval:
                    log.info(f"  Repeats: every {repeat_interval}")
                log.info("\nRun 'socialia schedule daemon' to start the scheduler")
            else:
                log.error(f"Error: {result['error']}")
                return 1
            return 0

        # Immediate follow
        result = client.grow(
            args.query,
            limit=args.limit,
            min_followers=args.min_followers,
            dry_run=args.dry_run,
        )
        if output_json:
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
        elif result["success"]:
            if result["dry_run"]:
                sys.stdout.write(f"=== DRY RUN === Would follow {result['discovered_count']} users:\n" + "\n")
                for user in result.get("discovered", []):
                    sys.stdout.write(f"  @{user['username']} ({user['followers']} followers)" + "\n")
                sys.stdout.write("\nRun without --dry-run to actually follow." + "\n")
            else:
                log.info(f"Followed {result['followed_count']} users:")
                for user in result.get("followed", []):
                    log.info(f"  @{user['username']}")
                if result.get("rate_limited"):
                    log.info("\n[Rate limited] Wait ~15 min before following more.")
                if result.get("skipped"):
                    log.info(f"\nSkipped {len(result['skipped'])}:")
                    for user in result["skipped"][:3]:  # Show first 3 only
                        log.info(f"  @{user['username']}: {user.get('error')}")
                    if len(result["skipped"]) > 3:
                        log.info(f"  ... and {len(result['skipped']) - 3} more")
        else:
            log.error(f"Error: {result['error']}")
            return 1

    elif args.grow_command == "user":
        result = client.get_user(args.username)
        if output_json:
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
        elif result["success"]:
            log.info(f"@{result['username']} ({result['name']})")
            log.info(f"  Followers: {result['followers']}")
            log.info(f"  Following: {result['following']}")
            log.info(f"  Tweets: {result['tweets']}")
            if result.get("description"):
                log.info(f"  Bio: {result['description']}")
        else:
            log.error(f"Error: {result['error']}")
            return 1

    elif args.grow_command == "follow-user":
        if args.dry_run:
            sys.stdout.write(f"=== DRY RUN === Would follow @{args.username}" + "\n")
            return 0
        result = client.follow_by_username(args.username)
        if output_json:
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
        elif result["success"]:
            user = result.get("user", {})
            log.info(f"Followed @{user.get('username', args.username)}")
        else:
            log.error(f"Error: {result['error']}")
            return 1

    elif args.grow_command == "search":
        result = client.search_tweets(args.query, limit=args.limit)
        if output_json:
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
        elif result["success"]:
            log.info(f"Found {result['count']} tweets for: {args.query}\n")
            for tweet in result.get("tweets", []):
                log.info(f"@{tweet['author_username']}:")
                text = tweet["text"][:200]
                log.info(f"  {text}{'...' if len(tweet['text']) > 200 else ''}")
                log.info(f"  Likes: {tweet['likes']} | RTs: {tweet['retweets']}")
                log.info(f"  {tweet['url']}\n")
        else:
            log.error(f"Error: {result['error']}")
            return 1

    elif args.grow_command == "auto":
        from ..scheduler import schedule_grow

        queries = args.queries
        interval = args.interval
        limit = args.limit
        min_followers = args.min_followers

        # Schedule jobs with staggered start times
        scheduled = []
        for i, query in enumerate(queries):
            # Stagger start: first one in 1 min, then interval apart
            if i == 0:
                start_time = "+1m"
            else:
                # Parse interval to get minutes/hours, multiply by index
                start_time = f"+{i}h" if "h" in interval else f"+{i * 30}m"

            result = schedule_grow(
                platform=args.platform,
                query=query,
                schedule_time=start_time,
                limit=limit,
                min_followers=min_followers,
                repeat_interval=interval,
            )
            if result["success"]:
                scheduled.append({"query": query, "job_id": result["job_id"]})

        if output_json:
            sys.stdout.write(json.dumps({"success": True, "scheduled": scheduled}, indent=2) + "\n")
        else:
            log.info(f"Scheduled {len(scheduled)} recurring grow jobs:\n")
            for s in scheduled:
                log.info(f'  [{s["job_id"]}] "{s["query"]}"')
            log.info(f"\nInterval: {interval}")
            log.info(f"Limit: {limit} users per job")
            log.info("\nRun 'socialia schedule daemon' to start")

    else:
        log.error("Error: Specify grow subcommand (discover, follow, user, follow-user, search, auto)")
        return 1

    return 0


def add_grow_parser(subparsers):
    """Add grow command parser."""
    grow_parser = subparsers.add_parser(
        "grow",
        help="Discover and follow users (Twitter)",
        description="Find relevant users and grow your following",
    )
    grow_parser.add_argument(
        "platform",
        choices=["twitter"],
        help="Platform (only twitter supported)",
    )
    grow_sub = grow_parser.add_subparsers(dest="grow_command", help="Growth operations")

    # discover subcommand
    discover_parser = grow_sub.add_parser(
        "discover",
        help="Find users by search query",
        description="Search tweets and extract unique users",
    )
    discover_parser.add_argument(
        "query", help="Search query (e.g., 'scientific python')"
    )
    discover_parser.add_argument(
        "-l", "--limit", type=int, default=20, help="Max users to find (default: 20)"
    )
    discover_parser.add_argument(
        "--min-followers",
        type=int,
        default=0,
        help="Minimum follower count filter",
    )

    # follow subcommand (batch follow from search)
    follow_parser = grow_sub.add_parser(
        "follow",
        help="Find and follow users by search query",
        description="Search for users and follow them",
    )
    follow_parser.add_argument("query", help="Search query")
    follow_parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Max users to follow (default: 10)"
    )
    follow_parser.add_argument(
        "--min-followers",
        type=int,
        default=0,
        help="Minimum follower count filter",
    )
    follow_parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Show users without following"
    )
    follow_parser.add_argument(
        "-S",
        "--schedule",
        help="Schedule for later (e.g., '+20m', '+1h', '10:00')",
    )
    follow_parser.add_argument(
        "-R",
        "--repeat",
        help="Repeat interval (e.g., '+1h', '+30m') - requires --schedule",
    )

    # auto subcommand (set up recurring growth)
    auto_parser = grow_sub.add_parser(
        "auto",
        help="Set up automatic recurring growth",
        description="Schedule recurring grow jobs with multiple queries",
    )
    auto_parser.add_argument(
        "queries",
        nargs="+",
        help="Search queries to rotate through",
    )
    auto_parser.add_argument(
        "-i",
        "--interval",
        default="+1h",
        help="Interval between jobs (default: +1h)",
    )
    auto_parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Max users per job (default: 10)"
    )
    auto_parser.add_argument(
        "--min-followers",
        type=int,
        default=0,
        help="Minimum follower count filter",
    )

    # user subcommand (lookup single user)
    user_parser = grow_sub.add_parser(
        "user",
        help="Get user info by username",
        description="Look up a user's profile",
    )
    user_parser.add_argument("username", help="Twitter username (with or without @)")

    # follow-user subcommand (follow single user)
    follow_user_parser = grow_sub.add_parser(
        "follow-user",
        help="Follow a single user by username",
        description="Follow a specific user",
    )
    follow_user_parser.add_argument("username", help="Twitter username to follow")
    follow_user_parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Show user without following"
    )

    # search subcommand (search tweets)
    search_parser = grow_sub.add_parser(
        "search",
        help="Search recent tweets",
        description="Search for tweets matching a query",
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Max tweets (default: 10)"
    )

    return grow_parser
