"""Unit tests for feature CLI commands.

TODO: Feature commands will be fully implemented in Phase 5.
Currently, all commands return a placeholder message.
"""

from typer.testing import CliRunner

from lyzr_kit.main import app

runner = CliRunner()


class TestFeatureCommands:
    """Tests for feature commands (Phase 5 stubs)."""

    def test_feature_ls_stub(self):
        """feature ls should show Phase 5 message."""
        result = runner.invoke(app, ["feature", "ls"])
        assert result.exit_code == 0
        assert "Phase 5" in result.output

    def test_feature_get_stub(self):
        """feature get should show Phase 5 message."""
        result = runner.invoke(app, ["feature", "get", "memory"])
        assert result.exit_code == 0
        assert "Phase 5" in result.output

    def test_feature_set_stub(self):
        """feature set should show Phase 5 message."""
        result = runner.invoke(app, ["feature", "set", "memory"])
        assert result.exit_code == 0
        assert "Phase 5" in result.output

    def test_feature_shorthand(self):
        """'lk f ls' should work as shorthand."""
        result = runner.invoke(app, ["f", "ls"])
        assert result.exit_code == 0
        assert "Phase 5" in result.output

    def test_feature_help(self):
        """feature --help should show available subcommands."""
        result = runner.invoke(app, ["feature", "--help"])
        assert result.exit_code == 0
        assert "ls" in result.output
        assert "get" in result.output
        assert "set" in result.output
