"""Unit tests for 'lk agent get' command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lyzr_kit.main import app
from lyzr_kit.utils.auth import AuthConfig, AuthError
from lyzr_kit.utils.platform import AgentResponse, PlatformError

runner = CliRunner()


class TestAgentGetSerialNumbers:
    """Tests for serial number support in 'lk agent get' command."""

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    @patch("lyzr_kit.commands.agent_get.PlatformClient")
    def test_get_accepts_serial_number(self, mock_platform_class, mock_load_auth, mock_validate):
        """get should accept plain serial number for built-in agents."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        mock_platform = MagicMock()
        mock_platform.create_agent.return_value = AgentResponse(
            agent_id="agent-123",
            env_id="env-456",
            endpoint="https://api.example.com/chat/agent-123",
            platform_url="https://studio.lyzr.ai/agent-create/agent-123",
        )
        mock_platform_class.return_value = mock_platform

        # Use 1 for built-in agent (chat-agent has serial 1)
        # Provide 'y' for confirmation prompt
        result = runner.invoke(app, ["agent", "get", "1"], input="y\n")
        assert result.exit_code == 0
        assert "created successfully" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_get_fails_with_invalid_builtin_serial(self, mock_load_auth, mock_validate):
        """get should fail when built-in serial number not found."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        # Try to use 99 which doesn't exist
        result = runner.invoke(app, ["agent", "get", "99"])
        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_get_shows_list_on_invalid_serial(self, mock_load_auth, mock_validate):
        """get should auto-show agent list when serial number is invalid."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        result = runner.invoke(app, ["agent", "get", "99"])
        assert result.exit_code == 1
        # Should show the agent list after error
        assert "Agents" in result.output


class TestAgentGetErrors:
    """Tests for error handling in 'lk agent get' command."""

    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_get_fails_without_auth(self, mock_load_auth):
        """get should fail with auth error when no .env file."""
        mock_load_auth.side_effect = AuthError("Authentication required")

        result = runner.invoke(app, ["agent", "get", "chat-agent"])
        assert result.exit_code == 1
        assert "Authentication Error" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    @patch("lyzr_kit.commands.agent_get.PlatformClient")
    def test_get_fails_on_platform_error(self, mock_platform_class, mock_load_auth, mock_validate):
        """get should show platform error message on API failure."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        mock_platform = MagicMock()
        mock_platform.create_agent.side_effect = PlatformError("API error")
        mock_platform_class.return_value = mock_platform

        # Provide 'y' for confirmation
        result = runner.invoke(app, ["agent", "get", "chat-agent"], input="y\n")
        assert result.exit_code == 1
        assert "Platform Error" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    @patch("lyzr_kit.commands.agent_get.PlatformClient")
    def test_get_creates_copy_of_agent(self, mock_platform_class, mock_load_auth, mock_validate):
        """get should create agent with copy-of-<name> ID."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        mock_platform = MagicMock()
        mock_platform.create_agent.return_value = AgentResponse(
            agent_id="agent-123",
            env_id="env-456",
            endpoint="https://api.example.com/chat/agent-123",
            platform_url="https://studio.lyzr.ai/agent-create/agent-123",
            chat_url="https://studio.lyzr.ai/agent/agent-123/",
            app_id="app-789",
        )
        mock_platform_class.return_value = mock_platform

        # Provide 'y' for confirmation
        result = runner.invoke(app, ["agent", "get", "chat-agent"], input="y\n")
        assert result.exit_code == 0
        assert "copy-of-chat-agent" in result.output
        assert "created successfully" in result.output

    def test_get_cancels_on_no(self):
        """get should cancel when user says no."""
        with (
            patch("lyzr_kit.commands._auth_helper.validate_auth", return_value=True),
            patch("lyzr_kit.commands._auth_helper.load_auth") as mock_load,
        ):
            mock_load.return_value = AuthConfig(api_key="test-key")

            result = runner.invoke(app, ["agent", "get", "chat-agent"], input="n\n")
            assert result.exit_code == 0
            assert "Cancelled" in result.output


class TestAgentGetHelp:
    """Tests for agent get help."""

    def test_agent_get_help(self):
        """agent get --help should show command description."""
        result = runner.invoke(app, ["agent", "get", "--help"])
        assert result.exit_code == 0
        assert "SOURCE_ID" in result.output
        assert "Clone" in result.output or "agent" in result.output.lower()
