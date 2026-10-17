#!/usr/bin/env python3
"""CLI command handlers for socialia."""

import json
import sys

import click

from .. import __version__
from ..analytics import GoogleAnalytics
from ..linkedin import LinkedIn
from ..reddit import Reddit
from ..slack import Slack
from ..twitter import Twitter
from ..youtube import YouTube


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


def cmd_post(args, output_json: bool = False) -> int:
    """Handle post command."""
    if args.file:
        if not args.file.exists():
            click.echo(f"Error: File not found: {args.file}", err=True)
            return 1
        text = args.file.read_text().strip()
    elif args.text:
        text = args.text
    else:
        click.echo("Error: Provide text or --file", err=True)
        return 1

    if args.dry_run:
        click.echo("=== DRY RUN ===")
        click.echo(f"Platform: {args.platform}")
        if args.platform == "reddit":
            click.echo(f"Subreddit: r/{getattr(args, 'subreddit', 'test')}")
            title = getattr(args, "title", None) or text.split("\n")[0][:100]
            click.echo(f"Title: {title}")
        elif args.platform == "youtube":
            video = getattr(args, "video", None)
            click.echo(f"Video: {video or 'None (community post)'}")
            click.echo(
                f"Title: {getattr(args, 'title', None) or text.split(chr(10))[0][:100]}"
            )
            click.echo(f"Privacy: {getattr(args, 'privacy', 'public')}")
        click.echo(
            f"Text ({len(text)} chars): {text[:100]}{'...' if len(text) > 100 else ''}"
        )
        if getattr(args, "schedule", None):
            click.echo(f"Schedule: {args.schedule}")
        return 0

    # Handle scheduled posts
    if getattr(args, "schedule", None):
        from ..scheduler import schedule_post

        kwargs = {}
        if args.platform == "reddit":
            kwargs["subreddit"] = getattr(args, "subreddit", "test")
            kwargs["title"] = getattr(args, "title", None)
        elif args.platform == "twitter":
            kwargs["reply_to"] = getattr(args, "reply_to", None)
            kwargs["quote_tweet_id"] = getattr(args, "quote", None)

        result = schedule_post(args.platform, text, args.schedule, **kwargs)

        if output_json:
            click.echo(json.dumps(result, indent=2))
        elif result["success"]:
            click.echo(f"📅 Scheduled for {result['scheduled_for']}")
            click.echo(f"   Job ID: {result['job_id']}")
            click.echo("   Run 'socialia schedule list' to view pending posts")
            click.echo("   Run 'socialia schedule daemon' to start the scheduler")
        else:
            click.echo(f"Error: {result['error']}", err=True)
            return 1
        return 0

    client = get_client(args.platform)
    if args.platform == "twitter":
        media_ids = None
        image_path = getattr(args, "image", None)
        if image_path:
            upload_result = client.upload_media(str(image_path))
            if upload_result["success"]:
                media_ids = [upload_result["media_id"]]
            else:
                click.echo(
                    f"Error uploading image: {upload_result['error']}", err=True
                )
                return 1
        result = client.post(
            text,
            reply_to=getattr(args, "reply_to", None),
            quote_tweet_id=getattr(args, "quote", None),
            media_ids=media_ids,
        )
    elif args.platform == "reddit":
        result = client.post(
            text,
            subreddit=getattr(args, "subreddit", "test"),
            title=getattr(args, "title", None),
        )
    elif args.platform == "slack":
        result = client.post(
            text,
            channel=getattr(args, "channel", None),
            thread_ts=getattr(args, "thread_ts", None),
        )
    elif args.platform == "youtube":
        video_path = getattr(args, "video", None)
        tags = getattr(args, "tags", None)
        result = client.post(
            text,
            video_path=str(video_path) if video_path else None,
            title=getattr(args, "title", None),
            tags=tags.split(",") if tags else None,
            privacy_status=getattr(args, "privacy", "public"),
            thumbnail_path=str(getattr(args, "thumbnail", None))
            if getattr(args, "thumbnail", None)
            else None,
        )
    else:
        result = client.post(text)

    if output_json:
        click.echo(json.dumps(result, indent=2))
    elif result["success"]:
        click.echo("Posted successfully!")
        click.echo(f"ID: {result['id']}")
        click.echo(f"URL: {result['url']}")
    else:
        click.echo(f"Error: {result['error']}", err=True)
        return 1

    return 0


def cmd_delete(args, output_json: bool = False) -> int:
    """Handle delete command."""
    client = get_client(args.platform)
    result = client.delete(args.post_id)

    if output_json:
        click.echo(json.dumps(result, indent=2))
    elif result["success"]:
        click.echo(f"Deleted: {args.post_id}")
    else:
        click.echo(f"Error: {result['error']}", err=True)
        return 1

    return 0


