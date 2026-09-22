#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-01-27
# File: src/socialia/_server.py

"""
MCP server for Socialia - Social Media Automation.

This is the main server entry point. Tools are organized in _mcp/tools/.
"""

from __future__ import annotations

__all__ = ["PLATFORM_STRATEGIES"]

import os
import sys
from pathlib import Path

try:
    from fastmcp import FastMCP
except ImportError as exc:
    raise ImportError(
        "socialia[mcp] is required for the MCP server: pip install socialia[mcp]"
    ) from exc

import scitex_logging as slogging

from ._branding import get_mcp_server_name
from ._mcp.tools import register_all_tools

log = slogging.getLogger(__name__)


# =============================================================================
# Environment Loading
# =============================================================================


def _load_env_file(env_file: str) -> None:
    """Load environment variables from a file."""
    path = Path(os.path.expandvars(env_file)).expanduser()
    if not path.exists():
        log.error(f"Warning: SOCIALIA_ENV_FILE not found: {path}")
        return

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                value = os.path.expandvars(value)
                os.environ[key] = value


# Load env file if specified
if env_file := os.environ.get("SOCIALIA_ENV_FILE"):
    _load_env_file(env_file)


# =============================================================================
# Platform Strategies (Resource)
# =============================================================================

PLATFORM_STRATEGIES = """
## PLATFORM CONTENT STRATEGIES

### Twitter/X (280 chars)
- Hook first: Lead with curiosity, controversy, or value (NOT announcements)
- Format: Short sentences. Line breaks. Visual hierarchy.
- Emoji: Use at least 1 emoji per tweet for visual appeal
- Links: ALWAYS include GitHub/project URL for discoverability
- Hashtags: 3-5 at the END. Mix broad + specific for reach.
- Avoid: "Just released", "Check out", "New version"

BAD:  "SciTeX v2.15.0 released! New audio relay. pip install scitex[audio] #Python #AI"
GOOD: "Your AI agent on a remote server can now speak to you locally.

Audio relay in SciTeX bridges the gap.

pip install scitex[audio]

#AIAgents #Python"

### LinkedIn (3,000 chars)
- Hook: First 2 lines visible before "see more" - make them count
- Format: Short paragraphs. Lots of whitespace.
- Hashtags: 3-5 at the END. Industry terms.
- CTA: End with a question

### Reddit
- Title is everything: Descriptive, specific, subreddit culture
- NO hashtags. Authentic tone. Value first, self-promo last.

### Slack
- Use channel mentions (@here, @channel) sparingly - they notify everyone
- Code blocks: Use triple backticks for technical content
- Threads: Keep discussions organized by replying in threads
- Links: Slack auto-unfurls URLs with previews
- Emoji reactions encouraged for engagement

### YouTube
- Title: Keyword-rich, <60 chars, curiosity-driven
- Hashtags: 3-5 in description
"""

MCP_INSTRUCTIONS = f"""
Socialia: Social Media Automation with Platform-Specific Strategies.

Posts to Twitter/X, LinkedIn, Reddit, Slack, and YouTube.
All MCP tool calls can be reproduced via CLI commands.

{PLATFORM_STRATEGIES}
"""


# =============================================================================
# FastMCP Server
# =============================================================================

mcp = FastMCP(name=get_mcp_server_name(), instructions=MCP_INSTRUCTIONS)


@mcp.tool()
def get_usage() -> str:
    """Get platform content strategies and usage guide for socialia."""
    return MCP_INSTRUCTIONS


# §5 audit-mcp-tools — every package's MCP server MUST expose
# skills_list + skills_get so agents can discover skill pages.
# Bare names (Convention A standalone source): the umbrella mounts with
# a namespace, so no `socialia_` prefix here. Skill tools are excluded
# from the §6 orphan check by the auditor.
@mcp.tool()
async def skills_list() -> dict:
    """List available skill pages for socialia."""
    from scitex_dev.ecosystem import list_skills

    return list_skills(package="socialia")


@mcp.tool()
async def skills_get(name: str | None = None) -> str | None:
    """Get a socialia skill page by name (or list when name is None)."""
    from scitex_dev.ecosystem import get_skill

    return get_skill(package="socialia", name=name)


@mcp.resource("socialia://strategies")
def get_strategies() -> str:
    """Platform content strategies for Twitter, LinkedIn, Reddit, YouTube."""
    return PLATFORM_STRATEGIES


# Register all tools from modules
register_all_tools(mcp)


# =============================================================================
# Server Entry Point
# =============================================================================


def run_server(transport: str = "stdio") -> None:
    """Run the MCP server."""
    mcp.run(transport=transport)


if __name__ == "__main__":
    run_server()

# EOF
