.. Socialia documentation master file

Socialia - Unified Social Media Management
==========================================

**Socialia** is a unified social media management package for posting, analytics, and insights. Part of `SciTeX <https://scitex.ai>`_ for scientific research automation.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   cli
   mcp

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/socialia

Key Features
------------

- **Multi-Platform Support**: Twitter/X, LinkedIn, Reddit, Slack, YouTube
- **Three Interfaces**: Python API, CLI commands, and MCP server (8 tools)
- **Analytics Integration**: Google Analytics tracking and reporting
- **Scheduling**: Schedule posts for later with daemon support
- **Org-mode Integration**: Draft management with Emacs org-mode
- **AI Integration**: MCP server for AI agent workflows

Quick Example
-------------

Python API:

.. code-block:: python

    from socialia import Twitter, LinkedIn, GoogleAnalytics

    # Post to Twitter
    twitter = Twitter()
    twitter.post("Hello World!")

    # Post to LinkedIn
    linkedin = LinkedIn()
    linkedin.post("Professional update!")

    # Track analytics
    ga = GoogleAnalytics()
    ga.track_event("page_view", {"page": "/docs"})

CLI:

.. code-block:: bash

    # Post to Twitter
    socialia post twitter "Hello World!"

    # Post with image
    socialia post twitter "Check this out!" --image photo.jpg

    # Schedule a post
    socialia post twitter "Hello!" --schedule "10:00"

    # Check all platform connections
    socialia check

MCP Server:

.. code-block:: bash

    # Start MCP server
    socialia mcp start

    # List available tools
    socialia mcp list-tools -v

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
