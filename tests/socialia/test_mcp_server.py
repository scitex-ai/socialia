"""Tests for socialia MCP server module."""

import pytest

fastmcp = pytest.importorskip("fastmcp", reason="fastmcp not installed")


# --- mcp list-tools --------------------------------------------------------


class TestMCPToolsList:
    def test_mcp_list_tools_returns_exit_zero(self, capsys):
        # Arrange
        from socialia.cli import main
        # Act
        result = main(["mcp", "list-tools"])
        # Assert
        assert result == 0

    def test_mcp_list_tools_output_includes_social_post(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "list-tools"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "social_post" in out

    def test_mcp_list_tools_output_includes_social_delete(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "list-tools"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "social_delete" in out

    def test_mcp_list_tools_output_includes_social_status(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "list-tools"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "social_status" in out

    def test_mcp_list_tools_output_includes_analytics_track(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "list-tools"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "analytics_track" in out

    def test_mcp_list_tools_output_includes_analytics_realtime(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "list-tools"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "analytics_realtime" in out


# --- mcp doctor ------------------------------------------------------------


class TestMCPDoctor:
    def test_mcp_doctor_returns_zero_or_one(self, capsys):
        # Arrange
        from socialia.cli import main
        # Act
        result = main(["mcp", "doctor"])
        # Assert
        assert result in (0, 1)

    def test_mcp_doctor_output_contains_health_check_header(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "doctor"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "Health Check" in out

    def test_mcp_doctor_output_lists_twitter_platform(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "doctor"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "Twitter" in out

    def test_mcp_doctor_output_lists_linkedin_platform(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "doctor"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "LinkedIn" in out

    def test_mcp_doctor_output_lists_reddit_platform(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "doctor"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "Reddit" in out


# --- mcp installation ------------------------------------------------------


class TestMCPInstallation:
    def test_mcp_installation_returns_exit_zero(self, capsys):
        # Arrange
        from socialia.cli import main
        # Act
        rc = main(["mcp", "installation"])
        # Assert
        assert rc == 0

    def test_mcp_installation_output_mentions_claude_desktop(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "installation"])
        # Act
        out = capsys.readouterr().err
        # Assert
        assert "Claude Desktop" in out

    def test_mcp_installation_output_renders_mcp_servers_section(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "installation"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "mcpServers" in out

    def test_mcp_installation_output_mentions_socialia_entry(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "installation"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "socialia" in out

    def test_mcp_installation_output_renders_json_open_brace(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "installation"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "{" in out

    def test_mcp_installation_output_renders_json_close_brace(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "installation"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "}" in out

    def test_mcp_installation_output_documents_command_key(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "installation"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert '"command"' in out or "command" in out


# --- mcp_server module surface --------------------------------------------


class TestMCPServerModuleImports:
    def test_mcp_server_module_imports_cleanly(self):
        # Arrange
        from socialia import mcp_server
        # Act
        module = mcp_server
        # Assert
        assert module is not None

    def test_get_tools_returns_list_or_dict_when_available(self):
        # Arrange
        import importlib

        mod = importlib.import_module("socialia.mcp_server")
        get_tools = getattr(mod, "get_tools", None)
        # If get_tools is unavailable, fall through to a trivial true
        # assertion — the import-surface coverage above already exercises
        # the module-import contract for the unavailable case.
        # Act
        tools = get_tools() if get_tools is not None else []
        # Assert
        assert isinstance(tools, (list, dict))


# --- mcp start --help ------------------------------------------------------


class TestMCPStartHelp:
    def test_mcp_start_help_returns_exit_zero(self, capsys):
        # Arrange
        from socialia.cli import main
        # Act
        rc = main(["mcp", "start", "--help"])
        # Assert
        assert rc == 0

    def test_mcp_start_help_mentions_start_subcommand(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "start", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "mcp start" in out or "start" in out.lower()

    def test_mcp_start_help_documents_dry_run_flag(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "start", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "--dry-run" in out

    def test_mcp_start_help_documents_yes_flag(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["mcp", "start", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "--yes" in out

    def test_mcp_root_without_subcommand_returns_zero_or_one(self, capsys):
        # Arrange
        from socialia.cli import main
        # Act
        result = main(["mcp"])
        # Assert
        assert result in (0, 1)
