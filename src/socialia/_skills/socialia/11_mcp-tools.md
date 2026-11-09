---
description: |
  [TOPIC] Mcp Tools
  [DETAILS] MCP tools for social media management and analytics.
tags: [socialia-mcp-tools]
---

# MCP Tools

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `social_post` | `platform`, `text`, `reply_to`, `image`, `dry_run` | Post to platform |
| `social_delete` | `platform`, `post_id` | Delete a post |
| `social_status` | `platform` | Check platform connection |
| `social_analytics_track` | `event_name`, `params` | Track custom GA4 event |
| `social_analytics_pageviews` | `start_date`, `end_date`, `path` | Get page view metrics |
| `social_analytics_sources` | `start_date`, `end_date` | Get traffic sources |
| `social_analytics_realtime` | -- | Get realtime active users |
| `usage` | -- | Read the server's platform strategies and usage guide |

The table reflects the eight tools registered by `socialia._server`.
`check` and `feed` remain CLI operations; they are not registered MCP tools.
Use `socialia mcp list-tools --json` to inspect the current registry.

In source after 0.5.15, `--module analytics --json` selects the four analytics
tools, while `--module social --json` selects the three posting/status tools.
This filters catalog output only, not the server's callable tools. The current
source JSON's `total` and module `count` describe the displayed tool metadata.
