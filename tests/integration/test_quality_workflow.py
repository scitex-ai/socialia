"""Quality preparation preserves the selected source in real Git checkouts."""

import os
import subprocess
from pathlib import Path

import pytest
import yaml

WORKFLOW = (
    Path(__file__).resolve().parents[2]
    / ".github/workflows/quality-audit-on-ubuntu-latest.yml"
)


def _environment():
    return {
        "PATH": os.environ.get("PATH", os.defpath),
        "LANG": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_AUTHOR_NAME": "Owned Git fixture",
        "GIT_COMMITTER_NAME": "Owned Git fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    }


def _git(cwd, *arguments):
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        env=_environment(),
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.strip()


@pytest.fixture
def git_checkout(tmp_path):
    remote, seed, checkout = [
        tmp_path / name for name in ["origin.git", "seed", "checkout"]
    ]
    _git(tmp_path, "init", "--bare", "--template=", str(remote))
    _git(tmp_path, "init", "--template=", str(seed))
    _git(seed, "branch", "-M", "develop")
    (seed / "payload.txt").write_text("initial\n")
    _git(seed, "add", "payload.txt")
    _git(seed, "commit", "-qm", "Initial owned fixture")
    _git(seed, "remote", "add", "origin", str(remote))
    _git(seed, "push", "origin", "develop")
    _git(tmp_path, "clone", "--branch", "develop", str(remote), str(checkout))
    return seed, checkout


@pytest.fixture
def advanced_checkout(git_checkout):
    seed, checkout = git_checkout
    selected = _git(checkout, "rev-parse", "HEAD")
    (seed / "payload.txt").write_text("new baseline\n")
    _git(seed, "commit", "-qam", "Advance owned baseline")
    _git(seed, "push", "origin", "develop")
    latest = _git(seed, "rev-parse", "HEAD")
    return checkout, selected, latest


def _prepare_and_stage(tmp_path, checkout):
    workflow = yaml.safe_load(WORKFLOW.read_text())
    step = next(
        s
        for s in workflow["jobs"]["audit"]["steps"]
        if s.get("name", "").startswith("Ensure local")
    )
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=checkout,
        env=_environment(),
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    _git(
        checkout, "worktree", "add", "--detach", str(tmp_path / "audit-base"), "develop"
    )
    return (
        result.returncode,
        _git(checkout, "rev-parse", "HEAD"),
        _git(tmp_path / "audit-base", "rev-parse", "HEAD"),
        result.stderr,
    )


def test_checked_out_develop_preserves_the_selected_source(tmp_path, advanced_checkout):
    # Arrange
    checkout, selected, _ = advanced_checkout
    # Act
    code, source, baseline, stderr = _prepare_and_stage(tmp_path, checkout)
    # Assert
    assert (code, source, baseline) == (0, selected, selected), stderr


@pytest.mark.parametrize(
    "checkout_args",
    [
        ["checkout", "--detach", "--quiet"],
        ["checkout", "--quiet", "-b", "feature"],
    ],
)
def test_nonbaseline_checkout_materializes_remote_develop(
    tmp_path, advanced_checkout, checkout_args
):
    # Arrange
    checkout, selected, latest = advanced_checkout
    _git(checkout, *checkout_args)
    # Act
    code, source, baseline, stderr = _prepare_and_stage(tmp_path, checkout)
    # Assert
    assert (code, source, baseline) == (0, selected, latest), stderr


def test_changes_to_the_actual_workflow_trigger_the_quality_gate():
    # Arrange
    workflow = yaml.safe_load(WORKFLOW.read_text())
    # Act
    triggers = workflow.get("on", workflow.get(True))
    # Assert
    assert ".github/workflows/" + WORKFLOW.name in triggers["push"]["paths"]
