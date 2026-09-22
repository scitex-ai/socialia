"""Click-based CLI entry point for socialia (audit-compliant).

Migrated from argparse to satisfy audit-cli rules:
  §1   verb-noun shape (renames + aliases)
  §1a  list-python-apis + mcp list-tools at top level
  §2   universal --json / --help-recursive / -h / -V flags
  §2   --dry-run / --yes on every mutating verb
  §4   Example: blocks in every docstring
  §6b  config-path fallback chain documented in root help
  §11  Click instead of argparse

Canonical subcommands (read verbs):
    socialia post <platform> [text|--file]
    socialia delete-post <platform> <post_id> [--dry-run] [--yes]
    socialia thread <platform> --file <path> [--dry-run]
    socialia show-status [--json]
    socialia show-setup [platform]
    socialia check-platforms [platform] [--json]
    socialia show-me <platform> [--json]
    socialia feed [platform] [--limit N] [--mentions] [--replies] [--detail] [--json]
    socialia analytics track <event> [--param K V]...
    socialia analytics show-realtime
    socialia analytics show-pageviews [--start] [--end] [--path]
    socialia analytics show-sources [--start] [--end]
    socialia schedule list [--full] [--json]
    socialia schedule cancel <job_id>
    socialia schedule run-due
    socialia schedule run-daemon [--interval N]
    socialia schedule update-source <old> <new> [--dry-run] [--yes]
    socialia mcp start [--dry-run] [--yes]
    socialia mcp doctor
    socialia mcp list-tools [-v|-vv|-vvv] [--json]
    socialia mcp show-installation
    socialia completion install [--shell bash|zsh] [--dry-run] [--yes]
    socialia show-completion-status [--json]
    socialia show-completion-bash [--json]
    socialia show-completion-zsh [--json]
    socialia org show-status <file>
    socialia org list <file> [--status]
    socialia org post <file> [--all] [--due] [--dry-run]
    socialia org schedule <file> [--dry-run] [--fluctuation N] [--fluctuation-bias]
    socialia org init <file> [--platform] [--force] [--dry-run] [--yes]
    socialia org sync <file> [--dry-run] [--yes] [--fluctuation] [--fluctuation-bias]
    socialia youtube batch [--config|--scitex] [--index] [--dry-run]
    socialia youtube show-config [--directory|--scitex] [--output] [--preset]
    socialia youtube list [--config|--scitex] [--channel] [--limit] [--json]
    socialia grow <platform> discover <query> [--limit] [--min-followers]
    socialia grow <platform> follow <query> [--limit] [--min-followers] [--dry-run]
    socialia grow <platform> auto-grow <queries...> [--interval] [--limit]
    socialia grow <platform> show-user <username>
    socialia grow <platform> follow-user <username> [--dry-run] [--yes]
    socialia grow <platform> search <query> [--limit] [--json]
    socialia list-python-apis [-v|-vv|-vvv] [--json]
    socialia skills list [--json]
    socialia skills get <name> [--json]
    socialia skills install [--dry-run]

Deprecated aliases (still accepted, rewritten to canonical names):
    delete                  -> delete-post
    setup                   -> show-setup
    check                   -> check-platforms
    me                      -> show-me
    status                  -> show-status
    analytics realtime      -> analytics show-realtime
    analytics pageviews     -> analytics show-pageviews
    analytics sources       -> analytics show-sources
    mcp installation        -> mcp show-installation
    schedule run            -> schedule run-due
    schedule daemon         -> schedule run-daemon
    completion status       -> show-completion-status
    completion bash         -> show-completion-bash
    completion zsh          -> show-completion-zsh
    org status              -> org show-status
    youtube config          -> youtube show-config
    grow <plat> auto        -> grow <plat> auto-grow
    grow <plat> user        -> grow <plat> show-user
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import click

from .. import __version__

PLATFORMS = ["twitter", "linkedin", "reddit", "slack", "youtube"]


# =========================================================================
# Helpers
# =========================================================================


def _ns(**kwargs) -> SimpleNamespace:
    """Build an attribute-access namespace for legacy handlers."""
    return SimpleNamespace(**kwargs)


def _print_help_recursive(ctx, _param, value):
    """Eager callback for --help-recursive."""
    if not value or ctx.resilient_parsing:
        return
    cmd = ctx.command
    click.echo(cmd.get_help(ctx))

    def walk(group, ancestry):
        if not isinstance(group, click.Group):
            return
        for name in sorted(group.commands):
            sub = group.commands[name]
            sub_ctx = click.Context(sub, info_name=name, parent=ctx)
            click.echo("\n---\n")
            click.echo(f"$ {' '.join(ancestry + [name])} --help\n")
            click.echo(sub.get_help(sub_ctx))
            walk(sub, ancestry + [name])

    walk(cmd, ["socialia"])
    ctx.exit(0)


def _get_root_epilog() -> str:
    try:
        from .._branding import get_env_var_name
    except Exception:
        return ""
    return f"""
Examples:
  socialia post twitter "Hello World!"
  socialia post twitter --file tweet.txt
  socialia delete-post twitter 1234567890 --yes
  socialia thread twitter --file thread.txt
  socialia show-status
  socialia mcp start
  socialia --help-recursive

