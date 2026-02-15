"""Unit tests for 'lk agent set' command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lyzr_kit.main import app
from lyzr_kit.utils.auth import AuthConfig, AuthError
from lyzr_kit.utils.platform import PlatformError

runner = CliRunner()


class TestAgentSetSerialNumbers:
    """Tests for serial number support in 'lk agent set' command."""

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_fails_with_invalid_local_serial(self, mock_load_auth, mock_validate):
        """set should fail when local serial number not found."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        # Try to use 99 which doesn't exist (assumes local agent)
        result = runner.invoke(app, ["agent", "set", "99"])
        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_shows_list_on_invalid_serial(self, mock_load_auth, mock_validate):
        """set should auto-show agent list when serial number is invalid."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        result = runner.invoke(app, ["agent", "set", "99"])
        assert result.exit_code == 1
        # Should show the agent list after error
        assert "Agents" in result.output


class TestAgentSetErrors:
    """Tests for error handling in 'lk agent set' command."""

    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_fails_without_auth(self, mock_load_auth):
        """set should fail with auth error when no .env file."""
        mock_load_auth.side_effect = AuthError("Authentication required")

        result = runner.invoke(app, ["agent", "set", "chat-agent"])
        assert result.exit_code == 1
        assert "Authentication Error" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_fails_when_agent_not_found(self, mock_load_auth, mock_validate):
        """set should fail when agent YAML file doesn't exist."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        result = runner.invoke(app, ["agent", "set", "nonexistent-agent"])
        assert result.exit_code == 1
        assert "not found in agents/" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_fails_with_invalid_yaml(self, mock_load_auth, mock_validate):
        """set should fail with YAML syntax error."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        # Create invalid YAML file
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "broken-agent.yaml").write_text("invalid: yaml: [")

        result = runner.invoke(app, ["agent", "set", "broken-agent"])
        assert result.exit_code == 1
        assert "Invalid YAML syntax" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_fails_with_invalid_schema(self, mock_load_auth, mock_validate):
        """set should fail with detailed schema error."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        # Create invalid schema YAML file
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "bad-schema-agent.yaml").write_text("field: value\nother: 123\n")

        result = runner.invoke(app, ["agent", "set", "bad-schema-agent"])
        assert result.exit_code == 1
        assert "invalid schema" in result.output
        assert "Expected fields:" in result.output
        assert "Your file is missing" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_fails_when_missing_platform_ids(self, mock_load_auth, mock_validate):
        """set should fail when agent has no platform IDs."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        # Create valid agent YAML without platform IDs
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "no-platform-agent.yaml").write_text("""
id: no-platform-agent
name: Test Agent
category: chat
model:
  provider: openai
  name: gpt-4
  credential_id: cred-1
""")

        result = runner.invoke(app, ["agent", "set", "no-platform-agent"])
        assert result.exit_code == 1
        assert "no platform IDs" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_fails_when_id_changed_to_existing(self, mock_load_auth, mock_validate):
        """set should fail when ID in YAML conflicts with existing agent file."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        # Create agent YAML with ID different from filename
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "my-agent.yaml").write_text("""
id: conflicting-id
name: Test Agent
category: chat
platform_agent_id: agent-123
platform_env_id: env-456
model:
  provider: openai
  name: gpt-4
  credential_id: cred-1
""")

        # Create a conflicting agent file with the same ID
        (agents_dir / "conflicting-id.yaml").write_text("""
id: conflicting-id
name: Existing Agent
category: chat
platform_agent_id: agent-existing
platform_env_id: env-existing
model:
  provider: openai
  name: gpt-4
  credential_id: cred-1
""")

        result = runner.invoke(app, ["agent", "set", "my-agent"])
        assert result.exit_code == 1
        assert "already exists" in result.output
        assert "Update the ID in the YAML" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    @patch("lyzr_kit.commands.agent_set.StorageManager")
    @patch("lyzr_kit.commands.agent_set.PlatformClient")
    def test_set_fails_on_platform_error(
        self, mock_platform_class, mock_storage_class, mock_load_auth, mock_validate
    ):
        """set should show platform error message on API failure."""
        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        # Create valid agent YAML with platform IDs
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "platform-error-agent.yaml").write_text("""
id: platform-error-agent
name: Test Agent
category: chat
platform_agent_id: agent-123
platform_env_id: env-456
model:
  provider: openai
  name: gpt-4
  credential_id: cred-1
""")

        mock_storage = MagicMock()
        mock_storage.local_path = Path.cwd()
        mock_storage.agent_exists.return_value = False
        mock_storage_class.return_value = mock_storage

        mock_platform = MagicMock()
        mock_platform.update_agent.side_effect = PlatformError("API error")
        mock_platform_class.return_value = mock_platform

        result = runner.invoke(app, ["agent", "set", "platform-error-agent"])
        assert result.exit_code == 1
        assert "Platform Error" in result.output


class TestAgentSetHelp:
    """Tests for agent set help."""

    def test_agent_set_help(self):
        """agent set --help should show command description."""
        result = runner.invoke(app, ["agent", "set", "--help"])
        assert result.exit_code == 0
        assert "IDENTIFIER" in result.output
        assert "Sync" in result.output or "platform" in result.output.lower()
