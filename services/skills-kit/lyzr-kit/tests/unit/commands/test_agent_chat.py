"""Unit tests for 'lk agent chat' command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from lyzr_kit.main import app
from lyzr_kit.utils.auth import AuthConfig, AuthError

runner = CliRunner()


class TestAgentChatSerialNumbers:
    """Tests for serial number support in 'lk agent chat' command."""

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_chat_fails_with_invalid_local_serial(self, mock_load_auth, mock_validate):
        """chat should fail when local serial number not found."""
        mock_load_auth.return_value = AuthConfig(
            api_key="test-key",
            user_id="user-123",
            memberstack_token="token-abc",
        )
        mock_validate.return_value = True

        # Try to use 99 which doesn't exist (assumes local agent)
        result = runner.invoke(app, ["agent", "chat", "99"])
        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_chat_shows_list_on_invalid_serial(self, mock_load_auth, mock_validate):
        """chat should auto-show agent list when serial number is invalid."""
        mock_load_auth.return_value = AuthConfig(
            api_key="test-key",
            user_id="user-123",
            memberstack_token="token-abc",
        )
        mock_validate.return_value = True

        result = runner.invoke(app, ["agent", "chat", "99"])
        assert result.exit_code == 1
        # Should show the agent list after error
        assert "Agents" in result.output


class TestAgentChat:
    """Tests for 'lk agent chat' command."""

    def test_chat_help_shows_usage(self):
        """chat --help should show command description."""
        result = runner.invoke(app, ["agent", "chat", "--help"])
        assert result.exit_code == 0
        assert "IDENTIFIER" in result.output
        assert "chat" in result.output.lower()

    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_chat_fails_without_auth(self, mock_load_auth):
        """chat should fail with auth error when no .env file."""
        mock_load_auth.side_effect = AuthError("Authentication required")

        result = runner.invoke(app, ["agent", "chat", "my-agent"])
        assert result.exit_code == 1
        assert "Authentication Error" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_chat_fails_when_missing_env_tokens(self, mock_load_auth, mock_validate):
        """chat should fail when LYZR_USER_ID or LYZR_MEMBERSTACK_TOKEN missing."""
        # Only API key set, missing user_id and memberstack_token
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        result = runner.invoke(app, ["agent", "chat", "my-agent"])
        assert result.exit_code == 1
        assert "Missing required .env tokens" in result.output
        assert "LYZR_USER_ID" in result.output
        assert "LYZR_MEMBERSTACK_TOKEN" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_chat_fails_when_agent_not_found(self, mock_load_auth, mock_validate):
        """chat should fail when agent YAML file doesn't exist."""
        mock_load_auth.return_value = AuthConfig(
            api_key="test-key",
            user_id="user-123",
            memberstack_token="token-xyz",
        )
        mock_validate.return_value = True

        result = runner.invoke(app, ["agent", "chat", "nonexistent-agent"])
        assert result.exit_code == 1
        assert "not found in agents/" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_chat_fails_when_agent_not_active(self, mock_load_auth, mock_validate):
        """chat should fail when agent is_active is False."""
        mock_load_auth.return_value = AuthConfig(
            api_key="test-key",
            user_id="user-123",
            memberstack_token="token-xyz",
        )
        mock_validate.return_value = True

        # Create agent YAML with is_active: false
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "inactive-agent.yaml").write_text("""
id: inactive-agent
name: Inactive Test Agent
category: chat
is_active: false
platform_agent_id: agent-123
platform_env_id: env-456
model:
  provider: openai
  name: gpt-4
  credential_id: cred-1
""")

        result = runner.invoke(app, ["agent", "chat", "inactive-agent"])
        assert result.exit_code == 1
        assert "not active" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_chat_fails_when_no_platform_id(self, mock_load_auth, mock_validate):
        """chat should fail when agent has no platform_agent_id."""
        mock_load_auth.return_value = AuthConfig(
            api_key="test-key",
            user_id="user-123",
            memberstack_token="token-xyz",
        )
        mock_validate.return_value = True

        # Create agent YAML without platform_agent_id
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "no-platform-id.yaml").write_text("""
id: no-platform-id
name: No Platform Agent
category: chat
is_active: true
model:
  provider: openai
  name: gpt-4
  credential_id: cred-1
""")

        result = runner.invoke(app, ["agent", "chat", "no-platform-id"])
        assert result.exit_code == 1
        assert "has no platform ID" in result.output
