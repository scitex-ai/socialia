MCP Server
==========

Socialia provides an MCP (Model Context Protocol) server for AI agent integration.

Starting the Server
-------------------

.. code-block:: bash

    socialia mcp start

Available Tools
---------------

List tools with different verbosity levels:

.. code-block:: bash

    socialia mcp list-tools         # Names only
    socialia mcp list-tools -v      # With signatures
    socialia mcp list-tools -vv     # + descriptions
    socialia mcp list-tools -vvv    # + full documentation

Social Module (7 tools)
~~~~~~~~~~~~~~~~~~~~~~~

**social_post**
    Post content to social media platforms.

    .. code-block:: python

        social_post(
            platform: string,      # twitter, linkedin, reddit, slack, youtube
            text: string,
            reply_to: string = None,
            image: string = None,  # Image path (Twitter only)
            dry_run: boolean = False
        ) -> dict

**social_delete**
    Delete a post by ID.

    .. code-block:: python

        social_delete(
            platform: string,
            post_id: string
        ) -> dict

**social_status**
    Check authentication status for a platform.

    .. code-block:: python

        social_status(platform: string) -> dict

Analytics Module (4 tools)
~~~~~~~~~~~~~~~~~~~~~~~~~~

**social_analytics_track**
    Track custom event in Google Analytics.

**social_analytics_pageviews**
    Get page view metrics.

**social_analytics_sources**
    Get traffic sources.

**social_analytics_realtime**
    Get realtime active users.

Claude Desktop Configuration
----------------------------

Run this command to see your configuration:

.. code-block:: bash

    socialia mcp installation

Example configuration for Claude Desktop:

.. code-block:: json

    {
      "mcpServers": {
        "socialia": {
          "command": "socialia",
          "args": ["mcp", "start"],
          "env": {
            "SOCIALIA_X_CONSUMER_KEY": "...",
            "SOCIALIA_X_CONSUMER_KEY_SECRET": "...",
            "SOCIALIA_X_ACCESSTOKEN": "...",
            "SOCIALIA_X_ACCESSTOKEN_SECRET": "..."
          }
        }
      }
    }

Health Check
------------

Verify server configuration:

.. code-block:: bash

    socialia mcp doctor

This checks:
- fastmcp package installation
- Platform credential configuration
- CLI availability in PATH
