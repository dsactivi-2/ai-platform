"""Unit tests for tool CLI commands.

TODO: Tool commands will be fully implemented in Phase 4.
Currently, all commands return a placeholder message.
"""

from typer.testing import CliRunner

from lyzr_kit.main import app

runner = CliRunner()


class TestToolCommands:
    """Tests for tool commands (Phase 4 stubs)."""

    def test_tool_ls_stub(self):
        """tool ls should show Phase 4 message."""
        result = runner.invoke(app, ["tool", "ls"])
        assert result.exit_code == 0
        assert "Phase 4" in result.output

    def test_tool_get_stub(self):
        """tool get should show Phase 4 message."""
        result = runner.invoke(app, ["tool", "get", "calculator"])
        assert result.exit_code == 0
        assert "Phase 4" in result.output

    def test_tool_set_stub(self):
        """tool set should show Phase 4 message."""
        result = runner.invoke(app, ["tool", "set", "calculator"])
        assert result.exit_code == 0
        assert "Phase 4" in result.output

    def test_tool_shorthand(self):
        """'lk t ls' should work as shorthand."""
        result = runner.invoke(app, ["t", "ls"])
        assert result.exit_code == 0
        assert "Phase 4" in result.output

    def test_tool_help(self):
        """tool --help should show available subcommands."""
        result = runner.invoke(app, ["tool", "--help"])
        assert result.exit_code == 0
        assert "ls" in result.output
        assert "get" in result.output
        assert "set" in result.output
