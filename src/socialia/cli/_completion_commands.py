#!/usr/bin/env python3
"""Completion CLI command handlers for socialia.

Fleet standard: completion drop-in contract v1. ``install`` writes the
static completion script to ``~/.scitex/socialia/runtime/completion/``
(dotfiles discovers the drop-in) and never touches shell rc files.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .._paths import get_completion_dir as _get_completion_dir


def _completion_dir() -> Path:
    """Resolve the drop-in directory at call time (honours SCITEX_DIR)."""
    return _get_completion_dir()


#: Drop-in filenames per shell (contract v1: ``<cmd>`` under the package
#: runtime completion dir).
_DROPIN_NAMES = {"bash": "socialia", "zsh": "socialia"}


def _dropin_path(shell: str) -> Path:
    """Return the canonical drop-in path for *shell*."""
    return _completion_dir() / _DROPIN_NAMES[shell]


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


def _atomic_write(path: Path, content: str) -> None:
    """Write *content* to *path* atomically (tmp + os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def cmd_completion(args, output_json: bool = False) -> int:
    """Handle completion command."""

    if args.completion_command == "bash":
        sys.stdout.write(_get_bash_script())
        return 0

    elif args.completion_command == "zsh":
        sys.stdout.write(_get_zsh_script())
        return 0

    elif args.completion_command == "install":
        return _install_completion(args, output_json)

    elif args.completion_command == "status":
        return _show_status(output_json)

    else:
        sys.stderr.write("Usage: socialia completion {bash|zsh|install|status}\n")
        return 1


def _install_completion(args, output_json: bool = False) -> int:
    """Install the completion drop-in (contract v1).

    Writes ``$HOME/.scitex/socialia/runtime/completion/socialia``
    atomically and idempotently, then prints the path. Never touches
    shell rc files — sourcing is owned by the dotfiles drop-in
    discovery rail.
    """
    shell = getattr(args, "shell", None)
    if not shell:
        # Auto-detect shell
        shell_path = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell_path:
            shell = "zsh"
        else:
            shell = "bash"

    if shell not in _DROPIN_NAMES:
        if output_json:
            sys.stdout.write(json.dumps({"shell": shell, "installed": False,
                                          "error": f"unsupported shell: {shell}"}))
        else:
            sys.stderr.write(f"Unsupported shell: {shell}\n")
        return 1

    script = _get_zsh_script() if shell == "zsh" else _get_bash_script()
    target = _dropin_path(shell)
    _atomic_write(target, script)

    results = {"shell": shell, "installed": True, "files": [str(target)],
               "path": str(target)}

    if output_json:
        sys.stdout.write(json.dumps(results, indent=2) + "\n")
    else:
        sys.stdout.write(str(target) + "\n")

    return 0


def _show_status(output_json: bool = False) -> int:
    """Show completion drop-in status (checks the drop-in file)."""
    status = {
        "argcomplete_installed": shutil.which("register-python-argcomplete")
        is not None,
        "bash": {
            "completion_file": str(_dropin_path("bash")),
            "installed": _dropin_path("bash").exists(),
        },
        "zsh": {
            "completion_file": str(_dropin_path("zsh")),
            "installed": _dropin_path("zsh").exists(),
        },
        "current_shell": os.environ.get("SHELL", "unknown"),
    }

    if output_json:
        sys.stdout.write(json.dumps(status, indent=2) + "\n")
    else:
        sys.stdout.write("Socialia Completion Status\n")
        sys.stdout.write("=" * 40 + "\n")
        sys.stdout.write("\n")
        sys.stdout.write(f"Current shell: {status['current_shell']}\n")
        sys.stdout.write(
            f"argcomplete:   {'installed' if status['argcomplete_installed'] else 'NOT INSTALLED'}\n"
        )
        sys.stdout.write("\n")
        sys.stdout.write("Bash:\n")
        sys.stdout.write(f"  File: {status['bash']['completion_file']}\n")
        sys.stdout.write(
            f"  Status: {'installed' if status['bash']['installed'] else 'not installed'}\n"
        )
        sys.stdout.write("\n")
        sys.stdout.write("Zsh:\n")
        sys.stdout.write(f"  File: {status['zsh']['completion_file']}\n")
        sys.stdout.write(
            f"  Status: {'installed' if status['zsh']['installed'] else 'not installed'}\n"
        )
        sys.stdout.write("\n")
        sys.stdout.write(
            "Sourcing is owned by the dotfiles drop-in discovery rail;\n"
            "this command never modifies shell rc files.\n"
        )
        sys.stdout.write("\n")
        if not status["argcomplete_installed"]:
            sys.stdout.write("Note: Install argcomplete for dynamic completion:\n")
            sys.stdout.write("  pip install argcomplete\n")

    return 0
