#!/usr/bin/env python3
"""CLI commands for org mode draft management."""

import json
import sys
from pathlib import Path

import click


def add_org_parser(subparsers, platforms: list[str]) -> None:
    """Add org subcommand to main parser."""
    org_parser = subparsers.add_parser(
        "org",
        help="Manage drafts from org mode files",
        description="Parse, schedule, and post from Emacs org mode files",
    )
    org_sub = org_parser.add_subparsers(dest="org_command", help="Org operations")

    org_status_parser = org_sub.add_parser(
        "status",
        help="Show draft status from org file",
        description="Display status summary of all drafts",
    )
    org_status_parser.add_argument("file", type=Path, help="Org file path")

    org_list_parser = org_sub.add_parser(
        "list",
        help="List drafts from org file",
        description="Show all drafts with their content",
    )
    org_list_parser.add_argument("file", type=Path, help="Org file path")
    org_list_parser.add_argument(
        "--status",
        choices=["TODO", "DONE", "CANCELLED"],
        help="Filter by status",
    )

    org_post_parser = org_sub.add_parser(
        "post",
        help="Post due drafts from org file",
        description="Post drafts that are due (scheduled time passed)",
    )
    org_post_parser.add_argument("file", type=Path, help="Org file path")
    org_post_parser.add_argument(
        "--all", action="store_true", help="Post all pending drafts"
    )
    org_post_parser.add_argument(
        "--due", action="store_true", help="Post only due drafts (default)"
    )
    org_post_parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Preview without posting"
    )

    org_schedule_parser = org_sub.add_parser(
        "schedule",
        help="Schedule drafts from org file",
        description="Add future scheduled drafts to scheduler",
    )
    org_schedule_parser.add_argument("file", type=Path, help="Org file path")
    org_schedule_parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Preview without scheduling"
    )
    org_schedule_parser.add_argument(
        "--fluctuation",
        "-f",
        type=int,
        default=0,
        help="Add random fluctuation (±minutes) for human-like timing",
    )
    org_schedule_parser.add_argument(
        "--fluctuation-bias",
        choices=["early", "late", "none"],
        default="none",
        help="Bias fluctuation direction (default: none)",
    )

    org_init_parser = org_sub.add_parser(
        "init",
        help="Create new org draft file",
        description="Generate template org file for drafts",
    )
    org_init_parser.add_argument("file", type=Path, help="Output file path")
    org_init_parser.add_argument(
        "--platform",
        "-p",
        choices=platforms,
        default="twitter",
        help="Default platform (default: twitter)",
    )
    org_init_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing file"
    )

    # sync command - org file as source of truth
    org_sync_parser = org_sub.add_parser(
        "sync",
        help="Sync org file with scheduler (org = source of truth)",
        description="Synchronize scheduler with org file - adds new, cancels removed",
    )
    org_sync_parser.add_argument("file", type=Path, help="Org file path")
    org_sync_parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Preview without syncing"
    )
    org_sync_parser.add_argument(
        "--fluctuation",
        "-f",
        type=int,
        default=0,
        help="Add random fluctuation (±minutes) for new jobs",
    )
    org_sync_parser.add_argument(
        "--fluctuation-bias",
        choices=["early", "late", "none"],
        default="none",
        help="Bias fluctuation direction (default: none)",
    )


def cmd_org(args, output_json: bool = False) -> int:
    """Handle org command dispatch."""
    if args.org_command == "status":
        return cmd_org_status(args, output_json=output_json)
    elif args.org_command == "list":
        return cmd_org_list(args, output_json=output_json)
    elif args.org_command == "post":
        return cmd_org_post(args, output_json=output_json)
    elif args.org_command == "schedule":
        return cmd_org_schedule(args, output_json=output_json)
    elif args.org_command == "init":
        return cmd_org_init(args, output_json=output_json)
    elif args.org_command == "sync":
        return cmd_org_sync(args, output_json=output_json)
    else:
        click.echo(
            "Error: Specify org subcommand (status, list, post, schedule, init, sync)"
        )
        return 1


def cmd_org_status(args, output_json: bool = False) -> int:
    """Show status of drafts in an org file."""
    from ..org import OrgDraftManager

    filepath = Path(args.file)
    if not filepath.exists():
        click.echo(f"Error: File not found: {filepath}", err=True)
        return 1

    manager = OrgDraftManager(filepath)
    report = manager.status_report()

    if output_json:
        click.echo(json.dumps(report, indent=2))
    else:
        click.echo(f"📄 {report['file']}")
        click.echo("=" * 50)
        click.echo(f"Total drafts: {report['total']}")
        click.echo(f"  Pending:    {report['pending']}")
        click.echo(f"  Done:       {report['done']}")
        click.echo(f"  Due now:    {report['due_now']}")
        click.echo(f"  Scheduled:  {report['scheduled']}")
        click.echo("")

        if report["drafts"]:
            click.echo("Drafts:")
            for d in report["drafts"]:
                status_icon = {
                    "TODO": "⬜",
                    "DONE": "✅",
                    "CANCELLED": "❌",
                }.get(d["status"], "❓")

                due_marker = " 🔴 DUE" if d["is_due"] else ""
                sched = f" @ {d['scheduled']}" if d["scheduled"] else ""

                click.echo(
                    f"  {status_icon} [{d['platform']}] {d['headline']}{sched}{due_marker}"
                )
                click.echo(f"      {d['char_count']} chars")

    return 0


