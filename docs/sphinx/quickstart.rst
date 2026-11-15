Quick Start
===========

This guide shows common operations with Socialia.

Posting Content
---------------

Python API:

.. code-block:: python

    from socialia import Twitter, LinkedIn

    # Post to Twitter
    twitter = Twitter()
    result = twitter.post("Hello World!")
    print(f"Posted: {result['url']}")

    # Post with image
    media = twitter.upload_media("photo.jpg")
    twitter.post("Check this!", media_ids=[media["media_id"]])

    # Post thread
    twitter.post_thread([
        "Thread starts here...",
        "Second tweet in thread",
        "Final tweet!"
    ])

CLI:

.. code-block:: bash

    # Basic post
    socialia post twitter "Hello World!"

    # Post with image
    socialia post twitter "Check this!" --image photo.jpg

    # Post from file
    socialia post twitter --file content.txt

    # Dry run (preview without posting)
    socialia post twitter "Test" --dry-run

Scheduling Posts
----------------

.. code-block:: bash

    # Schedule for specific time today
    socialia post twitter "Morning!" --schedule "09:00"

    # Schedule for specific date/time
    socialia post twitter "Hello!" --schedule "2026-02-14 10:00"

    # Relative scheduling
    socialia post twitter "Soon!" --schedule "+1h"
    socialia post twitter "Later!" --schedule "+30m"

    # View scheduled posts
    socialia schedule list

    # Start scheduler daemon
    socialia schedule daemon

Reading Your Feed
-----------------

.. code-block:: bash

    # Get recent posts from all platforms
    socialia feed

    # Get detailed feed with full text
    socialia feed --detail

    # Get mentions/notifications
    socialia feed --mentions

    # Get replies to your posts
    socialia feed --replies

    # Platform-specific
    socialia feed twitter --limit 10

Analytics
---------

Event tracking uses ``SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID`` and
``SOCIALIA_GOOGLE_ANALYTICS_API_SECRET``. Reporting additionally requires the
``socialia[analytics]`` extra, ``SOCIALIA_GOOGLE_ANALYTICS_PROPERTY_ID`` and
Google application credentials (for example, ``GOOGLE_APPLICATION_CREDENTIALS``).

Methods return dictionaries. Check ``result["success"]`` before reading metrics;
on failure, inspect ``result["error"]``.

Python API:

.. code-block:: python

    from socialia import GoogleAnalytics

    ga = GoogleAnalytics()

    # Track event
    ga.track_event("button_click", {"button": "subscribe"})

    # Get realtime users
    realtime = ga.get_realtime_users()

    # Get page views
    views = ga.get_page_views(start_date="7daysAgo", end_date="today")

    # Get traffic sources
    sources = ga.get_traffic_sources(start_date="7daysAgo", end_date="today")

CLI:

.. code-block:: bash

    # Track event
    socialia analytics track page_view --param page /docs

    # Get realtime users
    socialia analytics show-realtime

    # Get page views
    socialia analytics show-pageviews --start 7daysAgo

    # Get traffic sources
    socialia analytics show-sources

The older ``realtime``, ``pageviews`` and ``sources`` subcommands remain
supported aliases. The commands above use their canonical names.

Source: ``socialia.analytics.GoogleAnalytics`` and
``socialia.cli._commands.cmd_analytics``. The offline controls in
``tests/test_analytics.py`` cover event submission with an injected HTTP client,
credential lookup and CLI help; live ingestion and successful credentialed
Data API reports require separate verification.

MCP Server for AI Agents
------------------------

Start the MCP server:

.. code-block:: bash

    socialia mcp start

List available tools:

.. code-block:: bash

    socialia mcp list-tools -v

Check server health:

.. code-block:: bash

    socialia mcp doctor

Show Claude Desktop configuration:

.. code-block:: bash

    socialia mcp installation
