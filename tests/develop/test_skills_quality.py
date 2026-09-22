"""Enforces SciTeX skills quality checklist §1–§4.
Canonical: src/scitex/_skills/general/21_scitex-package-quality-checklist.md
"""
from pathlib import Path
from scitex_dev._skills_quality_pytest import make_skill_quality_tests

test_skills_quality = make_skill_quality_tests(
    package_root=Path(__file__).resolve().parents[2]
)


def test_skills_quality_gate_finds_packaged_skills():
    # Arrange — the gate scans the packaged skill dirs under src/.
    skills_root = (
        Path(__file__).resolve().parents[2] / "src" / "socialia" / "_skills"
    )
    # Act
    found = sorted(p for p in skills_root.iterdir() if p.is_dir())
    # Assert
    assert found, f"no skill dirs under {skills_root}"
