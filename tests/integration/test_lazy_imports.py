"""Fresh-process checks for public exports and metadata-only CLI startup."""

import json
import os
import subprocess
import sys
from pathlib import Path


def _probe(tmp_path, code):
    source = Path(__file__).resolve().parents[2] / "src"
    environment = {
        "PATH": os.environ.get("PATH", os.defpath),
        "HOME": str(tmp_path),
        "SCITEX_DIR": str(tmp_path / "state"),
        "PYTHONPATH": os.pathsep.join(
            filter(None, (str(source), os.environ.get("PYTHONPATH", "")))
        ),
    }
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    return json.loads(result.stdout)


def test_plain_import_does_not_construct_the_mcp_registry(tmp_path):
    # Arrange
    code = """
import json,sys,socialia
print(json.dumps(sorted(name for name in sys.modules
    if name in {'fastmcp','socialia._server','socialia.twitter','socialia.analytics'})))
"""
    # Act
    imported = _probe(tmp_path, code)
    # Assert
    assert imported == []


def test_setup_json_does_not_construct_the_mcp_registry(tmp_path):
    # Arrange
    code = """
import contextlib,io,json,sys
from socialia.cli import main
output=io.StringIO()
with contextlib.redirect_stdout(output):
    status=main(['mcp','show-installation','--json'])
print(json.dumps([status,json.loads(output.getvalue())['mcpServers']['socialia']['args'],
    'fastmcp' in sys.modules,'socialia._server' in sys.modules]))
"""
    # Act
    result = _probe(tmp_path, code)
    # Assert
    assert result == [0, ["mcp", "start"], False, False]


def test_public_exports_keep_identity_cache_and_discovery(tmp_path):
    # Arrange
    code = """
import importlib,json,socialia
owners={'Twitter':'twitter','LinkedIn':'linkedin','Reddit':'reddit','Slack':'slack',
    'YouTube':'youtube','GoogleAnalytics':'analytics','move_to_scheduled':'org_files',
    'move_to_posted':'org_files','ensure_project_dirs':'org_files'}
identical=all(getattr(socialia,name) is getattr(importlib.import_module('socialia.'+module),name)
    for name,module in owners.items())
print(json.dumps([identical,all(name in socialia.__dict__ for name in owners),
    set(socialia.__all__) <= set(dir(socialia)),isinstance(socialia.__version__,str),
    getattr(socialia,'not_a_public_export',None) is None]))
"""
    # Act
    result = _probe(tmp_path, code)
    # Assert
    assert result == [True, True, True, True, True]


def test_explicit_strategy_access_retains_the_provider_text(tmp_path):
    # Arrange
    code = """
import json,socialia
from socialia._server import PLATFORM_STRATEGIES
value=socialia.PLATFORM_STRATEGIES
print(json.dumps([value is PLATFORM_STRATEGIES,isinstance(value,str),
    socialia.__dict__['PLATFORM_STRATEGIES'] is value]))
"""
    # Act
    result = _probe(tmp_path, code)
    # Assert
    assert result == [True, True, True]
