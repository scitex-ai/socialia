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

The source startup fix after 0.5.15 keeps `socialia mcp start` in a single
event loop. `tests/integration/test_mcp_stdio_start.py` checks a real stdio
initialization and tool listing without invoking any platform operation.

## Per-platform status

`social_status(platform)` routes through the canonical CLI command
`socialia check-platforms <platform> --json`. `show-status` (and its legacy
`status` alias) shows global configuration and does not take a platform argument.
The tool keeps the platform-keyed check result and adds `cli_command`.

A missing-credential response has `status: "not_configured"` and `success: false`
inside the requested platform record. A completed CLI invocation is not proof
of successful authentication; inspect that record. With credentials configured,
the existing client check can make platform network requests. This tool does
not post or delete content.

The route is owned by `_mcp/handlers.py::social_status` and registered in
`_mcp/tools/social.py`. Controls in
`tests/integration/test_mcp_status_route.py` exercise the handler and actual
in-process MCP client/server through the real CLI for all five platforms, using
owned empty credential/file contexts. They also retain the legacy `check`
alias. Live authentication, network reachability, stdio startup and installed
skill delivery require separate qualification.
