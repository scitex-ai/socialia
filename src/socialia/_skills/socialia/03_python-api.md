---
description: |
  [TOPIC] Python Api
  [DETAILS] Python API reference — platform client classes, methods, and utility functions.
tags: [socialia-python-api]
---

# Python API

In source after 0.5.15, public clients and helpers load on first attribute
access. Plain imports and CLI setup metadata do not construct the MCP registry.
`dir(socialia)` still exposes the public names.

## Platform Clients

| Class | Methods | Notes |
|-------|---------|-------|
| `Twitter()` | `post()`, `delete()`, `post_thread()` | Twitter/X API v2 |
| `LinkedIn()` | `post()`, `delete()` | LinkedIn API |
| `Reddit()` | `post()`, `delete()` | Reddit API |
| `Slack()` | `post()`, `delete()` | Slack webhooks |
| `YouTube()` | `post()`, `delete()` | YouTube Data API |
| `GoogleAnalytics()` | `track()`, `pageviews()`, `sources()`, `realtime()` | GA4 |

## Utility Functions

| Function | Purpose |
|----------|---------|
| `move_to_scheduled(path)` | Move draft to scheduled directory |
| `move_to_posted(path)` | Move to posted directory after publishing |
| `ensure_project_dirs()` | Create project directory structure |
| `PLATFORM_STRATEGIES` | Platform content-strategy guidance text; `{}` if optional MCP support cannot import |

## Schedule files

Scheduler functions in `socialia.scheduler` initialize a missing schedule file
with an empty list. An existing file must contain a JSON list of dictionaries.
Malformed JSON, duplicate object fields (including escaped names or nested
objects), or another container shape raises `ValueError` without replacing
the file; filesystem read errors also propagate. Inspect and repair a damaged
queue before retrying. Existing job fields and extension metadata are retained.

`scheduler._load_schedule` delegates decoding to `socialia._schedule_store`. The source controls in
`tests/test_scheduler_integrity.py` exercise byte preservation through load,
add, list, cancel and due-job entry points using owned invalid/future-only files;
`tests/test_scheduler.py` covers the existing scheduler behavior. These checks
cover container integrity, with per-job schema and concurrent-writer handling
requiring separate validation.

Duplicate field names are rejected within each JSON object, even if their values
are equal. Different objects may reuse field names normally. The strict decoder
is `socialia/_schedule_store.py`, with owning controls in
`tests/test__schedule_store.py`; public file-preservation controls are in
`tests/test_scheduler_integrity.py`. This does not validate every job schema,
lock concurrent writers, or make file writes atomic.
