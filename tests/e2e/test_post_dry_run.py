"""E2E: dry-run post end to end (gated by RUN_E2E=1, loopback only)."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("RUN_E2E") != "1",
        reason="needs RUN_E2E=1",
    ),
]


def test_dry_run_post_twitter_exits_zero(env_save_restore, tmp_path):
    # Arrange — isolated state dir, blank credential so no real env leaks in.
    env_save_restore.set("SCITEX_DIR", str(tmp_path))
    env_save_restore.set("SOCIALIA_X_CONSUMER_KEY", " ")
    # Act
    proc = subprocess.run(
        [sys.executable, "-m", "socialia", "post", "twitter", "Hello", "--dry-run"],
        capture_output=True,
        text=True,
        timeout=55,
    )
    # Assert
    assert proc.returncode == 0


def test_dry_run_post_twitter_echoes_text(env_save_restore, tmp_path):
    # Arrange — isolated state dir, blank credential so no real env leaks in.
    env_save_restore.set("SCITEX_DIR", str(tmp_path))
    env_save_restore.set("SOCIALIA_X_CONSUMER_KEY", " ")
    # Act
    proc = subprocess.run(
        [sys.executable, "-m", "socialia", "post", "twitter", "Hello", "--dry-run"],
        capture_output=True,
        text=True,
        timeout=55,
    )
    # Assert
    assert "Hello" in proc.stdout
