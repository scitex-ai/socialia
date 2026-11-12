"""Exercise the release install block with inert local command processes."""

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[2] / ".github/ci/run-in-sif.sh"


def _install(tmp_path, status):
    script = HELPER.read_text()
    start = script.index('\nuv pip install --python "$VENV/bin/python"') + 1
    end = script.index("\nexport PYTHONPATH=", start)
    command_dir = tmp_path / "bin"
    command_dir.mkdir()
    command = command_dir / "installer"
    command.write_text(
        f"#!/bin/sh\n'''exec' {shlex.quote(sys.executable)} \"$0\" \"$@\"\n' '''\n"
        "import json,os,sys\nfrom pathlib import Path\n"
        "name=Path(sys.argv[0]).name\n"
        "with open(os.environ['CALLS'],'a') as stream:\n"
        " stream.write(json.dumps([name,sys.argv[1:]])+'\\n')\n"
        "raise SystemExit(int(os.environ['INSTALL_EXIT']) if name=='uv' else 0)\n"
    )
    command.chmod(0o700)
    for name in ["uv", "pip"]:
        (command_dir / name).symlink_to(command.name)
    calls = tmp_path / "calls.jsonl"
    reached = tmp_path / "next-step"
    environment = {
        "PATH": str(command_dir) + os.pathsep + os.defpath,
        "VENV": str(tmp_path / "venv"),
        "TMPDIR": str(tmp_path / "scratch"),
        "CALLS": str(calls),
        "INSTALL_EXIT": str(status),
        "NEXT_STEP": str(reached),
    }
    result = subprocess.run(
        [
            "bash",
            "-c",
            "set -euo pipefail\n"
            + script[start:end]
            + '\nprintf ready > "$NEXT_STEP"\n',
        ],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    recorded = [json.loads(line) for line in calls.read_text().splitlines()]
    return result.returncode, recorded, reached.exists()


@pytest.mark.parametrize("status", [0, 17])
def test_release_profile_failure_cannot_fall_back_to_reduced_extras(tmp_path, status):
    # Arrange
    expected = [
        [
            "uv",
            [
                "pip",
                "install",
                "--python",
                str(tmp_path / "venv/bin/python"),
                "--target=" + str(tmp_path / "scratch/site"),
                "-e",
                ".[all,dev]",
            ],
        ]
    ]
    # Act
    code, calls, reached = _install(tmp_path, status)
    # Assert
    assert (code, calls, reached) == (status, expected, status == 0)
