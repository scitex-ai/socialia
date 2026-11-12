"""Installation metadata is portable JSON without credential values."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _invoke(tmp_path, command, as_json):
    source = Path(__file__).resolve().parents[1] / "src"
    environment = {
        "PATH": os.environ.get("PATH", os.defpath),
        "HOME": str(tmp_path),
        "SCITEX_DIR": str(tmp_path / "state"),
        "PYTHONPATH": os.pathsep.join(
            filter(None, (str(source), os.environ.get("PYTHONPATH", "")))
        ),
        "LANG": "C.UTF-8",
        "SOCIALIA_X_CONSUMER_KEY": "owned-canary-not-for-export",
        "COVERAGE_FILE": str(tmp_path / ".coverage"),
    }
    arguments = [sys.executable, "-m", "socialia", "mcp", command]
    if as_json:
        arguments.append("--json")
    return subprocess.run(
        arguments,
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


@pytest.mark.parametrize("command", ["show-installation", "installation"])
def test_json_installation_is_a_client_configuration(tmp_path, command):
    # Arrange
    as_json = True
    # Act
    result = _invoke(tmp_path, command, as_json)
    config = json.loads(result.stdout)
    server = config["mcpServers"]["socialia"]
    # Assert
    assert (
        result.returncode,
        set(config),
        set(config["mcpServers"]),
        set(server),
        server["command"],
        server["args"],
    ) == (
        0,
        {"mcpServers"},
        {"socialia"},
        {"command", "args", "env"},
        "socialia",
        ["mcp", "start"],
    )


def test_json_contains_placeholders_instead_of_environment_credentials(tmp_path):
    # Arrange
    expected_placeholder = "..."
    # Act
    result = _invoke(tmp_path, "show-installation", True)
    values = json.loads(result.stdout)["mcpServers"]["socialia"]["env"]
    # Assert
    assert (
        result.returncode,
        len(values),
        set(values.values()),
        "owned-canary-not-for-export" in result.stdout,
    ) == (0, 4, {expected_placeholder}, False)


def test_plain_installation_keeps_the_human_readable_instructions(tmp_path):
    # Arrange
    expected_text = "Add this to your Claude Desktop config file:"
    # Act
    result = _invoke(tmp_path, "show-installation", False)
    # Assert
    assert (
        result.returncode,
        expected_text in result.stdout,
        '"mcpServers"' in result.stdout,
    ) == (0, True, True)
