"""Docs must identify their checkout without importing Socialia runtime code."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("launch_from_conf_dir", [False, True])
def test_documented_version_belongs_to_selected_checkout(tmp_path, launch_from_conf_dir):
    # Arrange
    # The synthetic version differs from both the repository and installed package.
    checkout = tmp_path / "selected checkout"
    conf_dir = checkout / "docs/sphinx"
    conf_dir.mkdir(parents=True)
    (checkout / "src").mkdir()
    conf = conf_dir / "conf.py"
    conf.write_bytes((ROOT / "docs/sphinx/conf.py").read_bytes())
    (checkout / "pyproject.toml").write_text('[project]\nversion = "7.8.9"\n')
    launch_dir = conf_dir if launch_from_conf_dir else tmp_path
    code = (
        "import json,runpy,sys; "
        "config=runpy.run_path(sys.argv[1]); "
        "print(json.dumps({'release':config['release'], 'source':sys.path[0], "
        "'title':config['html_title'], "
        "'runtime_imported':any(n=='socialia' or n.startswith('socialia.') "
        "for n in sys.modules)}))"
    )
    # Act
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(conf)],
        cwd=launch_dir, capture_output=True, text=True, timeout=30,
    )
    # Assert
    observed = json.loads(result.stdout) if result.returncode == 0 else None
    assert (result.returncode, observed) == (0, {
        "release": "7.8.9", "source": str(checkout / "src"),
        "title": "Socialia v7.8.9", "runtime_imported": False,
    }), result.stdout + result.stderr
