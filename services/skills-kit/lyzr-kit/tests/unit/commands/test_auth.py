"""Unit tests for auth CLI command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from lyzr_kit.main import app

runner = CliRunner()


class TestAuthCommand:
    """Tests for 'lk auth' command."""

    def test_auth_creates_env_file(self):
        """auth should create .env file with API key."""
        # Provide: API key, User ID (skip), Org ID (skip), Memberstack token (skip)
        result = runner.invoke(app, ["auth"], input="test-api-key-123\n\n\n\n")
        assert result.exit_code == 0
        assert "saved" in result.output.lower()

        env_file = Path.cwd() / ".env"
        assert env_file.exists()
        assert "LYZR_API_KEY=test-api-key-123" in env_file.read_text()

    def test_auth_updates_existing_env(self):
        """auth should update existing .env file."""
        # Create existing .env
        env_file = Path.cwd() / ".env"
        env_file.write_text("OTHER_VAR=value\nLYZR_API_KEY=old-key\n")

        # Run auth - provide all 4 prompts (skip optional ones)
        result = runner.invoke(app, ["auth"], input="new-api-key\n\n\n\n")
        assert result.exit_code == 0

        # Check updated
        content = env_file.read_text()
        assert "LYZR_API_KEY=new-api-key" in content
        assert "OTHER_VAR=value" in content
        assert "old-key" not in content

    def test_auth_appends_to_env_without_key(self):
        """auth should append if .env exists but has no LYZR_API_KEY."""
        # Create existing .env without API key
        env_file = Path.cwd() / ".env"
        env_file.write_text("OTHER_VAR=value\n")

        # Run auth - provide all 4 prompts (skip optional ones)
        result = runner.invoke(app, ["auth"], input="my-api-key\n\n\n\n")
        assert result.exit_code == 0

        # Check appended
        content = env_file.read_text()
        assert "LYZR_API_KEY=my-api-key" in content
        assert "OTHER_VAR=value" in content

    def test_auth_help(self):
        """auth --help should show command description."""
        result = runner.invoke(app, ["auth", "--help"])
        assert result.exit_code == 0
        assert "API" in result.output or "key" in result.output.lower()

    @patch("lyzr_kit.commands.auth.typer.prompt", return_value="")
    def test_auth_rejects_empty_key(self, mock_prompt):
        """auth should reject empty API key."""
        result = runner.invoke(app, ["auth"])
        assert result.exit_code == 1
        assert "empty" in result.output.lower()

    @patch("lyzr_kit.commands.auth.typer.prompt", return_value="   ")
    def test_auth_rejects_whitespace_only_key(self, mock_prompt):
        """auth should reject whitespace-only API key."""
        result = runner.invoke(app, ["auth"])
        assert result.exit_code == 1
        assert "empty" in result.output.lower()