def cmd_thread(args, output_json: bool = False) -> int:
    """Handle thread command."""
    if not args.file.exists():
        click.echo(f"Error: File not found: {args.file}", err=True)
        return 1

    content = args.file.read_text()
    tweets = [t.strip() for t in content.split("---") if t.strip()]

    if not tweets:
        click.echo("Error: No content found in file", err=True)
        return 1

    if args.dry_run:
        click.echo("=== DRY RUN (Thread) ===")
        click.echo(f"Platform: {args.platform}")
        click.echo(f"Posts: {len(tweets)}")
        for i, t in enumerate(tweets, 1):
            click.echo(f"\n--- Post {i} ({len(t)} chars) ---")
            click.echo(t[:200] + ("..." if len(t) > 200 else ""))
        return 0

    client = get_client(args.platform)
    result = client.post_thread(tweets)

    if output_json:
        click.echo(json.dumps(result, indent=2))
    elif result["success"]:
        click.echo(f"Thread posted! ({len(result['ids'])} posts)")
        for url in result["urls"]:
            click.echo(f"  {url}")
    else:
        click.echo(f"Error: {result['error']}", err=True)
        return 1

    return 0


def cmd_analytics(args, output_json: bool = False) -> int:
    """Handle analytics command."""
    ga = GoogleAnalytics()

    if args.analytics_command == "track":
        params = {}
        if args.param:
            for key, value in args.param:
                params[key] = value
        result = ga.track_event(args.event_name, params)

    elif args.analytics_command == "realtime":
        result = ga.get_realtime_users()

    elif args.analytics_command == "pageviews":
        result = ga.get_page_views(
            start_date=args.start,
            end_date=args.end,
            page_path=getattr(args, "path", None),
        )

    elif args.analytics_command == "sources":
        result = ga.get_traffic_sources(
            start_date=args.start,
            end_date=args.end,
        )

    else:
        click.echo(
            "Error: Specify analytics subcommand (track, realtime, pageviews, sources)", err=True,
        )
        return 1

    if output_json:
        click.echo(json.dumps(result, indent=2))
    elif result["success"]:
        if args.analytics_command == "track":
            click.echo(f"Event tracked: {args.event_name}")
        elif args.analytics_command == "realtime":
            click.echo(f"Active users: {result.get('active_users', 0)}")
        elif args.analytics_command == "pageviews":
            click.echo(f"Page views ({result['date_range']}):")
            for page in result.get("pages", [])[:10]:
                click.echo(
                    f"  {page['path']}: {page['page_views']} views, {page['users']} users"
                )
        elif args.analytics_command == "sources":
            click.echo(f"Traffic sources ({result['date_range']}):")
            for src in result.get("sources", [])[:10]:
                click.echo(f"  {src['source']}/{src['medium']}: {src['sessions']} sessions")
    else:
        click.echo(f"Error: {result['error']}", err=True)
        return 1

    return 0


def cmd_status(output_json: bool = False) -> int:
    """Show configuration and environment status."""
    from .._branding import get_env, get_env_var_name

    env_vars = {
        "twitter": {
            get_env_var_name("X_CONSUMER_KEY"): get_env("X_CONSUMER_KEY"),
            get_env_var_name("X_CONSUMER_KEY_SECRET"): get_env("X_CONSUMER_KEY_SECRET"),
            get_env_var_name("X_ACCESSTOKEN"): get_env("X_ACCESSTOKEN"),
            get_env_var_name("X_ACCESSTOKEN_SECRET"): get_env("X_ACCESSTOKEN_SECRET"),
        },
        "linkedin": {
            get_env_var_name("LINKEDIN_ACCESS_TOKEN"): get_env("LINKEDIN_ACCESS_TOKEN"),
        },
        "reddit": {
            get_env_var_name("REDDIT_CLIENT_ID"): get_env("REDDIT_CLIENT_ID"),
            get_env_var_name("REDDIT_CLIENT_SECRET"): get_env("REDDIT_CLIENT_SECRET"),
            get_env_var_name("REDDIT_USERNAME"): get_env("REDDIT_USERNAME"),
            get_env_var_name("REDDIT_PASSWORD"): get_env("REDDIT_PASSWORD"),
        },
        "youtube": {
            get_env_var_name("YOUTUBE_CLIENT_SECRETS_FILE"): get_env(
                "YOUTUBE_CLIENT_SECRETS_FILE"
            ),
        },
        "analytics": {
            get_env_var_name("GOOGLE_ANALYTICS_MEASUREMENT_ID"): (
                get_env("GOOGLE_ANALYTICS_MEASUREMENT_ID")
                or get_env("GA_MEASUREMENT_ID")
            ),
            get_env_var_name("GOOGLE_ANALYTICS_API_SECRET"): (
                get_env("GOOGLE_ANALYTICS_API_SECRET") or get_env("GA_API_SECRET")
            ),
            get_env_var_name("GOOGLE_ANALYTICS_PROPERTY_ID"): (
                get_env("GOOGLE_ANALYTICS_PROPERTY_ID") or get_env("GA_PROPERTY_ID")
            ),
        },
    }

    status = {}
    for platform, vars_dict in env_vars.items():
        configured = all(v is not None for v in vars_dict.values())
        partial = any(v is not None for v in vars_dict.values())
        status[platform] = {
            "configured": configured,
            "partial": partial and not configured,
            "vars": {k: "set" if v else "missing" for k, v in vars_dict.items()},
        }

    if output_json:
        click.echo(json.dumps({"version": __version__, "platforms": status}, indent=2))
    else:
        click.echo(f"Socialia v{__version__}")
        click.echo("=" * 40)
        for platform, info in status.items():
            if info["configured"]:
                mark = "[OK]"
            elif info["partial"]:
                mark = "[PARTIAL]"
            else:
                mark = "[NOT SET]"
            click.echo(f"\n{platform.upper():12} {mark}")
            for var, state in info["vars"].items():
                indicator = "+" if state == "set" else "-"
                click.echo(f"  {indicator} {var}")

    return 0


