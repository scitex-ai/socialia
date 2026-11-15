"""Schedule-file controls use owned files; no due post or platform operation runs."""

import json

import pytest

from socialia.scheduler import (
    _load_schedule,
    cancel_scheduled,
    list_scheduled,
    run_due_jobs,
    schedule_post,
)


_FUTURE_JOB = {
    "id": "owned-future", "platform": "twitter", "text": "not dispatched",
    "scheduled_for": "9999-12-31T23:59:59", "status": "pending",
}
_BAD_STORES = [
    b"not JSON",
    b'[{"id":"retained","text":"truncated',
    b'{"jobs":[]}',
    b"null",
    b"42",
    b'"not a job list"',
    b"[null]",
    b'[{"id":"first","id":"owned","status":"cancelled"}]',
    b'[{"id":"first","i\\u0064":"owned","status":"cancelled"}]',
    b'[{"id":"owned","status":"cancelled","status":"cancelled"}]',
    b'[{"id":"owned","status":"cancelled","extension":{"key":1,"key":2}}]',
    json.dumps([_FUTURE_JOB, None]).encode(),
]


def _invoke(operation, path):
    if operation == "load":
        return _load_schedule(path)
    if operation == "add":
        return schedule_post("twitter", "owned queued post", "+1h", schedule_file=path)
    if operation == "list":
        return list_scheduled(schedule_file=path)
    if operation == "cancel":
        return cancel_scheduled("owned", schedule_file=path)
    return run_due_jobs(schedule_file=path)


@pytest.mark.parametrize("operation", ["load", "add", "list", "cancel", "run"])
@pytest.mark.parametrize("payload", _BAD_STORES)
def test_invalid_schedule_is_rejected_without_replacing_bytes(tmp_path, operation, payload):
    # Arrange
    path = tmp_path / "scheduled.json"
    path.write_bytes(payload)
    error = None
    # Act
    try:
        _invoke(operation, path)
    except Exception as caught:
        error = caught
    # Assert
    assert (isinstance(error, ValueError), path.read_bytes()) == (True, payload)


def test_missing_schedule_initializes_an_empty_list(tmp_path):
    # Arrange
    path = tmp_path / "owned runtime/scheduled.json"
    # Act
    result = _load_schedule(path)
    # Assert
    assert (result, path.read_bytes()) == ([], b"[]")


def test_valid_job_objects_retain_legacy_and_extension_fields(tmp_path):
    # Arrange
    jobs = [{"id": "legacy", "status": "cancelled", "extension": {"nested": [1, 2]}}]
    payload = json.dumps(jobs, indent=4).encode()
    path = tmp_path / "scheduled.json"
    path.write_bytes(payload)
    # Act
    result = _load_schedule(path)
    # Assert
    assert (result, path.read_bytes()) == (jobs, payload)



def test_distinct_objects_may_reuse_keys_without_changing_bytes(tmp_path):
    # Arrange
    jobs = [
        {"id": "one", "status": "cancelled", "extension": {"key": 1}},
        {"id": "two", "status": "cancelled", "extension": {"key": 2}},
    ]
    payload = json.dumps(jobs, indent=4).encode()
    path = tmp_path / "scheduled.json"
    path.write_bytes(payload)
    # Act
    result = _load_schedule(path)
    # Assert
    assert (result, path.read_bytes()) == (jobs, payload)
