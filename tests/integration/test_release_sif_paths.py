"""Exercise the outer release wrapper without a container or shared filesystem."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

WRAPPER = Path(__file__).resolve().parents[2] / ".github/ci/exec-in-sif.sh"


@pytest.fixture
def wrapper_case(tmp_path):
    """Own every executable, path and recorded effect used by the wrapper."""
    commands = tmp_path / "bin with spaces"
    commands.mkdir()
    recorder = commands / "record"
    recorder.write_text(
        f"#!{sys.executable}\n"
        "import json,os,sys\nfrom pathlib import Path\n"
        "root=Path(os.environ['OWNED_ROOT']).resolve()\n"
        "if Path(sys.argv[0]).name=='mkdir':\n"
        " for value in sys.argv[1:]:\n"
        "  if value.startswith('-'):continue\n"
        "  path=Path(value).resolve()\n"
        "  if root not in path.parents:raise SystemExit(93)\n"
        "  path.mkdir(parents=True,exist_ok=True)\n"
        "else:\n"
        " Path(os.environ['CALLS']).write_text(json.dumps({\n"
        "  'argv':sys.argv[1:],'path':os.environ['PATH'],\n"
        "  'tmp':os.environ.get('APPTAINER_TMPDIR'),\n"
        "  'bind':os.environ.get('APPTAINER_BINDPATH')}))\n"
    )
    recorder.chmod(0o700)
    for name in ("mkdir", "apptainer"):
        (commands / name).symlink_to(recorder.name)
    image = tmp_path / "image with spaces.sif"
    image.write_text("owned inert image")
    calls = tmp_path / "calls.json"
    env = {
        "PATH": str(commands) + os.pathsep + os.defpath,
        "HOME": str(tmp_path),
        "OWNED_ROOT": str(tmp_path),
        "CALLS": str(calls),
        "SCITEX_CI_APPTAINER": str(commands / "apptainer"),
        "SCITEX_CI_SIF": str(image),
        "RUNNER_TEMP": str(tmp_path / "runner temp"),
    }

    def run(overrides=None):
        current = {**env, **(overrides or {})}
        result = subprocess.run(
            ["bash", str(WRAPPER), "run-in-sif.sh", "3.12"],
            cwd=tmp_path,
            env=current,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        recorded = json.loads(calls.read_text()) if calls.exists() else None
        return result, recorded, current

    return run


def test_wrapper_uses_configured_executable_and_image_as_separate_arguments(
    wrapper_case,
):
    # Arrange
    run = wrapper_case
    # Act
    result, recorded, env = run()
    # Assert
    assert (result.returncode, recorded and recorded["argv"]) == (
        0,
        [
            "exec",
            "--pwd",
            env["OWNED_ROOT"],
            env["SCITEX_CI_SIF"],
            "bash",
            ".github/ci/run-in-sif.sh",
            "3.12",
        ],
    )


def test_wrapper_uses_runner_scratch_instead_of_a_personal_mount(wrapper_case):
    # Arrange
    run = wrapper_case
    # Act
    result, recorded, env = run()
    # Assert
    assert (result.returncode, recorded and recorded["tmp"]) == (
        0,
        str(Path(env["RUNNER_TEMP"]) / "scitex-socialia-apptainer"),
    )


def test_wrapper_preserves_an_explicit_scratch_directory(wrapper_case, tmp_path):
    # Arrange
    scratch = str(tmp_path / "explicit scratch")
    # Act
    result, recorded, _ = wrapper_case({"APPTAINER_TMPDIR": scratch})
    # Assert
    assert (result.returncode, recorded and recorded["tmp"]) == (0, scratch)


@pytest.mark.parametrize(
    "bindings",
    [
        {"APPTAINER_BINDPATH": "/shared:/mnt"},
        {"SCITEX_CI_BINDPATH": "/configured:/mnt"},
    ],
)
def test_wrapper_passes_only_configured_bindings(wrapper_case, bindings):
    # Arrange
    expected = next(iter(bindings.values()))
    # Act
    result, recorded, _ = wrapper_case(bindings)
    # Assert
    assert (result.returncode, recorded and recorded["bind"]) == (0, expected)


@pytest.mark.parametrize("missing", ["SCITEX_CI_APPTAINER", "SCITEX_CI_SIF"])
def test_wrapper_refuses_missing_required_runtime_paths(wrapper_case, missing):
    # Arrange
    invalid = {missing: "/nonexistent/owned-release-runtime"}
    # Act
    result, recorded, _ = wrapper_case(invalid)
    # Assert
    assert result.returncode != 0 and recorded is None
