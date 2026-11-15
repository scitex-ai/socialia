"""Decode schedule storage without choosing between duplicate object fields."""

import json
from pathlib import Path


def _decode_schedule(text: str, *, source: Path) -> list:
    """Return job objects, rejecting malformed or ambiguous JSON storage."""
    def reject_duplicate_keys(pairs):
        record = {}
        for key, value in pairs:
            if key in record:
                raise ValueError(
                    f"Schedule file {source} contains duplicate object key {key!r}"
                )
            record[key] = value
        return record

    jobs = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(jobs, list) or any(not isinstance(job, dict) for job in jobs):
        raise ValueError(f"Schedule file {source} must contain a list of job objects")
    return jobs
