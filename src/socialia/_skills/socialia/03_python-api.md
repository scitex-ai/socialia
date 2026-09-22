---
description: |
  [TOPIC] Python Api
  [DETAILS] Python API reference — platform client classes, methods, and utility functions.
tags: [socialia-python-api]
---

# Python API

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
| `PLATFORM_STRATEGIES` | Dict mapping platform names to client classes |

## Sync Function API (§6 parity surface)

Same-named sync functions mirroring the MCP tools — one code path
behind the CLI, MCP, and Python call:

| Function | Mirrors MCP tool |
|----------|------------------|
| `social_post(platform, text, ...)` | `social_post` |
| `social_delete(platform, post_id)` | `social_delete` |
| `social_status(platform)` | `social_status` |
| `analytics_track(event_name, params)` | `social_analytics_track` |
| `analytics_pageviews(start_date, end_date, path)` | `social_analytics_pageviews` |
| `analytics_sources(start_date, end_date)` | `social_analytics_sources` |
| `analytics_realtime()` | `social_analytics_realtime` |
| `get_usage()` | `get_usage` |