def _get_setup_guide(platform: str) -> str:
    """Get setup guide with branded env var names."""
    from .._branding import get_env_var_name

    guides = {
        "twitter": f"""
TWITTER/X SETUP
===============

1. Go to https://developer.x.com
2. Create app with Read+Write permissions
3. Generate API keys and access tokens

Environment Variables:
  export {get_env_var_name("X_CONSUMER_KEY")}="..."
  export {get_env_var_name("X_CONSUMER_KEY_SECRET")}="..."
  export {get_env_var_name("X_ACCESSTOKEN")}="..."
  export {get_env_var_name("X_ACCESSTOKEN_SECRET")}="..."

Test:
  socialia post twitter "Test" --dry-run
""",
        "linkedin": f"""
LINKEDIN SETUP
==============

1. Go to https://www.linkedin.com/developers/
2. Create app (or use existing one)
3. Go to Products tab, add TWO products:
   - "Share on LinkedIn" (for posting)
   - "Sign In with LinkedIn using OpenID Connect" (for user ID)
4. Go to Auth tab → OAuth 2.0 tools
5. Select BOTH scopes:
   - w_member_social
   - openid
6. Click "Request access token"
7. Authorize and copy the token

Environment Variables:
  export {get_env_var_name("LINKEDIN_ACCESS_TOKEN")}="..."

LIMITATIONS:
  - Posting: ✅ Works with w_member_social scope
  - Feed/mentions: ❌ Requires r_member_social scope (partner-only)
  - LinkedIn restricts feed reading to verified partners
  - "socialia feed linkedin" will return 403 error

Note: Tokens expire after 60 days. Regenerate via OAuth 2.0 tools.

Test:
  socialia post linkedin "Test" --dry-run
""",
        "reddit": f"""
REDDIT SETUP
============

1. Go to https://www.reddit.com/prefs/apps
2. Create 'script' type app

Environment Variables:
  export {get_env_var_name("REDDIT_CLIENT_ID")}="..."
  export {get_env_var_name("REDDIT_CLIENT_SECRET")}="..."
  export {get_env_var_name("REDDIT_USERNAME")}="..."
  export {get_env_var_name("REDDIT_PASSWORD")}="..."

Test:
  socialia post reddit "Test" --subreddit test --dry-run
""",
        "youtube": f"""
YOUTUBE SETUP
=============

1. Go to https://console.cloud.google.com/
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials
4. Download client_secrets.json

Environment Variables:
  export {get_env_var_name("YOUTUBE_CLIENT_SECRETS_FILE")}="/path/to/client_secrets.json"

Test:
  socialia post youtube "Test" --video test.mp4 --dry-run
""",
        "analytics": f"""
GOOGLE ANALYTICS SETUP
======================

PART 1: Send Events (Measurement Protocol)
------------------------------------------
1. Go to https://analytics.google.com/
2. Admin > Data Streams > Select your stream
3. Measurement Protocol API secrets > Create

Environment Variables:
  export {get_env_var_name("GOOGLE_ANALYTICS_MEASUREMENT_ID")}="G-XXXXXXXXXX"
  export {get_env_var_name("GOOGLE_ANALYTICS_API_SECRET")}="..."

Test:
  socialia analytics track test_event

PART 2: Read Data (Data API) - Optional
---------------------------------------
1. Get Property ID: GA Admin > Property Settings (numeric, e.g., 379172597)
2. Go to https://console.cloud.google.com/
3. Enable "Google Analytics Data API"
4. IAM & Admin > Service Accounts > Create
   - Name: socialia-analytics
   - Create key > JSON > Download
5. In GA: Admin > Property access management
   - Add service account email with Viewer role

Environment Variables:
  export {get_env_var_name("GOOGLE_ANALYTICS_PROPERTY_ID")}="379172597"
  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

Test:
  socialia analytics realtime
  socialia analytics pageviews
  socialia analytics sources
""",
    }
    return guides[platform]


def cmd_setup(args) -> int:
    """Show platform setup instructions."""
    platform = getattr(args, "platform", "all") or "all"

    if platform == "all":
        for name in ["twitter", "linkedin", "reddit", "youtube", "analytics"]:
            click.echo(_get_setup_guide(name))
    else:
        click.echo(_get_setup_guide(platform))

    return 0
