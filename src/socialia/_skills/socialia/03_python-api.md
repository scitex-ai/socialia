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
| `GoogleAnalytics()` | `track_event()`, `get_page_views()`, `get_traffic_sources()`, `get_realtime_users()` | GA4; Measurement Protocol for events, Data API for reports |

## Analytics setup and results

`GoogleAnalytics.track_event()` sends events using the measurement ID and API
secret. The three `get_*` methods query the Data API and require the
`socialia[analytics]` extra, a property ID and Google application credentials.
Methods return dictionaries: check `result["success"]` before reading metrics;
failed requests include `result["error"]`.

The implementation is `src/socialia/analytics.py`; the public CLI adapter is
`src/socialia/cli/_commands.py::cmd_analytics`. Existing controls in
`tests/test_analytics.py` cover event success/failure with an injected HTTP
client, credential lookup and analytics CLI help. They do not establish live
Google ingestion or successful credentialed Data API reports.

## Utility Functions

| Function | Purpose |
|----------|---------|
| `move_to_scheduled(path)` | Move draft to scheduled directory |
| `move_to_posted(path)` | Move to posted directory after publishing |
| `ensure_project_dirs()` | Create project directory structure |
| `PLATFORM_STRATEGIES` | Platform content-strategy guidance text; `{}` if optional MCP support cannot import |