def cmd_org_list(args, output_json: bool = False) -> int:
    """List drafts from an org file."""
    from ..org import OrgDraftManager

    filepath = Path(args.file)
    if not filepath.exists():
        click.echo(f"Error: File not found: {filepath}", err=True)
        return 1

    manager = OrgDraftManager(filepath)
    status_filter = getattr(args, "status", None)
    drafts = manager.list_drafts(status=status_filter)

    if output_json:
        data = [
            {
                "headline": d.headline,
                "status": d.status,
                "platform": d.platform,
                "scheduled": d.scheduled.isoformat() if d.scheduled else None,
                "content": d.content,
                "is_due": d.is_due,
            }
            for d in drafts
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        for d in drafts:
            status_icon = {"TODO": "⬜", "DONE": "✅", "CANCELLED": "❌"}.get(
                d.status, "❓"
            )
            sched = (
                d.scheduled.strftime("%Y-%m-%d %H:%M") if d.scheduled else "unscheduled"
            )
            click.echo(f"{status_icon} [{d.platform}] {d.headline}")
            click.echo(f"   Scheduled: {sched}")
            click.echo(f"   Content ({len(d.content)} chars):")
            # Show first 100 chars
            preview = d.content[:100].replace("\n", " ")
            click.echo(f"   {preview}...")
            click.echo("")

    return 0


def cmd_org_post(args, output_json: bool = False) -> int:
    """Post drafts from an org file."""
    from ..org import OrgDraftManager

    filepath = Path(args.file)
    if not filepath.exists():
        click.echo(f"Error: File not found: {filepath}", err=True)
        return 1

    manager = OrgDraftManager(filepath)
    dry_run = getattr(args, "dry_run", False)

    # Check what to post
    if getattr(args, "all", False):
        drafts = manager.get_pending()
    elif getattr(args, "due", False):
        drafts = manager.get_due()
    else:
        # Post only items that are due
        drafts = manager.get_due()

    if not drafts:
        if output_json:
            click.echo(
                json.dumps(
                    {"success": True, "message": "No drafts to post", "results": []}
                )
            )
        else:
            click.echo("No drafts due for posting.")
        return 0

    results = []
    for draft in drafts:
        result = manager.post_draft(draft, dry_run=dry_run)
        result["headline"] = draft.headline
        results.append(result)

    if output_json:
        click.echo(json.dumps({"success": True, "results": results}, indent=2))
    else:
        prefix = "[DRY RUN] " if dry_run else ""
        for r in results:
            status = "✅" if r.get("success") else "❌"
            click.echo(f"{prefix}{status} {r.get('headline', 'Unknown')}")
            if r.get("url"):
                click.echo(f"   URL: {r['url']}")
            if r.get("error"):
                click.echo(f"   Error: {r['error']}")

    return 0


def cmd_org_schedule(args, output_json: bool = False) -> int:
    """Schedule drafts from an org file."""
    from ..org import OrgDraftManager

    filepath = Path(args.file)
    if not filepath.exists():
        click.echo(f"Error: File not found: {filepath}", err=True)
        return 1

    manager = OrgDraftManager(filepath)
    dry_run = getattr(args, "dry_run", False)
    fluctuation = getattr(args, "fluctuation", 0)
    fluctuation_bias = getattr(args, "fluctuation_bias", "none")

    results = manager.schedule_all(
        dry_run=dry_run,
        fluctuation=fluctuation,
        fluctuation_bias=fluctuation_bias,
    )

    if not results:
        if output_json:
            click.echo(
                json.dumps(
                    {"success": True, "message": "No drafts to schedule", "results": []}
                )
            )
        else:
            click.echo("No drafts with future scheduled times.")
        return 0

    if output_json:
        click.echo(json.dumps({"success": True, "results": results}, indent=2))
    else:
        prefix = "[DRY RUN] " if dry_run else ""
        fluct_info = f" (±{fluctuation}min fluctuation)" if fluctuation > 0 else ""
        click.echo(f"{prefix}Scheduled {len(results)} draft(s){fluct_info}:")
        for r in results:
            status = "📅" if r.get("success") else "❌"
            sched = r.get("scheduled_for", "unknown")
            # Show original vs actual time if fluctuation applied
            if r.get("original_time") and r.get("original_time") != sched:
                fluct_mins = r.get("fluctuation_minutes", 0)
                sign = "+" if fluct_mins >= 0 else ""
                time_info = (
                    f"{r['original_time']} → {sched} ({sign}{fluct_mins:.0f}min)"
                )
            else:
                time_info = sched
            click.echo(f"  {status} {r.get('headline', 'Unknown')} -> {time_info}")
            if r.get("job_id"):
                click.echo(f"     Job ID: {r['job_id']}")
            if r.get("error"):
                click.echo(f"     Error: {r['error']}")

        if not dry_run:
            # Show if file was moved
            moved_to = results[0].get("moved_to") if results else None
            if moved_to:
                click.echo(f"\n📁 Moved to: {moved_to}")
            click.echo("\nRun 'socialia schedule daemon' to start the scheduler.")

    return 0


def cmd_org_init(args, output_json: bool = False) -> int:
    """Create a new org file template for drafts."""
    from datetime import datetime, timedelta

    filepath = Path(args.file)
    if filepath.exists() and not getattr(args, "force", False):
        click.echo(f"Error: File already exists: {filepath}", err=True)
        click.echo("Use --force to overwrite.", err=True)
        return 1

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Generate template
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    day_after = now + timedelta(days=2)

    platform = getattr(args, "platform", "twitter")

    template = f"""#+TITLE: Social Media Drafts
#+AUTHOR: {Path.home().name}
#+STARTUP: showall

* Drafts [0/2]

** TODO [#A] Example Draft 1
   SCHEDULED: <{tomorrow.strftime("%Y-%m-%d %a")} 10:00>
   :PROPERTIES:
   :PLATFORM: {platform}
   :ID: draft-001
   :END:

Your first draft content goes here.

Write multiple lines if needed.

** TODO [#B] Example Draft 2
   SCHEDULED: <{day_after.strftime("%Y-%m-%d %a")} 10:00>
   :PROPERTIES:
   :PLATFORM: {platform}
   :ID: draft-002
   :END:

Second draft content.

* Archive
# Move DONE items here after posting
"""

    filepath.write_text(template)

    if output_json:
        click.echo(json.dumps({"success": True, "file": str(filepath)}))
    else:
        click.echo(f"Created: {filepath}")
        click.echo(f"Platform: {platform}")
        click.echo("\nEdit the file and run:")
        click.echo(f"  socialia org status {filepath}")
        click.echo(f"  socialia org schedule {filepath}")

    return 0


def cmd_org_sync(args, output_json: bool = False) -> int:
    """Sync org file with scheduler - org file is source of truth."""
    from ..org import OrgDraftManager

    filepath = Path(args.file)
    if not filepath.exists():
        click.echo(f"Error: File not found: {filepath}", err=True)
        return 1

    manager = OrgDraftManager(filepath)
    dry_run = getattr(args, "dry_run", False)
    fluctuation = getattr(args, "fluctuation", 0)
    fluctuation_bias = getattr(args, "fluctuation_bias", "none")

    if dry_run:
        # Preview mode - just show what would happen
        from ..scheduler import _load_schedule

        org_scheduled = {d.headline: d for d in manager.get_scheduled()}
        jobs = _load_schedule()
        file_jobs = {
            j.get("headline", j.get("id")): j
            for j in jobs
            if j.get("source_file") == str(filepath) and j.get("status") == "pending"
        }

        would_cancel = [j["id"] for h, j in file_jobs.items() if h not in org_scheduled]
        would_add = [h for h in org_scheduled.keys() if h not in file_jobs]
        unchanged = [h for h in org_scheduled.keys() if h in file_jobs]

        result = {
            "success": True,
            "dry_run": True,
            "file": str(filepath),
            "would_add": would_add,
            "would_cancel": would_cancel,
            "unchanged": unchanged,
        }

        if output_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"[DRY RUN] Sync preview for: {filepath}")
            click.echo("=" * 50)
            if would_add:
                click.echo(f"Would ADD {len(would_add)} job(s):")
                for h in would_add:
                    click.echo(f"  + {h}")
            if would_cancel:
                click.echo(f"Would CANCEL {len(would_cancel)} job(s):")
                for jid in would_cancel:
                    click.echo(f"  - {jid}")
            if unchanged:
                click.echo(f"Unchanged: {len(unchanged)} job(s)")
            if not would_add and not would_cancel:
                click.echo("Already in sync.")
        return 0

    # Actually sync
    result = manager.sync_with_scheduler(
        fluctuation=fluctuation,
        fluctuation_bias=fluctuation_bias,
    )

    if output_json:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Synced: {result['file']}")
        click.echo("=" * 50)
        if result["added"]:
            click.echo(f"Added {len(result['added'])} job(s):")
            for h in result["added"]:
                click.echo(f"  + {h}")
        if result["cancelled"]:
            click.echo(f"Cancelled {len(result['cancelled'])} job(s):")
            for jid in result["cancelled"]:
                click.echo(f"  - {jid}")
        if result["unchanged"]:
            click.echo(f"Unchanged: {len(result['unchanged'])} job(s)")
        if not result["added"] and not result["cancelled"]:
            click.echo("Already in sync.")

    return 0
