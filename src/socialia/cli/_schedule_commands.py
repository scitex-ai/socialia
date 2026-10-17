#!/usr/bin/env python3
"""Schedule CLI command handlers for socialia."""

import json
import sys

import click


def cmd_schedule(args, output_json: bool = False) -> int:
    """Handle schedule command."""
    from ..scheduler import (
        SCHEDULE_FILE,
        cancel_scheduled,
        list_scheduled,
        run_daemon,
        run_due_jobs,
    )

    cmd = getattr(args, "schedule_command", None)

    if cmd == "list":
        full = getattr(args, "full", False)
        jobs = list_scheduled(full=full)
        if output_json:
            click.echo(json.dumps({"file": str(SCHEDULE_FILE), "jobs": jobs}, indent=2))
        elif not jobs:
            msg = "No jobs" if full else "No scheduled posts"
            click.echo(f"{msg} ({SCHEDULE_FILE})")
        else:
            # Group by source file
            source_files = set(
                j.get("source_file") for j in jobs if j.get("source_file")
            )
            title = "All jobs" if full else "Scheduled posts"
            click.echo(f"{title} ({len(jobs)}) - {SCHEDULE_FILE}")
            if source_files:
                click.echo(f"Source: {', '.join(source_files)}")
            click.echo("─" * 50)
            for job in jobs:
                scheduled = job.get("scheduled_for", "")[:16].replace("T", " ")
                status = job.get("status", "pending")
                headline = job.get("headline", "")

                # Status indicator
                status_icon = {
                    "pending": "⏳",
                    "completed": "✅",
                    "cancelled": "❌",
                    "failed": "💥",
                }.get(status, "❓")

                if headline:
                    click.echo(
                        f"  {status_icon} [{job['id']}] {job['platform']} @ {scheduled}"
                    )
                    click.echo(f"         {headline}")
                else:
                    click.echo(
                        f"  {status_icon} [{job['id']}] {job['platform']} @ {scheduled}"
                    )
                    text = job.get("text", "")[:60]
                    if len(job.get("text", "")) > 60:
                        text += "..."
                    click.echo(f"         {text}")

                # Show cancel reason if any
                if full and job.get("cancel_reason"):
                    click.echo(f"         Reason: {job['cancel_reason']}")
                click.echo("")
        return 0

    elif cmd == "cancel":
        result = cancel_scheduled(args.job_id)
        if output_json:
            click.echo(json.dumps(result, indent=2))
        elif result["success"]:
            click.echo(f"Cancelled job: {args.job_id}")
        else:
            click.echo(f"Error: {result['error']}", err=True)
            return 1
        return 0

    elif cmd == "run":
        results = run_due_jobs()
        if output_json:
            click.echo(json.dumps(results, indent=2))
        elif not results:
            click.echo("No jobs due")
        else:
            for r in results:
                status = "✅" if r.get("success") else "❌"
                click.echo(f"{status} Job {r['job_id']}")
                if r.get("url"):
                    click.echo(f"   URL: {r['url']}")
                if r.get("error"):
                    click.echo(f"   Error: {r['error']}")
        return 0

    elif cmd == "daemon":
        click.echo(f"Schedule file: {SCHEDULE_FILE}")
        run_daemon(interval=args.interval)
        return 0

    elif cmd == "update-source":
        from ..scheduler import update_source_path

        result = update_source_path(args.old_path, args.new_path)
        if output_json:
            click.echo(json.dumps(result, indent=2))
        elif result["updated"] > 0:
            click.echo(f"Updated {result['updated']} job(s) to: {result['new_path']}")
        else:
            click.echo(f"No jobs found with source: {args.old_path}")
        return 0

    else:
        click.echo(
            "Usage: socialia schedule {list|cancel|run|daemon|update-source}", err=True,
        )
        return 1
