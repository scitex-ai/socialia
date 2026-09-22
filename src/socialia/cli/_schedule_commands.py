#!/usr/bin/env python3
"""Schedule CLI command handlers for socialia."""

import json
import sys
import scitex_logging as slogging
log = slogging.getLogger(__name__)


def cmd_schedule(args, output_json: bool = False) -> int:
    """Handle schedule command."""
    from ..scheduler import (
        list_scheduled,
        cancel_scheduled,
        run_due_jobs,
        run_daemon,
        SCHEDULE_FILE,
    )

    cmd = getattr(args, "schedule_command", None)

    if cmd == "list":
        full = getattr(args, "full", False)
        jobs = list_scheduled(full=full)
        if output_json:
            sys.stdout.write(json.dumps({"file": str(SCHEDULE_FILE), "jobs": jobs}, indent=2) + "\n")
        elif not jobs:
            msg = "No jobs" if full else "No scheduled posts"
            log.info(f"{msg} ({SCHEDULE_FILE})")
        else:
            # Group by source file
            source_files = set(
                j.get("source_file") for j in jobs if j.get("source_file")
            )
            title = "All jobs" if full else "Scheduled posts"
            log.info(f"{title} ({len(jobs)}) - {SCHEDULE_FILE}")
            if source_files:
                log.info(f"Source: {', '.join(source_files)}")
            log.info("─" * 50)
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
                    log.info(f"  {status_icon} [{job['id']}] {job['platform']} @ {scheduled}")
                    log.info(f"         {headline}")
                else:
                    log.info(f"  {status_icon} [{job['id']}] {job['platform']} @ {scheduled}")
                    text = job.get("text", "")[:60]
                    if len(job.get("text", "")) > 60:
                        text += "..."
                    log.info(f"         {text}")

                # Show cancel reason if any
                if full and job.get("cancel_reason"):
                    log.info(f"         Reason: {job['cancel_reason']}")
                log.info("")
        return 0

    elif cmd == "cancel":
        result = cancel_scheduled(args.job_id)
        if output_json:
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
        elif result["success"]:
            log.info(f"Cancelled job: {args.job_id}")
        else:
            log.error(f"Error: {result['error']}")
            return 1
        return 0

    elif cmd == "run":
        results = run_due_jobs()
        if output_json:
            sys.stdout.write(json.dumps(results, indent=2) + "\n")
        elif not results:
            log.info("No jobs due")
        else:
            for r in results:
                status = "✅" if r.get("success") else "❌"
                log.info(f"{status} Job {r['job_id']}")
                if r.get("url"):
                    log.info(f"   URL: {r['url']}")
                if r.get("error"):
                    log.info(f"   Error: {r['error']}")
        return 0

    elif cmd == "daemon":
        log.info(f"Schedule file: {SCHEDULE_FILE}")
        run_daemon(interval=args.interval)
        return 0

    elif cmd == "update-source":
        from ..scheduler import update_source_path

        result = update_source_path(args.old_path, args.new_path)
        if output_json:
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
        elif result["updated"] > 0:
            log.info(f"Updated {result['updated']} job(s) to: {result['new_path']}")
        else:
            log.info(f"No jobs found with source: {args.old_path}")
        return 0

    else:
        log.error("Usage: socialia schedule {list|cancel|run|daemon|update-source}")
        return 1
