#!/usr/bin/env python3
"""Scheduler for delayed/scheduled posts."""

import json
import random
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import scitex_logging as slogging

from ._paths import get_schedule_file as _get_schedule_file

log = slogging.getLogger(__name__)

SCHEDULE_FILE: Path = _get_schedule_file()
"""Path to the scheduled-jobs JSON file (under ``~/.scitex/socialia/runtime/``).

Tests may override this at the module level for isolation — see
``_resolve_schedule_file``.
"""


def _resolve_schedule_file(schedule_file=None) -> Path:
    """Resolve the schedule-file path used by a public API call.

    Production callers leave ``schedule_file=None`` and we use the
    module-level ``SCHEDULE_FILE`` (under ``~/.scitex/socialia/runtime/``).
    Tests pass an explicit ``tmp_path`` so they don't mutate the user's home.
    """
    return Path(schedule_file) if schedule_file is not None else SCHEDULE_FILE


def add_human_fluctuation(
    dt: datetime,
    max_minutes: int = 15,
    bias: str = "none",
) -> datetime:
    """
    Add random fluctuation to a datetime for more human-like timing.

    Avoids bot detection by making scheduled times appear natural.

    Args:
        dt: Original datetime
        max_minutes: Maximum fluctuation in minutes (default: ±15)
        bias: "early" (negative), "late" (positive), or "none" (both)

    Returns:
        datetime with random offset applied
    """
    if bias == "early":
        offset = -random.randint(0, max_minutes)
    elif bias == "late":
        offset = random.randint(0, max_minutes)
    else:  # "none" - both directions
        offset = random.randint(-max_minutes, max_minutes)

    return dt + timedelta(minutes=offset)


def _ensure_schedule_file(schedule_file=None):
    """Ensure schedule directory and file exist."""
    sf = _resolve_schedule_file(schedule_file)
    sf.parent.mkdir(parents=True, exist_ok=True)
    if not sf.exists():
        sf.write_text("[]")
    return sf


