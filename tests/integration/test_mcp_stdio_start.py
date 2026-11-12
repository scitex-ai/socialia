"""Initialize the real CLI stdio server without invoking platform tools."""

import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_cli_stdio_initializes_and_lists_registered_tools(tmp_path):
    # Arrange
    source = Path(__file__).resolve().parents[2] / "src"
    expected = {
        "social_post",
        "social_delete",
        "social_status",
        "usage",
        "social_analytics_track",
        "social_analytics_pageviews",
        "social_analytics_sources",
        "social_analytics_realtime",
    }
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "socialia", "mcp", "start"],
        env={
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(tmp_path),
            "SCITEX_DIR": str(tmp_path / "state"),
            "PYTHONPATH": os.pathsep.join(
                filter(None, (str(source), os.environ.get("PYTHONPATH", "")))
            ),
        },
        cwd=tmp_path,
    )

    async def collect_names():
        with (tmp_path / "server.log").open("w") as errors:
            async with (
                stdio_client(parameters, errlog=errors) as (read, write),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                response = await session.list_tools()
                return {tool.name for tool in response.tools}

    # Act
    names = asyncio.run(asyncio.wait_for(collect_names(), timeout=30))
    # Assert
    assert names == expected
