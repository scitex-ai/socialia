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
