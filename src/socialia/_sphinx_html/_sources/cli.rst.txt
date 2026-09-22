CLI Reference
=============

Socialia provides a comprehensive CLI for all operations.

Global Options
--------------

.. code-block:: text

    socialia [-h] [-V] [-v] [--json] [--help-recursive]

    -h, --help          Show help message
    -V, --version       Show version
    -v, --verbose       Verbosity level (-v, -vv, -vvv)
    --json              Output as JSON
    --help-recursive    Show help for all commands

Commands Overview
-----------------

.. code-block:: bash

    socialia post           # Post content to platforms
    socialia delete         # Delete a post
    socialia thread         # Post a thread
    socialia feed           # Get recent posts
    socialia check          # Verify connections
    socialia me             # Get user info
    socialia schedule       # Manage scheduled posts
    socialia analytics      # Google Analytics operations
    socialia mcp            # MCP server commands
    socialia status         # Show configuration status
    socialia setup          # Show setup instructions
    socialia completion     # Shell completion
    socialia org            # Org-mode draft management
    socialia youtube        # YouTube batch operations
    socialia grow           # Twitter follower growth
    socialia list-python-apis  # List Python APIs

post
----

Post content to a social media platform.

.. code-block:: bash

    socialia post <platform> <text> [options]

    Platforms: twitter, linkedin, reddit, slack, youtube

    Options:
      -f, --file FILE       Read content from file
      --reply-to ID         Reply to post (Twitter)
      --quote ID            Quote tweet (Twitter)
      -i, --image FILE      Attach image (Twitter)
      -s, --subreddit NAME  Target subreddit (Reddit)
      -t, --title TITLE     Post title (Reddit/YouTube)
      -V, --video FILE      Video file (YouTube)
      -S, --schedule TIME   Schedule for later
      -n, --dry-run         Preview without posting

Examples:

.. code-block:: bash

    socialia post twitter "Hello!"
    socialia post twitter "Photo!" --image photo.jpg
    socialia post linkedin "Professional update"
    socialia post reddit "Check this out" --subreddit python --title "Title"

feed
----

Get recent posts from platforms.

.. code-block:: bash

    socialia feed [platform] [options]

    Options:
      -l, --limit N         Number of posts (default: 5)
      -m, --mentions        Show mentions
      -r, --replies         Show replies
      -d, --detail          Show full text
      --json                Output as JSON

schedule
--------

Manage scheduled posts.

.. code-block:: bash

    socialia schedule list              # List pending posts
    socialia schedule list --full       # Include completed
    socialia schedule cancel <job_id>   # Cancel a job
    socialia schedule run               # Run due jobs now
    socialia schedule daemon            # Start scheduler

mcp
---

MCP (Model Context Protocol) server commands.

.. code-block:: bash

    socialia mcp start          # Start server
    socialia mcp doctor         # Health check
    socialia mcp list-tools     # List tools
    socialia mcp installation   # Show Claude config

    # List tools with verbosity
    socialia mcp list-tools -v      # Signatures
    socialia mcp list-tools -vv     # + descriptions
    socialia mcp list-tools -vvv    # + full docs

analytics
---------

Google Analytics operations.

.. code-block:: bash

    socialia analytics track <event>    # Track event
    socialia analytics realtime         # Realtime users
    socialia analytics pageviews        # Page views
    socialia analytics sources          # Traffic sources