def _load_schedule(schedule_file=None) -> list:
    """Load scheduled jobs."""
    sf = _ensure_schedule_file(schedule_file)
    try:
        return json.loads(sf.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_schedule(jobs: list, schedule_file=None):
    """Save scheduled jobs."""
    sf = _ensure_schedule_file(schedule_file)
    sf.write_text(json.dumps(jobs, indent=2))


def parse_schedule_time(time_str: str) -> datetime:
    """
    Parse schedule time string.

    Supports:
        - "10:00" - today at 10:00 (or tomorrow if past)
        - "2026-01-23 10:00" - specific date and time
        - "+1h" - 1 hour from now
        - "+30m" - 30 minutes from now
    """
    now = datetime.now()

    # Relative time (+1h, +30m)
    if time_str.startswith("+"):
        amount = int(time_str[1:-1])
        unit = time_str[-1]
        if unit == "h":
            return datetime.fromtimestamp(now.timestamp() + amount * 3600)
        elif unit == "m":
            return datetime.fromtimestamp(now.timestamp() + amount * 60)
        else:
            raise ValueError(f"Unknown time unit: {unit} (use 'h' or 'm')")

    # Full datetime
    if "-" in time_str and " " in time_str:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M")

    # Time only (today or tomorrow)
    if ":" in time_str and "-" not in time_str:
        target = datetime.strptime(time_str, "%H:%M")
        target = target.replace(year=now.year, month=now.month, day=now.day)
        if target <= now:
            # Schedule for tomorrow.  `target.replace(day=now.day + 1)` breaks
            # at month-end (e.g. April 30 + 1 → ValueError).  timedelta crosses
            # month / year boundaries cleanly.
            target = target + timedelta(days=1)
        return target

    raise ValueError(f"Cannot parse time: {time_str}")


def schedule_grow(
    platform: str,
    query: str,
    schedule_time: str,
    limit: int = 10,
    min_followers: int = 0,
    fluctuation: int = 0,
    fluctuation_bias: str = "none",
    repeat_interval: str = None,
) -> dict:
    """
    Schedule a grow job for later.

    Args:
        platform: Target platform (twitter only for now)
        query: Search query for discovering users
        schedule_time: When to run (see parse_schedule_time)
        limit: Max users to follow per run
        min_followers: Minimum audience-size filter
        fluctuation: Max random fluctuation in minutes
        fluctuation_bias: "early", "late", or "none"
        repeat_interval: Repeat interval (e.g., "+1h", "+30m") or None

    Returns:
        dict with 'success', 'job_id', 'scheduled_for'
    """
    try:
        scheduled_dt = parse_schedule_time(schedule_time)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    original_dt = scheduled_dt
    if fluctuation > 0:
        scheduled_dt = add_human_fluctuation(
            scheduled_dt, max_minutes=fluctuation, bias=fluctuation_bias
        )

    job = {
        "id": str(uuid.uuid4())[:8],
        "type": "grow",
        "platform": platform,
        "query": query,
        "limit": limit,
        "min_followers": min_followers,
        "scheduled_for": scheduled_dt.isoformat(),
        "created_at": datetime.now().isoformat(),
        "status": "pending",
    }

    if repeat_interval:
        job["repeat_interval"] = repeat_interval

    if fluctuation > 0:
        job["original_time"] = original_dt.isoformat()
        job["fluctuation_applied"] = (scheduled_dt - original_dt).total_seconds() / 60

    jobs = _load_schedule()
    jobs.append(job)
    _save_schedule(jobs)

    result = {
        "success": True,
        "job_id": job["id"],
        "scheduled_for": scheduled_dt.strftime("%Y-%m-%d %H:%M"),
    }

    if repeat_interval:
        result["repeat_interval"] = repeat_interval

    return result


def schedule_post(
    platform: str,
    text: str,
    schedule_time: str,
    fluctuation: int = 0,
    fluctuation_bias: str = "none",
    *,
    schedule_file=None,
    **kwargs,
) -> dict:
    """
    Schedule a post for later.

    Args:
        platform: Target platform (twitter, linkedin, etc.)
        text: Post content
        schedule_time: When to post (see parse_schedule_time)
        fluctuation: Max random fluctuation in minutes (0=disabled, default)
        fluctuation_bias: "early", "late", or "none" (default)
        **kwargs: Additional arguments (subreddit, title, etc.)

    Returns:
        dict with 'success', 'job_id', 'scheduled_for', 'original_time' (if fluctuated)
    """
    try:
        scheduled_dt = parse_schedule_time(schedule_time)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    original_dt = scheduled_dt
    if fluctuation > 0:
        scheduled_dt = add_human_fluctuation(
            scheduled_dt, max_minutes=fluctuation, bias=fluctuation_bias
        )

    # Extract metadata from kwargs
    source_file = kwargs.pop("source_file", None)
    headline = kwargs.pop("headline", None)

    job = {
        "id": str(uuid.uuid4())[:8],
        "platform": platform,
        "text": text,
        "scheduled_for": scheduled_dt.isoformat(),
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "kwargs": kwargs,
    }

    # Track source file if provided (e.g., from org mode)
    if source_file:
        job["source_file"] = source_file
    if headline:
        job["headline"] = headline

    # Track original time if fluctuation was applied
    if fluctuation > 0:
        job["original_time"] = original_dt.isoformat()
        job["fluctuation_applied"] = (scheduled_dt - original_dt).total_seconds() / 60

    jobs = _load_schedule(schedule_file)
    jobs.append(job)
    _save_schedule(jobs, schedule_file)

    result = {
        "success": True,
        "job_id": job["id"],
        "scheduled_for": scheduled_dt.strftime("%Y-%m-%d %H:%M"),
    }

    if fluctuation > 0:
        result["original_time"] = original_dt.strftime("%Y-%m-%d %H:%M")
        result["fluctuation_minutes"] = job["fluctuation_applied"]

    return result


def _cancel_orphaned_jobs(jobs: list) -> bool:
    """Cancel jobs whose source file no longer exists.

    When source file is renamed/deleted, jobs are cancelled.
    The org file is the source of truth.

    Returns True if any jobs were cancelled.
    """
    cancelled = False
    for job in jobs:
        if job.get("status") != "pending":
            continue
        src = job.get("source_file")
        if src and not Path(src).exists():
            job["status"] = "cancelled"
            job["cancel_reason"] = "source_file_missing"
            cancelled = True
    return cancelled


def list_scheduled(full: bool = False, *, schedule_file=None) -> list:
    """List scheduled jobs.

    Args:
        full: If True, return all jobs including cancelled/completed.
              If False (default), return only pending jobs.
    """
    jobs = _load_schedule(schedule_file)

    # Cancel jobs whose source file is gone
    if _cancel_orphaned_jobs(jobs):
        _save_schedule(jobs, schedule_file)

    if full:
        # Return all jobs sorted by scheduled time
        return sorted(jobs, key=lambda j: j.get("scheduled_for", ""))

    # Filter to pending only and sort by time
    pending = [j for j in jobs if j.get("status") == "pending"]
    return sorted(pending, key=lambda j: j.get("scheduled_for", ""))


def cancel_scheduled(job_id: str, *, schedule_file=None) -> dict:
    """Cancel a scheduled job. Supports prefix matching like screen -r."""
    jobs = _load_schedule(schedule_file)

    # Find matching jobs (prefix match)
    matches = [
        j for j in jobs if j["id"].startswith(job_id) and j.get("status") == "pending"
    ]

    if len(matches) == 0:
        return {"success": False, "error": f"Job not found: {job_id}"}
    elif len(matches) > 1:
        ids = [m["id"] for m in matches]
        return {
            "success": False,
            "error": f"Ambiguous ID '{job_id}' matches: {', '.join(ids)}",
        }

    # Single match - cancel it
    job = matches[0]
    job["status"] = "cancelled"
    _save_schedule(jobs, schedule_file)
    return {"success": True, "cancelled": job["id"]}


def update_source_path(old_path: str, new_path: str) -> dict:
    """Update source_file path for all matching jobs (after file rename)."""
    jobs = _load_schedule()
    updated = 0
    for job in jobs:
        if job.get("source_file") == old_path and job.get("status") == "pending":
            job["source_file"] = new_path
            updated += 1
    if updated > 0:
        _save_schedule(jobs)
    return {"success": True, "updated": updated, "new_path": new_path}


def _run_grow_job(job: dict) -> dict:
    """Execute a grow job."""
    from .twitter import Twitter

    if job["platform"] != "twitter":
        return {"success": False, "error": f"Grow not supported for {job['platform']}"}

    client = Twitter()
    result = client.grow(
        query=job["query"],
        limit=job.get("limit", 10),
        min_followers=job.get("min_followers", 0),
        dry_run=False,
    )
    return result


def run_due_jobs(*, schedule_file=None) -> list:
    """Run all jobs that are due. Returns list of results."""
    from .twitter import Twitter
    from .linkedin import LinkedIn
    from .reddit import Reddit
    from .youtube import YouTube
    from .org_files import move_to_posted

    def get_client(platform):
        if platform == "twitter":
            return Twitter()
        elif platform == "linkedin":
            return LinkedIn()
        elif platform == "reddit":
            return Reddit()
        elif platform == "youtube":
            return YouTube()
        raise ValueError(f"Unknown platform: {platform}")

    jobs = _load_schedule(schedule_file)
    results = []
    now = datetime.now()
    completed_files = set()
    new_jobs = []  # For repeat jobs

    for job in jobs:
        if job.get("status") != "pending":
            continue

        scheduled = datetime.fromisoformat(job["scheduled_for"])
        if scheduled <= now:
            # Job is due
            try:
                job_type = job.get("type", "post")

                if job_type == "grow":
                    result = _run_grow_job(job)
                    job["status"] = "completed"
                    job["result"] = {
                        "followed_count": result.get("followed_count", 0),
                        "rate_limited": result.get("rate_limited", False),
                    }
                    job["executed_at"] = now.isoformat()
                    results.append(
                        {
                            "job_id": job["id"],
                            "type": "grow",
                            "followed": result.get("followed_count", 0),
                            "rate_limited": result.get("rate_limited", False),
                            **result,
                        }
                    )

                    # Schedule repeat if configured
                    if job.get("repeat_interval") and not result.get("rate_limited"):
                        next_time = parse_schedule_time(job["repeat_interval"])
                        new_job = {
                            "id": str(uuid.uuid4())[:8],
                            "type": "grow",
                            "platform": job["platform"],
                            "query": job["query"],
                            "limit": job.get("limit", 10),
                            "min_followers": job.get("min_followers", 0),
                            "scheduled_for": next_time.isoformat(),
                            "created_at": now.isoformat(),
                            "status": "pending",
                            "repeat_interval": job["repeat_interval"],
                            "parent_job": job["id"],
                        }
                        new_jobs.append(new_job)

                else:
                    # Regular post job
                    client = get_client(job["platform"])
                    kwargs = job.get("kwargs", {})
                    result = client.post(job["text"], **kwargs)
                    job["status"] = "completed" if result.get("success") else "failed"
                    job["result"] = result
                    job["executed_at"] = now.isoformat()
                    results.append({"job_id": job["id"], **result})

                    # Track completed source files
                    if result.get("success") and job.get("source_file"):
                        completed_files.add(job["source_file"])

            except Exception as e:
                job["status"] = "failed"
                job["error"] = str(e)
                results.append({"job_id": job["id"], "success": False, "error": str(e)})

    # Add new repeat jobs
    jobs.extend(new_jobs)
    _save_schedule(jobs, schedule_file)

    # Move completed source files to posted/ if all jobs for that file are done
    for source_file in completed_files:
        file_jobs = [j for j in jobs if j.get("source_file") == source_file]
        all_done = all(j.get("status") in ("completed", "cancelled") for j in file_jobs)
        if all_done:
            src_path = Path(source_file)
            if src_path.exists():
                new_path = move_to_posted(src_path)
                if new_path and new_path != src_path:
                    # Update source_file paths in jobs
                    for j in file_jobs:
                        j["source_file"] = str(new_path)
                    _save_schedule(jobs, schedule_file)

    return results


def run_daemon(interval: int = 60):
    """Run scheduler daemon that checks for due jobs."""
    log.info(f"Scheduler daemon started (checking every {interval}s)")
    log.info(f"Schedule file: {SCHEDULE_FILE}")
    log.info("Press Ctrl+C to stop")

    try:
        while True:
            results = run_due_jobs()
            for r in results:
                status = "✅" if r.get("success") else "❌"
                log.info(f"{status} Job {r['job_id']}: {r}")
            time.sleep(interval)
    except KeyboardInterrupt:
        log.info("\nDaemon stopped")
