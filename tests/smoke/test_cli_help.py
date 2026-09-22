"""Smoke: the installed CLI answers `--help` in a subprocess (<60s)."""

from __future__ import annotations

import subprocess
import sys

import pytest

pytestmark = pytest.mark.smoke


def _run(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "socialia", *argv],
        capture_output=True,
        text=True,
        timeout=50,
    )


def test_cli_top_level_help_exits_zero(env_save_restore, tmp_path):
    # Arrange — isolated state dir, blank credential so no real env leaks in.
    env_save_restore.set("SCITEX_DIR", str(tmp_path))
    env_save_restore.set("SOCIALIA_X_CONSUMER_KEY", " ")
    # Act
    proc = _run("--help")
    # Assert
    assert proc.returncode == 0


def test_cli_top_level_help_lists_post_command(env_save_restore, tmp_path):
    # Arrange — isolated state dir, blank credential so no real env leaks in.
    env_save_restore.set("SCITEX_DIR", str(tmp_path))
    env_save_restore.set("SOCIALIA_X_CONSUMER_KEY", " ")
    # Act
    proc = _run("--help")
    # Assert
    assert "post" in proc.stdout
