#!/usr/bin/env python3
"""Completion CLI command handlers for socialia."""

import os
import subprocess
import sys
from pathlib import Path

from .._paths import get_completion_dir as _get_completion_dir
import scitex_logging as slogging
log = slogging.getLogger(__name__)


BASH_COMPLETION_DIR = _get_completion_dir()
ZSH_COMPLETION_DIR = _get_completion_dir()


def _get_bash_script() -> str:
    """Generate bash completion script using argcomplete."""
    try:
        result = subprocess.run(
            ["register-python-argcomplete", "socialia"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: generate manually
        return """# Bash completion for socialia (argcomplete)
eval "$(register-python-argcomplete socialia)"
"""


def _get_zsh_script() -> str:
    """Generate zsh completion script."""
    return """#compdef socialia
# Zsh completion for socialia

# Use bashcompinit for argcomplete compatibility
autoload -U bashcompinit
bashcompinit

eval "$(register-python-argcomplete socialia)"
"""


def cmd_completion(args, output_json: bool = False) -> int:
    """Handle completion command."""

    if args.completion_command == "bash":
        sys.stdout.write(_get_bash_script() + "\n")
        return 0

    elif args.completion_command == "zsh":
        sys.stdout.write(_get_zsh_script() + "\n")
        return 0

    elif args.completion_command == "install":
        return _install_completion(args, output_json)

    elif args.completion_command == "status":
        return _show_status(output_json)

    else:
        log.error("Usage: socialia completion {bash|zsh|install|status}")
        return 1


def _install_completion(args, output_json: bool = False) -> int:
    """Install completion to shell configuration."""
    import json

    shell = getattr(args, "shell", None)
    if not shell:
        # Auto-detect shell
        shell_path = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell_path:
            shell = "zsh"
        else:
            shell = "bash"

    results = {"shell": shell, "installed": False, "files": []}

    if shell == "bash":
        # Create completion directory
        BASH_COMPLETION_DIR.mkdir(parents=True, exist_ok=True)
        completion_file = BASH_COMPLETION_DIR / "socialia.bash"

        # Write completion script
        completion_file.write_text(_get_bash_script())
        results["files"].append(str(completion_file))

        # Check if sourced in bashrc
        bashrc = Path.home() / ".bashrc"
        source_line = f'[[ -f "{completion_file}" ]] && source "{completion_file}"'

        if bashrc.exists():
            content = bashrc.read_text()
            if str(completion_file) not in content:
                # Add source line
                with bashrc.open("a") as f:
                    f.write(f"\n# Socialia completion\n{source_line}\n")
                results["bashrc_updated"] = True
            else:
                results["bashrc_updated"] = False
        else:
            results["bashrc_updated"] = False

        results["installed"] = True

    elif shell == "zsh":
        # Create completion directory
        ZSH_COMPLETION_DIR.mkdir(parents=True, exist_ok=True)
        completion_file = ZSH_COMPLETION_DIR / "_socialia"

        # Write completion script
        completion_file.write_text(_get_zsh_script())
        results["files"].append(str(completion_file))

        # Check if fpath includes our directory
        zshrc = Path.home() / ".zshrc"
        fpath_line = f'fpath=("{ZSH_COMPLETION_DIR}" $fpath)'

        if zshrc.exists():
            content = zshrc.read_text()
            if str(ZSH_COMPLETION_DIR) not in content:
                with zshrc.open("a") as f:
                    f.write(
                        f"\n# Socialia completion\n{fpath_line}\nautoload -Uz compinit && compinit\n"
                    )
                results["zshrc_updated"] = True
            else:
                results["zshrc_updated"] = False
        else:
            results["zshrc_updated"] = False

        results["installed"] = True

    if output_json:
        sys.stdout.write(json.dumps(results, indent=2) + "\n")
    else:
        if results["installed"]:
            log.info(f"Installed {shell} completion:")
            for f in results["files"]:
                log.info(f"  {f}")
            if results.get("bashrc_updated") or results.get("zshrc_updated"):
                log.info(f"\nRestart your shell or run: source ~/.{shell}rc")
            else:
                log.info("\nShell config already configured.")
        else:
            log.error(f"Failed to install {shell} completion")
            return 1

    return 0


def _show_status(output_json: bool = False) -> int:
    """Show completion installation status."""
    import json
    import shutil

    status = {
        "argcomplete_installed": shutil.which("register-python-argcomplete")
        is not None,
        "bash": {
            "completion_file": str(BASH_COMPLETION_DIR / "socialia.bash"),
            "installed": (BASH_COMPLETION_DIR / "socialia.bash").exists(),
        },
        "zsh": {
            "completion_file": str(ZSH_COMPLETION_DIR / "_socialia"),
            "installed": (ZSH_COMPLETION_DIR / "_socialia").exists(),
        },
        "current_shell": os.environ.get("SHELL", "unknown"),
    }

    if output_json:
        sys.stdout.write(json.dumps(status, indent=2) + "\n")
    else:
        log.info("Socialia Completion Status")
        log.info("=" * 40)
        log.info("")
        log.info(f"Current shell: {status['current_shell']}")
        log.info(f"argcomplete:   {'installed' if status['argcomplete_installed'] else 'NOT INSTALLED'}")
        log.info("")
        log.info("Bash:")
        log.info(f"  File: {status['bash']['completion_file']}")
        log.info(f"  Status: {'installed' if status['bash']['installed'] else 'not installed'}")
        log.info("")
        log.info("Zsh:")
        log.info(f"  File: {status['zsh']['completion_file']}")
        log.info(f"  Status: {'installed' if status['zsh']['installed'] else 'not installed'}")
        log.info("")
        if not status["argcomplete_installed"]:
            log.info("Note: Install argcomplete for dynamic completion:")
            log.info("  pip install argcomplete")

    return 0
