---
description: |
  [TOPIC] Cli Reference
  [DETAILS] Complete CLI reference for socialia — posting, scheduling, analytics, and management.
tags: [socialia-cli-reference]
---

# CLI Reference

```bash
# Posting
socialia post "Hello world!" --platform twitter
socialia thread <file> --platform twitter
socialia delete <post-id> --platform twitter

# Status & Discovery
socialia status                  # Show all platform connection status
socialia check                   # Verify connections to all platforms
socialia me                      # Get authenticated user info
socialia feed                    # Get recent posts from platforms
socialia setup                   # Show platform setup instructions

# Scheduling
socialia schedule list
socialia schedule cancel <id>
socialia schedule run
socialia schedule daemon
socialia schedule update-source

# Analytics (Google Analytics)
socialia analytics track <event_name>
socialia analytics realtime
socialia analytics pageviews [--start <date>] [--end <date>]
socialia analytics sources [--start <date>] [--end <date>]

# Growth
socialia grow                    # Discover and follow users

# Org mode
socialia org                     # Org mode draft management

# YouTube
socialia youtube                 # YouTube batch operations

# MCP server
socialia mcp start
socialia mcp list-tools
socialia mcp list-tools --module analytics --json
socialia mcp doctor
socialia mcp show-installation --json

# Introspection
socialia list-python-apis [-v]
```

In source after 0.5.15, `mcp show-installation --json` emits only an `mcpServers`
configuration object with placeholder credential values. The legacy
`mcp installation --json` alias has the same output. Plain output retains the
human-readable setup instructions. Older 0.5.15 installations print those
instructions even with `--json`; upgrade after this fix is released.

The analytics metadata filter likewise requires the source fixes after 0.5.15:
four `social_analytics_*` tools belong to analytics, not the broader social
namespace. Filtering changes printed metadata only. In the current source JSON,
`total` counts the displayed tools; the selected module's `count` reports its
displayed group. The unfiltered registry still has the same eight tools.
