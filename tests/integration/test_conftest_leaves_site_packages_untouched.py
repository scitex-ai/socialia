"""Regression: importing tests/conftest.py must not touch site-packages.

Subprocess coverage is configured declaratively in pyproject.toml
(``patch = ["subprocess"]``); collecting tests must neither install ``.pth``
hooks into shared site-packages nor overwrite caller-owned coverage
environment variables.
"""

import subprocess
import sys
from pathlib import Path


def test_conftest_runpy_leaves_site_packages_and_coverage_env_untouched():
    # Arrange
    conftest = Path(__file__).resolve().parents[1] / "conftest.py"
    child = (
        "import os, runpy, site\n"
        "os.environ['COVERAGE_PROCESS_START'] = 'sentinel-process-start'\n"
        "os.environ['COVERAGE_FILE'] = 'sentinel-coverage-file'\n"
        "def _dirs():\n"
        "    ds = []\n"
        "    try:\n"
        "        ds.extend(site.getsitepackages())\n"
        "    except AttributeError:\n"
        "        pass\n"
        "    u = site.getusersitepackages()\n"
        "    ds.extend([u] if isinstance(u, str) else list(u))\n"
        "    return [d for d in dict.fromkeys(ds) if os.path.isdir(d)]\n"
        "def _snap():\n"
        "    return dict((d, sorted(os.listdir(d))) for d in _dirs())\n"
        "before = _snap()\n"
        "runpy.run_path(" + repr(str(conftest)) + ", run_name='probe')\n"
        "after = _snap()\n"
        "assert before == after, 'conftest modified site-packages'\n"
        "assert os.environ.get('COVERAGE_PROCESS_START') == 'sentinel-process-start'\n"
        "assert os.environ.get('COVERAGE_FILE') == 'sentinel-coverage-file'\n"
    )
    # Act
    result = subprocess.run(
        [sys.executable, "-c", child],
        text=True,
        capture_output=True,
        timeout=120,
    )
    # Assert
    assert result.returncode == 0