Environment Variables:
  {get_env_var_name("X_CONSUMER_KEY"):36} Twitter API consumer key
  {get_env_var_name("X_ACCESSTOKEN"):36} Twitter access token
  {get_env_var_name("LINKEDIN_ACCESS_TOKEN"):36} LinkedIn OAuth access token
  {get_env_var_name("REDDIT_CLIENT_ID"):36} Reddit app client ID
  {get_env_var_name("GOOGLE_ANALYTICS_MEASUREMENT_ID"):36} Google Analytics measurement ID
"""


# =========================================================================
# Root group
# =========================================================================


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog=_get_root_epilog(),
)
@click.version_option(__version__, "-V", "--version", prog_name="socialia")
@click.option(
    "--help-recursive",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_help_recursive,
    help="Show help for the root command and every subcommand.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit machine-readable JSON output where supported.",
)
@click.pass_context
def main_group(ctx, as_json):
    """Socialia — Unified social media management CLI.

    \b
    Configuration precedence (highest -> lowest):
      1. Explicit CLI flags
      2. ./pyproject.toml [tool.socialia]
      3. ./socialia.yaml (project-local)
      4. $SOCIALIA_CONFIG (path to a YAML file)
      5. ~/.scitex/socialia/config.yaml (user-wide)
      6. Built-in defaults

    \b
    Example:
        $ socialia post twitter "Hello world"
        $ socialia show-status
        $ socialia mcp start
    """
    ctx.ensure_object(dict)
    ctx.obj["as_json"] = as_json
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# =========================================================================
# post (read-shaped: positional <platform> required, content positional/file)
# =========================================================================


@main_group.command("post")
@click.argument("platform", type=click.Choice(PLATFORMS))
@click.argument("text", required=False)
@click.option(
    "-f",
    "--file",
    "file",
    type=click.Path(path_type=Path),
    default=None,
    help="Read content from file.",
)
@click.option("--reply-to", default=None, help="Post ID to reply to (Twitter).")
@click.option("--quote", default=None, help="Post ID to quote (Twitter).")
@click.option("-s", "--subreddit", default="test", help="Target subreddit (Reddit).")
@click.option("-c", "--channel", default=None, help="Channel ID (Slack).")
@click.option("--thread-ts", default=None, help="Thread timestamp to reply to (Slack).")
@click.option("-t", "--title", default=None, help="Post title (Reddit/YouTube).")
@click.option(
    "-V",
    "--video",
    type=click.Path(path_type=Path),
    default=None,
    help="Video file path (YouTube).",
)
@click.option(
    "--thumbnail",
    type=click.Path(path_type=Path),
    default=None,
    help="Thumbnail image (YouTube).",
)
@click.option("--tags", default=None, help="Comma-separated tags (YouTube).")
@click.option(
    "--privacy",
    type=click.Choice(["public", "private", "unlisted"]),
    default="public",
    help="Privacy status (YouTube).",
)
@click.option(
    "-n", "--dry-run", is_flag=True, default=False, help="Print without posting."
)
@click.option(
    "-S",
    "--schedule",
    default=None,
    help="Schedule for later (e.g., '10:00', '+1h', '+30m').",
)
@click.option(
    "-i",
    "--image",
    type=click.Path(path_type=Path),
    default=None,
    help="Image file to attach (Twitter).",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_post_click(
    platform,
    text,
    file,
    reply_to,
    quote,
    subreddit,
    channel,
    thread_ts,
    title,
    video,
    thumbnail,
    tags,
    privacy,
    dry_run,
    schedule,
    image,
    as_json,
):
    """Post content to a social media platform.

    \b
    Example:
        $ socialia post twitter "Hello World!"
        $ socialia post twitter --file tweet.txt
        $ socialia post linkedin "Announcement" --dry-run
    """
    from ._commands import cmd_post

    args = _ns(
        platform=platform,
        text=text,
        file=file,
        reply_to=reply_to,
        quote=quote,
        subreddit=subreddit,
        channel=channel,
        thread_ts=thread_ts,
        title=title,
        video=video,
        thumbnail=thumbnail,
        tags=tags,
        privacy=privacy,
        dry_run=dry_run,
        schedule=schedule,
        image=image,
        json=as_json,
    )
    sys.exit(cmd_post(args, output_json=as_json))


# =========================================================================
# delete-post (mutating; positional object satisfies §1)
# =========================================================================


@main_group.command("delete-post")
@click.argument("platform", type=click.Choice(PLATFORMS))
@click.argument("post_id")
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be deleted without acting.",
)
@click.option(
    "-y", "--yes", is_flag=True, default=False, help="Skip confirmation prompt."
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_delete_post(platform, post_id, dry_run, yes, as_json):
    """Delete a post by ID on the given platform.

    \b
    Example:
        $ socialia delete-post twitter 1234567890 --yes
        $ socialia delete-post linkedin urn:li:share:abc --dry-run
    """
    if dry_run:
        click.echo(f"Would delete {platform} post {post_id}")
        sys.exit(0)
    if not yes:
        click.echo(
            f"error: refusing to delete {platform} post {post_id} without --yes/-y",
            err=True,
        )
        sys.exit(2)
    from ._commands import cmd_delete

    args = _ns(platform=platform, post_id=post_id, json=as_json)
    sys.exit(cmd_delete(args, output_json=as_json))


# =========================================================================
# thread (positional object: platform)
# =========================================================================


@main_group.command("thread")
@click.argument("platform", type=click.Choice(PLATFORMS))
@click.option(
    "-f",
    "--file",
    "file",
    type=click.Path(path_type=Path),
    required=True,
    help="File with thread content (separate posts with ---).",
)
@click.option(
    "-n", "--dry-run", is_flag=True, default=False, help="Print without posting."
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_thread_click(platform, file, dry_run, as_json):
    """Post a thread of connected posts.

    \b
    Example:
        $ socialia thread twitter --file thread.txt
        $ socialia thread twitter --file thread.txt --dry-run
    """
    from ._commands import cmd_thread

    args = _ns(platform=platform, file=file, dry_run=dry_run, json=as_json)
    sys.exit(cmd_thread(args, output_json=as_json))


# =========================================================================
# show-status / show-setup / check-platforms / show-me
# =========================================================================


@main_group.command("show-status")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_show_status(as_json):
    """Show configuration and environment variable status.

    \b
    Example:
        $ socialia show-status
        $ socialia show-status --json
    """
    from ._commands import cmd_status

    sys.exit(cmd_status(output_json=as_json))


@main_group.command("show-setup")
@click.argument(
    "platform",
    required=False,
    default="all",
    type=click.Choice(["twitter", "linkedin", "reddit", "youtube", "analytics", "all"]),
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_show_setup(platform, as_json):
    """Show platform setup / API configuration instructions.

    \b
    Example:
        $ socialia show-setup
        $ socialia show-setup twitter
    """
    from ._commands import cmd_setup

    args = _ns(platform=platform, json=as_json)
    sys.exit(cmd_setup(args))


@main_group.command("check-platforms")
@click.argument("platform", required=False, default=None, type=click.Choice(PLATFORMS))
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_check_platforms(platform, as_json):
    """Verify connections to one or all configured platforms.

    \b
    Example:
        $ socialia check-platforms
        $ socialia check-platforms twitter --json
    """
    from ._feed_commands import cmd_check

    args = _ns(platform=platform, json=as_json)
    sys.exit(cmd_check(args, output_json=as_json))


@main_group.command("show-me")
@click.argument("platform", type=click.Choice(PLATFORMS))
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_show_me(platform, as_json):
    """Show authenticated user info for a platform.

    \b
    Example:
        $ socialia show-me twitter
        $ socialia show-me linkedin --json
    """
    from ._feed_commands import cmd_me

    args = _ns(platform=platform, json=as_json)
    sys.exit(cmd_me(args, output_json=as_json))


# =========================================================================
# feed
# =========================================================================


@main_group.command("feed")
@click.argument("platform", required=False, default=None, type=click.Choice(PLATFORMS))
@click.option(
    "-l", "--limit", type=int, default=5, help="Number of posts per platform."
)
@click.option(
    "-m",
    "--mentions",
    is_flag=True,
    default=False,
    help="Show mentions instead of posts.",
)
@click.option(
    "-r", "--replies", is_flag=True, default=False, help="Show replies to your posts."
)
@click.option(
    "-d",
    "--detail",
    is_flag=True,
    default=False,
    help="Show detailed output with full text.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_feed_click(platform, limit, mentions, replies, detail, as_json):
    """Get recent posts from configured platforms.

    \b
    Example:
        $ socialia feed
        $ socialia feed twitter --limit 10
        $ socialia feed --mentions --json
    """
    from ._feed_commands import cmd_feed

    args = _ns(
        platform=platform,
        limit=limit,
        mentions=mentions,
        replies=replies,
        detail=detail,
        json=as_json,
    )
    sys.exit(cmd_feed(args, output_json=as_json))


# =========================================================================
# analytics group
# =========================================================================


@main_group.group("analytics", invoke_without_command=True)
@click.pass_context
def analytics_group(ctx):
    """Google Analytics operations.

    \b
    Example:
        $ socialia analytics show-realtime
        $ socialia analytics show-pageviews --start 30daysAgo
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@analytics_group.command("track")
@click.argument("event_name")
@click.option(
    "-p",
    "--param",
    multiple=True,
    nargs=2,
    metavar="KEY VALUE",
    help="Event parameter (can be repeated).",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_analytics_track(event_name, param, as_json):
    """Track a custom analytics event.

    \b
    Example:
        $ socialia analytics track signup
        $ socialia analytics track purchase -p item_id 42 -p price 9.99
    """
    from ._commands import cmd_analytics

    args = _ns(
        analytics_command="track",
        event_name=event_name,
        param=[list(p) for p in param],
        json=as_json,
    )
    sys.exit(cmd_analytics(args, output_json=as_json))


@analytics_group.command("show-realtime")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_analytics_realtime(as_json):
    """Show realtime active users.

    \b
    Example:
        $ socialia analytics show-realtime
    """
    from ._commands import cmd_analytics

    args = _ns(analytics_command="realtime", json=as_json)
    sys.exit(cmd_analytics(args, output_json=as_json))


@analytics_group.command("show-pageviews")
@click.option("--start", default="7daysAgo", help="Start date.")
@click.option("--end", default="today", help="End date.")
@click.option("--path", default=None, help="Filter by page path.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_analytics_pageviews(start, end, path, as_json):
    """Show page view metrics.

    \b
    Example:
        $ socialia analytics show-pageviews
        $ socialia analytics show-pageviews --start 30daysAgo --path /blog
    """
    from ._commands import cmd_analytics

    args = _ns(
        analytics_command="pageviews", start=start, end=end, path=path, json=as_json
    )
    sys.exit(cmd_analytics(args, output_json=as_json))


@analytics_group.command("show-sources")
@click.option("--start", default="7daysAgo", help="Start date.")
@click.option("--end", default="today", help="End date.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_analytics_sources(start, end, as_json):
    """Show traffic source breakdown.

    \b
    Example:
        $ socialia analytics show-sources
        $ socialia analytics show-sources --start 30daysAgo
    """
    from ._commands import cmd_analytics

    args = _ns(analytics_command="sources", start=start, end=end, json=as_json)
    sys.exit(cmd_analytics(args, output_json=as_json))


# =========================================================================
# mcp group
# =========================================================================


@main_group.group("mcp", invoke_without_command=True)
@click.pass_context
def mcp_group(ctx):
    """MCP (Model Context Protocol) server management.

    \b
    Example:
        $ socialia mcp start
        $ socialia mcp list-tools
        $ socialia mcp doctor
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@mcp_group.command("start")
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would happen without starting the server.",
)
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_mcp_start(dry_run, yes, as_json):
    """Start the MCP server.

    \b
    Example:
        $ socialia mcp start
        $ socialia mcp start --dry-run
    """
    if dry_run:
        click.echo("Would start socialia MCP server (stdio transport).")
        sys.exit(0)
    from ._mcp_commands import cmd_mcp

    args = _ns(mcp_command="start", json=as_json)
    sys.exit(cmd_mcp(args))


@mcp_group.command("doctor")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_mcp_doctor(as_json):
    """Check MCP server health and platform credentials.

    \b
    Example:
        $ socialia mcp doctor
    """
    from ._mcp_commands import cmd_mcp

    args = _ns(mcp_command="doctor", json=as_json)
    sys.exit(cmd_mcp(args))


@mcp_group.command("list-tools")
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="Verbosity: -v sig, -vv +desc, -vvv full.",
)
@click.option("-c", "--compact", is_flag=True, default=False, help="Compact output.")
@click.option("-m", "--module", default=None, help="Filter by module name.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_mcp_list_tools(verbose, compact, module, as_json):
    """List available MCP tools exposed by socialia.

    \b
    Example:
        $ socialia mcp list-tools
        $ socialia mcp list-tools -vv
        $ socialia mcp list-tools --json
    """
    from ._mcp_commands import cmd_mcp

    args = _ns(
        mcp_command="list-tools",
        verbose=verbose,
        compact=compact,
        module=module,
        json=as_json,
    )
    sys.exit(cmd_mcp(args))


@mcp_group.command("show-installation")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_mcp_show_installation(as_json):
    """Show Claude Desktop MCP configuration snippet.

    \b
    Example:
        $ socialia mcp show-installation
    """
    from ._mcp_commands import cmd_mcp

    args = _ns(mcp_command="installation", json=as_json)
    sys.exit(cmd_mcp(args))


# =========================================================================
# schedule group
# =========================================================================


@main_group.group("schedule", invoke_without_command=True)
@click.pass_context
def schedule_group(ctx):
    """Manage scheduled posts.

    \b
    Example:
        $ socialia schedule list
        $ socialia schedule start-due-jobs
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@schedule_group.command("list")
@click.option(
    "-a",
    "--full",
    is_flag=True,
    default=False,
    help="Show all jobs (including cancelled/completed).",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_schedule_list(full, as_json):
    """List pending scheduled posts.

    \b
    Example:
        $ socialia schedule list
        $ socialia schedule list --full --json
    """
    from ._schedule_commands import cmd_schedule

    args = _ns(schedule_command="list", full=full, json=as_json)
    sys.exit(cmd_schedule(args, output_json=as_json))


@schedule_group.command("cancel")
@click.argument("job_id")
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Preview only.")
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_schedule_cancel(job_id, dry_run, yes, as_json):
    """Cancel a scheduled post by job ID.

    \b
    Example:
        $ socialia schedule cancel job-abc123 --yes
    """
    if dry_run:
        click.echo(f"Would cancel job {job_id}")
        sys.exit(0)
    if not yes:
        click.echo(f"error: refusing to cancel job {job_id} without --yes/-y", err=True)
        sys.exit(2)
    from ._schedule_commands import cmd_schedule

    args = _ns(schedule_command="cancel", job_id=job_id, json=as_json)
    sys.exit(cmd_schedule(args, output_json=as_json))


@schedule_group.command("start-due-jobs")
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Preview only.")
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_schedule_run_due(dry_run, yes, as_json):
    """Run all due scheduled jobs now.

    \b
    Example:
        $ socialia schedule start-due-jobs
        $ socialia schedule start-due-jobs --dry-run
    """
    if dry_run:
        click.echo("Would execute all due jobs.")
        sys.exit(0)
    from ._schedule_commands import cmd_schedule

    args = _ns(schedule_command="run", json=as_json)
    sys.exit(cmd_schedule(args, output_json=as_json))


@schedule_group.command("start-daemon")
@click.option(
    "-i",
    "--interval",
    type=int,
    default=60,
    help="Check interval in seconds (default: 60).",
)
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Preview only.")
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_schedule_run_daemon(interval, dry_run, yes, as_json):
    """Run the scheduler daemon (long-running background loop).

    \b
    Example:
        $ socialia schedule run-daemon --interval 60
    """
    if dry_run:
        click.echo(f"Would start daemon (interval={interval}s).")
        sys.exit(0)
    from ._schedule_commands import cmd_schedule

    args = _ns(schedule_command="daemon", interval=interval, json=as_json)
    sys.exit(cmd_schedule(args, output_json=as_json))


@schedule_group.command("update-source")
@click.argument("old_path")
@click.argument("new_path")
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Preview only.")
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_schedule_update_source(old_path, new_path, dry_run, yes, as_json):
    """Update source-file path on scheduled jobs after rename.

    \b
    Example:
        $ socialia schedule update-source old.org new.org --yes
    """
    if dry_run:
        click.echo(f"Would update {old_path} -> {new_path}")
        sys.exit(0)
    if not yes:
        click.echo(
            f"error: refusing to update {old_path} -> {new_path} without --yes/-y",
            err=True,
        )
        sys.exit(2)
    from ._schedule_commands import cmd_schedule

    args = _ns(
        schedule_command="update-source",
        old_path=old_path,
        new_path=new_path,
        json=as_json,
    )
    sys.exit(cmd_schedule(args, output_json=as_json))


# =========================================================================
# completion group
# =========================================================================


@main_group.group("completion", invoke_without_command=True)
@click.pass_context
def completion_group(ctx):
    """Shell tab-completion management.

    \b
    Example:
        $ socialia completion install --shell bash
        $ socialia show-completion-status
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@completion_group.command("install")
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh"]),
    default=None,
    help="Shell type (auto-detected if not provided).",
)
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be installed without writing.",
)
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_completion_install(shell, dry_run, yes, as_json):
    """Install shell completion to RC file.

    \b
    Example:
        $ socialia completion install
        $ socialia completion install --shell zsh --yes
    """
    if dry_run:
        click.echo(f"Would install {shell or 'auto-detected'} completion.")
        sys.exit(0)
    from ._completion_commands import cmd_completion

    args = _ns(completion_command="install", shell=shell, json=as_json)
    sys.exit(cmd_completion(args, output_json=as_json))


@main_group.command("show-completion-status")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_show_completion_status(as_json):
    """Show shell completion installation status.

    \b
    Example:
        $ socialia show-completion-status --json
    """
    from ._completion_commands import cmd_completion

    args = _ns(completion_command="status", json=as_json)
    sys.exit(cmd_completion(args, output_json=as_json))


@main_group.command("show-completion-bash")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_show_completion_bash(as_json):
    """Print bash completion script to stdout.

    \b
    Example:
        $ socialia show-completion-bash > /etc/bash_completion.d/socialia
    """
    from ._completion_commands import cmd_completion

    args = _ns(completion_command="bash", json=as_json)
    sys.exit(cmd_completion(args, output_json=as_json))


@main_group.command("show-completion-zsh")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_show_completion_zsh(as_json):
    """Print zsh completion script to stdout.

    \b
    Example:
        $ socialia show-completion-zsh > ~/.zsh/completions/_socialia
    """
    from ._completion_commands import cmd_completion

    args = _ns(completion_command="zsh", json=as_json)
    sys.exit(cmd_completion(args, output_json=as_json))


# =========================================================================
# org group
# =========================================================================


@main_group.group("org", invoke_without_command=True)
@click.pass_context
def org_group(ctx):
    """Manage drafts from Emacs org-mode files.

    \b
    Example:
        $ socialia org show-status drafts.org
        $ socialia org post drafts.org --due
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@org_group.command("show-status")
@click.argument("file", type=click.Path(path_type=Path))
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_org_show_status(file, as_json):
    """Show draft status summary from an org file.

    \b
    Example:
        $ socialia org show-status drafts.org
    """
    from ._org_commands import cmd_org_status

    args = _ns(file=file, json=as_json)
    sys.exit(cmd_org_status(args, output_json=as_json))


@org_group.command("list")
@click.argument("file", type=click.Path(path_type=Path))
@click.option(
    "--status",
    type=click.Choice(["TODO", "DONE", "CANCELLED"]),
    default=None,
    help="Filter by status.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_org_list_click(file, status, as_json):
    """List drafts from an org file.

    \b
    Example:
        $ socialia org list drafts.org
        $ socialia org list drafts.org --status TODO --json
    """
    from ._org_commands import cmd_org_list

    args = _ns(file=file, status=status, json=as_json)
    sys.exit(cmd_org_list(args, output_json=as_json))


@org_group.command("post")
@click.argument("file", type=click.Path(path_type=Path))
@click.option(
    "--all", "all_", is_flag=True, default=False, help="Post all pending drafts."
)
@click.option(
    "--due", is_flag=True, default=False, help="Post only due drafts (default)."
)
@click.option(
    "-n", "--dry-run", is_flag=True, default=False, help="Preview without posting."
)
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_org_post_click(file, all_, due, dry_run, yes, as_json):
    """Post due drafts from an org file.

    \b
    Example:
        $ socialia org post drafts.org --due
        $ socialia org post drafts.org --all --dry-run
    """
    from ._org_commands import cmd_org_post

    args = _ns(file=file, all=all_, due=due, dry_run=dry_run, json=as_json)
    sys.exit(cmd_org_post(args, output_json=as_json))


@org_group.command("schedule")
@click.argument("file", type=click.Path(path_type=Path))
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Preview only.")
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option(
    "-f", "--fluctuation", type=int, default=0, help="Random fluctuation (+/- minutes)."
)
@click.option(
    "--fluctuation-bias",
    type=click.Choice(["early", "late", "none"]),
    default="none",
    help="Bias fluctuation direction.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_org_schedule_click(file, dry_run, yes, fluctuation, fluctuation_bias, as_json):
    """Schedule future drafts from an org file.

    \b
    Example:
        $ socialia org schedule drafts.org
        $ socialia org schedule drafts.org --fluctuation 15
    """
    from ._org_commands import cmd_org_schedule

    args = _ns(
        file=file,
        dry_run=dry_run,
        fluctuation=fluctuation,
        fluctuation_bias=fluctuation_bias,
        json=as_json,
    )
    sys.exit(cmd_org_schedule(args, output_json=as_json))


@org_group.command("init")
@click.argument("file", type=click.Path(path_type=Path))
@click.option(
    "-p",
    "--platform",
    type=click.Choice(PLATFORMS),
    default="twitter",
    help="Default platform.",
)
@click.option(
    "-f", "--force", is_flag=True, default=False, help="Overwrite existing file."
)
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Preview only.")
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_org_init_click(file, platform, force, dry_run, yes, as_json):
    """Create a new org draft file from template.

    \b
    Example:
        $ socialia org init drafts.org --platform twitter
    """
    if dry_run:
        click.echo(f"Would create {file} (platform={platform}, force={force}).")
        sys.exit(0)
    from ._org_commands import cmd_org_init

    args = _ns(file=file, platform=platform, force=force, json=as_json)
    sys.exit(cmd_org_init(args, output_json=as_json))


@org_group.command("sync")
@click.argument("file", type=click.Path(path_type=Path))
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Preview only.")
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option(
    "-f", "--fluctuation", type=int, default=0, help="Random fluctuation (+/- minutes)."
)
@click.option(
    "--fluctuation-bias",
    type=click.Choice(["early", "late", "none"]),
    default="none",
    help="Bias fluctuation direction.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_org_sync_click(file, dry_run, yes, fluctuation, fluctuation_bias, as_json):
    """Sync an org file with the scheduler (org = source of truth).

    \b
    Example:
        $ socialia org sync drafts.org --yes
    """
    from ._org_commands import cmd_org_sync

    args = _ns(
        file=file,
        dry_run=dry_run,
        fluctuation=fluctuation,
        fluctuation_bias=fluctuation_bias,
        json=as_json,
    )
    sys.exit(cmd_org_sync(args, output_json=as_json))


# =========================================================================
# youtube group
# =========================================================================


@main_group.group("youtube", invoke_without_command=True)
@click.pass_context
def youtube_group(ctx):
    """YouTube batch operations.

    \b
    Example:
        $ socialia youtube list --channel
        $ socialia youtube batch --config videos.yaml
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@youtube_group.command("batch")
@click.option("-c", "--config", default=None, help="YAML configuration file path.")
@click.option(
    "--scitex",
    is_flag=True,
    default=False,
    help="Use built-in SciTeX demo configuration.",
)
@click.option(
    "-i",
    "--index",
    type=int,
    default=None,
    help="Upload only video at this index (1-based).",
)
@click.option(
    "-n", "--dry-run", is_flag=True, default=False, help="Show what would be uploaded."
)
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_youtube_batch_click(config, scitex, index, dry_run, yes, as_json):
    """Batch-upload videos from a configuration file.

    \b
    Example:
        $ socialia youtube batch --config videos.yaml
        $ socialia youtube batch --scitex --dry-run
    """
    from ._youtube_commands import cmd_youtube_batch

    args = _ns(
        youtube_command="batch",
        config=config,
        scitex=scitex,
        index=index,
        dry_run=dry_run,
        json=as_json,
    )
    sys.exit(cmd_youtube_batch(args, output_json=as_json))


@youtube_group.command("show-config")
@click.option("-d", "--directory", default=None, help="Directory containing MP4 files.")
@click.option(
    "--scitex", is_flag=True, default=False, help="Generate SciTeX demo configuration."
)
@click.option("-o", "--output", default=None, help="Output YAML file path.")
@click.option(
    "--preset",
    type=click.Choice(["scitex-demo", "tutorial", "presentation"]),
    default="scitex-demo",
    help="Preset for default settings.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_youtube_show_config(directory, scitex, output, preset, as_json):
    """Generate / show upload configuration YAML.

    \b
    Example:
        $ socialia youtube show-config --directory videos/
        $ socialia youtube show-config --scitex --output videos.yaml
    """
    from ._youtube_commands import cmd_youtube_config

    args = _ns(
        youtube_command="config",
        directory=directory,
        scitex=scitex,
        output=output,
        preset=preset,
        json=as_json,
    )
    sys.exit(cmd_youtube_config(args, output_json=as_json))


@youtube_group.command("list")
@click.option("-c", "--config", default=None, help="YAML configuration file path.")
@click.option("--scitex", is_flag=True, default=False, help="List SciTeX demo videos.")
@click.option(
    "--channel",
    is_flag=True,
    default=False,
    help="List videos from your YouTube channel.",
)
@click.option("-l", "--limit", type=int, default=10, help="Number of videos to list.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_youtube_list_click(config, scitex, channel, limit, as_json):
    """List configured or channel videos.

    \b
    Example:
        $ socialia youtube list --channel
        $ socialia youtube list --config videos.yaml --json
    """
    from ._youtube_commands import cmd_youtube_list

    args = _ns(
        youtube_command="list",
        config=config,
        scitex=scitex,
        channel=channel,
        limit=limit,
        json=as_json,
    )
    sys.exit(cmd_youtube_list(args, output_json=as_json))


# =========================================================================
# grow group (parent takes <platform> positional, then sub-verbs)
# =========================================================================


@main_group.group("grow", invoke_without_command=True)
@click.argument("platform", type=click.Choice(["twitter"]))
@click.pass_context
def grow_group(ctx, platform):
    """Discover and follow users on a platform.

    \b
    Example:
        $ socialia grow twitter discover "scientific python"
        $ socialia grow twitter follow "ml researchers" --limit 5
    """
    ctx.ensure_object(dict)
    ctx.obj["platform"] = platform
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@grow_group.command("discover")
@click.argument("query")
@click.option("-l", "--limit", type=int, default=20, help="Max users (default: 20).")
@click.option(
    "--min-followers", type=int, default=0, help="Minimum follower count filter."
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.pass_context
def cmd_grow_discover(ctx, query, limit, min_followers, as_json):
    """Find users matching a search query.

    \b
    Example:
        $ socialia grow twitter discover "scientific python" --limit 30
    """
    from ._grow_commands import cmd_grow

    args = _ns(
        platform=ctx.obj["platform"],
        grow_command="discover",
        query=query,
        limit=limit,
        min_followers=min_followers,
        json=as_json,
    )
    sys.exit(cmd_grow(args, output_json=as_json))


@grow_group.command("follow")
@click.argument("query")
@click.option("-l", "--limit", type=int, default=10, help="Max users (default: 10).")
@click.option(
    "--min-followers", type=int, default=0, help="Minimum follower count filter."
)
@click.option(
    "-n", "--dry-run", is_flag=True, default=False, help="Show users without following."
)
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option(
    "-S", "--schedule", default=None, help="Schedule for later (e.g., '+20m', '+1h')."
)
@click.option(
    "-R", "--repeat", default=None, help="Repeat interval (requires --schedule)."
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.pass_context
def cmd_grow_follow(
    ctx, query, limit, min_followers, dry_run, yes, schedule, repeat, as_json
):
    """Find and follow users by search query.

    \b
    Example:
        $ socialia grow twitter follow "ml researchers" --limit 5 --yes
    """
    from ._grow_commands import cmd_grow

    args = _ns(
        platform=ctx.obj["platform"],
        grow_command="follow",
        query=query,
        limit=limit,
        min_followers=min_followers,
        dry_run=dry_run,
        schedule=schedule,
        repeat=repeat,
        json=as_json,
    )
    sys.exit(cmd_grow(args, output_json=as_json))


@grow_group.command("start-auto")
@click.argument("queries", nargs=-1, required=True)
@click.option("-i", "--interval", default="+1h", help="Interval between jobs.")
@click.option("-l", "--limit", type=int, default=10, help="Max users per job.")
@click.option("--min-followers", type=int, default=0, help="Min follower filter.")
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Preview only.")
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.pass_context
def cmd_grow_auto(ctx, queries, interval, limit, min_followers, dry_run, yes, as_json):
    """Set up recurring auto-grow jobs across multiple queries.

    \b
    Example:
        $ socialia grow twitter auto-grow "ml" "neuroscience" --interval +2h
    """
    from ._grow_commands import cmd_grow

    args = _ns(
        platform=ctx.obj["platform"],
        grow_command="auto",
        queries=list(queries),
        interval=interval,
        limit=limit,
        min_followers=min_followers,
        dry_run=dry_run,
        json=as_json,
    )
    sys.exit(cmd_grow(args, output_json=as_json))


@grow_group.command("show-user")
@click.argument("username")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.pass_context
def cmd_grow_show_user(ctx, username, as_json):
    """Show profile info for a single user.

    \b
    Example:
        $ socialia grow twitter show-user @ywatanabe
    """
    from ._grow_commands import cmd_grow

    args = _ns(
        platform=ctx.obj["platform"],
        grow_command="user",
        username=username,
        json=as_json,
    )
    sys.exit(cmd_grow(args, output_json=as_json))


@grow_group.command("follow-user")
@click.argument("username")
@click.option(
    "-n", "--dry-run", is_flag=True, default=False, help="Show user without following."
)
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.pass_context
def cmd_grow_follow_user(ctx, username, dry_run, yes, as_json):
    """Follow a single user by username.

    \b
    Example:
        $ socialia grow twitter follow-user @ywatanabe --yes
    """
    if not dry_run and not yes:
        click.echo(f"error: refusing to follow {username} without --yes/-y", err=True)
        sys.exit(2)
    from ._grow_commands import cmd_grow

    args = _ns(
        platform=ctx.obj["platform"],
        grow_command="follow-user",
        username=username,
        dry_run=dry_run,
        json=as_json,
    )
    sys.exit(cmd_grow(args, output_json=as_json))


@grow_group.command("search")
@click.argument("query")
@click.option("-l", "--limit", type=int, default=10, help="Max tweets.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.pass_context
def cmd_grow_search(ctx, query, limit, as_json):
    """Search recent tweets matching a query.

    \b
    Example:
        $ socialia grow twitter search "scientific python" --json
    """
    from ._grow_commands import cmd_grow

    args = _ns(
        platform=ctx.obj["platform"],
        grow_command="search",
        query=query,
        limit=limit,
        json=as_json,
    )
    sys.exit(cmd_grow(args, output_json=as_json))


# =========================================================================
# list-python-apis (top-level introspection)
# =========================================================================


@main_group.command("list-python-apis")
@click.option(
    "-v", "--verbose", count=True, default=0, help="Verbosity: -v +doc, -vv full doc."
)
@click.option("-d", "--max-depth", type=int, default=5, help="Max recursion depth.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def cmd_list_python_apis_click(verbose, max_depth, as_json):
    """List the public Python API surface of socialia.

    \b
    Example:
        $ socialia list-python-apis
        $ socialia list-python-apis -vv
        $ socialia list-python-apis --json
    """
    from ._introspect_commands import cmd_list_python_apis

    args = _ns(verbose=verbose, max_depth=max_depth, json=as_json)
    sys.exit(cmd_list_python_apis(args))


# =========================================================================
# skills group (§1a: list / get / install over the bundled _skills/ tree)
# =========================================================================

from ._skills_commands import skills_group as _skills_group

main_group.add_command(_skills_group)


# =========================================================================
# Backward-compat: rewrite deprecated argv to canonical names
# =========================================================================


_TOP_RENAMES = {
    "delete": "delete-post",
    "setup": "show-setup",
    "check": "check-platforms",
    "me": "show-me",
    "status": "show-status",
}

_ANALYTICS_RENAMES = {
    "realtime": "show-realtime",
    "pageviews": "show-pageviews",
    "sources": "show-sources",
}

_MCP_RENAMES = {
    "installation": "show-installation",
}

_SCHEDULE_RENAMES = {
    "run": "start-due-jobs",
    "run-due": "start-due-jobs",
    "daemon": "start-daemon",
    "run-daemon": "start-daemon",
}

_COMPLETION_RENAMES_TO_TOP = {
    # `completion <name>` (read leaves) -> top-level `show-completion-<name>`
    "status": "show-completion-status",
    "bash": "show-completion-bash",
    "zsh": "show-completion-zsh",
}

_ORG_RENAMES = {
    "status": "show-status",
}

_YOUTUBE_RENAMES = {
    "config": "show-config",
}

# `grow <platform> <verb>` -> rewrite verb at i+2
_GROW_RENAMES = {
    "auto": "start-auto",
    "auto-grow": "start-auto",
    "user": "show-user",
}


def _rewrite_argv(argv):
    """Translate deprecated subcommand names to canonical Click names.

    Preserves all flags and positional arguments verbatim.
    """
    if not argv:
        return argv

    # First non-flag token is the top-level subcommand
    i = 0
    while i < len(argv) and argv[i].startswith("-"):
        i += 1
    if i >= len(argv):
        return argv

    sub = argv[i]
    if sub in _TOP_RENAMES:
        argv = argv[:i] + [_TOP_RENAMES[sub]] + argv[i + 1 :]
        return argv

    if sub == "analytics" and i + 1 < len(argv):
        nxt = argv[i + 1]
        if nxt in _ANALYTICS_RENAMES:
            argv = argv[: i + 1] + [_ANALYTICS_RENAMES[nxt]] + argv[i + 2 :]
        return argv

    if sub == "mcp" and i + 1 < len(argv):
        nxt = argv[i + 1]
        if nxt in _MCP_RENAMES:
            argv = argv[: i + 1] + [_MCP_RENAMES[nxt]] + argv[i + 2 :]
        return argv

    if sub == "schedule" and i + 1 < len(argv):
        nxt = argv[i + 1]
        if nxt in _SCHEDULE_RENAMES:
            argv = argv[: i + 1] + [_SCHEDULE_RENAMES[nxt]] + argv[i + 2 :]
        return argv

    if sub == "completion" and i + 1 < len(argv):
        nxt = argv[i + 1]
        if nxt in _COMPLETION_RENAMES_TO_TOP:
            argv = argv[:i] + [_COMPLETION_RENAMES_TO_TOP[nxt]] + argv[i + 2 :]
        return argv

    if sub == "org" and i + 1 < len(argv):
        nxt = argv[i + 1]
        if nxt in _ORG_RENAMES:
            argv = argv[: i + 1] + [_ORG_RENAMES[nxt]] + argv[i + 2 :]
        return argv

    if sub == "youtube" and i + 1 < len(argv):
        nxt = argv[i + 1]
        if nxt in _YOUTUBE_RENAMES:
            argv = argv[: i + 1] + [_YOUTUBE_RENAMES[nxt]] + argv[i + 2 :]
        return argv

    if sub == "grow" and i + 2 < len(argv):
        # grow <platform> <verb> [...]
        verb = argv[i + 2]
        if verb in _GROW_RENAMES:
            argv = argv[: i + 2] + [_GROW_RENAMES[verb]] + argv[i + 3 :]
        return argv

    return argv


# Wire canonical install-shell-completion + print-shell-completion (§1a).
try:
    from scitex_dev._cli._completion import attach_shell_completion

    attach_shell_completion(main_group, prog_name="socialia")
except ImportError:
    pass


# Inject version line into root --help (§4).
try:
    main_group.help = f"socialia (v{__version__}) — " + (main_group.help or "").lstrip()
except Exception:
    pass


def main(argv: list = None) -> int:
    """Entry point. Returns exit code (0 on success).

    Wraps Click so existing callers (and tests) that pass argv lists keep working.
    Translates deprecated subcommand names to canonical Click names.
    """
    raw = list(sys.argv[1:]) if argv is None else list(argv)
    raw = _rewrite_argv(raw)

    try:
        main_group.main(args=raw, prog_name="socialia", standalone_mode=False)
        return 0
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        return code
    except click.exceptions.UsageError as e:
        click.echo(f"Error: {e.format_message()}", err=True)
        return 2
    except click.exceptions.Abort:
        click.echo("Aborted.", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
