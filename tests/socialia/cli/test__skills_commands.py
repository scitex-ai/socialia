"""Tests for `socialia skills` (list / get / install)."""

from socialia.cli import main


# --- skills list -----------------------------------------------------------


class TestSkillsList:
    def test_skills_list_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["skills", "list"])
        # Assert
        assert result == 0

    def test_skills_list_output_names_bundled_skill(self, capsys):
        # Arrange
        main(["skills", "list"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "01_installation" in out


# --- skills get ------------------------------------------------------------


class TestSkillsGet:
    def test_skills_get_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["skills", "get", "01_installation"])
        # Assert
        assert result == 0

    def test_skills_get_output_contains_skill_body(self, capsys):
        # Arrange
        main(["skills", "get", "01_installation"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "Installation" in out

    def test_skills_get_unknown_name_returns_nonzero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["skills", "get", "no-such-skill"])
        # Assert
        assert result != 0


# --- skills install --------------------------------------------------------


class TestSkillsInstall:
    def test_skills_install_dry_run_returns_exit_zero(self, capsys):
        # Arrange
        # (no setup)
        # Act
        result = main(["skills", "install", "--dry-run"])
        # Assert
        assert result == 0

    def test_skills_install_dry_run_previews_action(self, capsys):
        # Arrange
        main(["skills", "install", "--dry-run"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "would symlink" in out
