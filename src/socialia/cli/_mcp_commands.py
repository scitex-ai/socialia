#!/usr/bin/env python3
"""MCP CLI command handlers for socialia."""

import sys
import scitex_logging as slogging
log = slogging.getLogger(__name__)


def _style(text: str, fg: str = None, bold: bool = False) -> str:
    """Apply ANSI color styling."""
    if not sys.stdout.isatty():
        return text
    codes = {
        "green": "\033[32m",
        "cyan": "\033[36m",
        "yellow": "\033[33m",
        "magenta": "\033[35m",
        "white": "\033[37m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }
    prefix = ""
    if bold:
        prefix += codes["bold"]
    if fg and fg in codes:
        prefix += codes[fg]
    return f"{prefix}{text}{codes['reset']}" if prefix else text


def _get_tool_module(name: str) -> str:
    """Get logical module for a tool name."""
    if "social" in name:
        return "social"
    if "analytics" in name:
        return "analytics"
    return "general"


def _format_tool_signature(tool, compact: bool = False, indent: str = "  ") -> str:
    """Format tool as Python-like function signature with colors."""
    params = []
    if hasattr(tool, "parameters") and tool.parameters:
        schema = tool.parameters
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for name, info in props.items():
            ptype = info.get("type", "any")
            default = info.get("default")
            name_s = _style(name, "white", bold=True)
            type_s = _style(ptype, "cyan")
            if name in required:
                params.append(f"{name_s}: {type_s}")
            elif default is not None:
                def_str = repr(default) if len(repr(default)) < 20 else "..."
                def_s = _style(f"= {def_str}", "yellow")
                params.append(f"{name_s}: {type_s} {def_s}")
            else:
                def_s = _style("= None", "yellow")
                params.append(f"{name_s}: {type_s} {def_s}")

    name_s = _style(tool.name, "green")
    ret_type = f" -> {_style('dict', 'magenta')}"

    if compact or len(params) <= 2:
        return f"{indent}{name_s}({', '.join(params)}){ret_type}"
    else:
        param_indent = indent + "    "
        params_str = ",\n".join(f"{param_indent}{p}" for p in params)
        return f"{indent}{name_s}(\n{params_str}\n{indent}){ret_type}"


def cmd_mcp(args) -> int:
    """Handle MCP command."""
    from .._branding import get_env_var_name

    if args.mcp_command == "start":
        import asyncio
        from ..mcp_server import main as mcp_main, HAS_MCP

        if not HAS_MCP:
            log.error("Error: MCP package not installed. Run: pip install socialia[mcp]")
            return 1
        asyncio.run(mcp_main())
        return 0

    elif args.mcp_command == "doctor":
        from ..mcp_server import HAS_MCP
        from .. import __version__

        log.info(f"socialia {__version__}\n")
        log.info("Health Check")
        log.info("=" * 40)

        checks = []

        if HAS_MCP:
            try:
                import fastmcp
            except ImportError:
                checks.append(("fastmcp", False, "not installed"))
            else:
                checks.append(("fastmcp", True, fastmcp.__version__))
        else:
            checks.append(("fastmcp", False, "not installed"))

        # Check platform credentials
        from .._branding import get_env
        import shutil

        platforms = {
            "Twitter": ["X_CONSUMER_KEY", "X_ACCESSTOKEN"],
            "LinkedIn": ["LINKEDIN_ACCESS_TOKEN"],
            "Reddit": ["REDDIT_CLIENT_ID", "REDDIT_USERNAME"],
            "YouTube": ["YOUTUBE_CLIENT_SECRETS_FILE"],
            "Analytics": ["GOOGLE_ANALYTICS_MEASUREMENT_ID"],
        }
        for platform, keys in platforms.items():
            configured = all(get_env(k) for k in keys)
            checks.append(
                (platform, configured, "configured" if configured else "not configured")
            )

        cli_path = shutil.which("socialia")
        if cli_path:
            checks.append(("CLI", True, cli_path))
        else:
            checks.append(("CLI", False, "not in PATH"))

        all_ok = True
        for name, ok, info in checks:
            status = "✓" if ok else "✗"
            if not ok:
                all_ok = False
            log.info(f"  {status} {name}: {info}")

        return 0 if all_ok else 1

    elif args.mcp_command == "list-tools":
        verbose = getattr(args, "verbose", 0)
        compact = getattr(args, "compact", False)
        module_filter = getattr(args, "module", None)
        as_json = getattr(args, "json", False)

        try:
            from .._server import mcp
            from scitex_dev import get_tools_sync
        except ImportError:
            log.error("Error: MCP not installed. Run: pip install socialia[mcp]")
            return 1

        tools_map = get_tools_sync(mcp)
        tools = list(tools_map.keys())
        total = len(tools)

        # Group by logical module
        modules = {}
        for tool_name in sorted(tools):
            module = _get_tool_module(tool_name)
            if module not in modules:
                modules[module] = []
            modules[module].append(tool_name)

        # Filter by module if specified
        if module_filter:
            module_filter = module_filter.lower()
            if module_filter not in modules:
                log.info(f"ERROR: Unknown module '{module_filter}'")
                log.info(f"Available modules: {', '.join(sorted(modules.keys()))}")
                return 1
            modules = {module_filter: modules[module_filter]}

        if as_json:
            import json

            output = {
                "name": "socialia",
                "total": sum(len(t) for t in modules.values()),
                "modules": {},
            }
            for mod, tool_list in modules.items():
                output["modules"][mod] = {
                    "count": len(tool_list),
                    "tools": tool_list,
                }
            sys.stdout.write(json.dumps(output, indent=2) + "\n")
            return 0

        sys.stdout.write(_style("Socialia MCP: socialia", "cyan", bold=True) + "\n")
        sys.stdout.write(f"Tools: {total} ({len(modules)} modules)\n" + "\n")

        for module in sorted(modules.keys()):
            mod_tools = sorted(modules[module])
            sys.stdout.write(_style(f"{module}: {len(mod_tools)} tools", "green", bold=True) + "\n")
            for tool_name in mod_tools:
                tool_obj = tools_map.get(tool_name)

                if verbose == 0:
                    sys.stdout.write(f"  {tool_name}" + "\n")
                elif verbose == 1:
                    sig = (
                        _format_tool_signature(tool_obj, compact=compact)
                        if tool_obj
                        else f"  {tool_name}"
                    )
                    sys.stdout.write(sig + "\n")
                elif verbose == 2:
                    sig = (
                        _format_tool_signature(tool_obj, compact=compact)
                        if tool_obj
                        else f"  {tool_name}"
                    )
                    sys.stdout.write(sig + "\n")
                    if tool_obj and tool_obj.description:
                        desc = tool_obj.description.split("\n")[0].strip()
                        sys.stdout.write(f"    {desc}" + "\n")
                    sys.stdout.write("\n")
                else:
                    sig = (
                        _format_tool_signature(tool_obj, compact=compact)
                        if tool_obj
                        else f"  {tool_name}"
                    )
                    sys.stdout.write(sig + "\n")
                    if tool_obj and tool_obj.description:
                        for line in tool_obj.description.strip().split("\n"):
                            sys.stdout.write(f"    {line}" + "\n")
                    sys.stdout.write("\n")
            sys.stdout.write("\n")

        return 0

    elif args.mcp_command == "installation":
        from .. import __version__
        import shutil

        log.info(f"socialia {__version__}\n")
        log.info("Add this to your Claude Desktop config file:\n")
        log.info("  macOS: ~/Library/Application Support/Claude/claude_desktop_config.json")
        log.info("  Linux: ~/.config/Claude/claude_desktop_config.json\n")

        cli_path = shutil.which("socialia")
        if cli_path:
            log.info(f"Your installation path: {cli_path}\n")

        config = f'''{{
  "mcpServers": {{
    "socialia": {{
      "command": "socialia",
      "args": ["mcp", "start"],
      "env": {{
        "{get_env_var_name("X_CONSUMER_KEY")}": "...",
        "{get_env_var_name("X_CONSUMER_KEY_SECRET")}": "...",
        "{get_env_var_name("X_ACCESSTOKEN")}": "...",
        "{get_env_var_name("X_ACCESSTOKEN_SECRET")}": "..."
      }}
    }}
  }}
}}'''
        sys.stdout.write(config + "\n")
        return 0

    else:
        log.error("Usage: socialia mcp {start|doctor|list-tools|installation}")
        return 1


def add_mcp_parser(subparsers) -> None:
    """Register MCP subcommand parser."""
    import argparse

    mcp_parser = subparsers.add_parser(
        "mcp",
        help="MCP server commands",
        description="Model Context Protocol server operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_command", help="MCP operations")

    mcp_sub.add_parser("start", help="Start the MCP server")
    mcp_sub.add_parser("doctor", help="Check MCP server health")

    lst = mcp_sub.add_parser(
        "list-tools",
        help="List available MCP tools",
        description="Verbosity: (none) names, -v sig, -vv +desc, -vvv full",
    )
    lst.add_argument("-v", "--verbose", action="count", default=0)
    lst.add_argument("-c", "--compact", action="store_true")
    lst.add_argument("-m", "--module", type=str, default=None)
    lst.add_argument("--json", action="store_true", default=False)

    mcp_sub.add_parser("installation", help="Show Claude Desktop configuration")
