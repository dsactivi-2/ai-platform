"""Unit tests for agent CLI commands.

These tests verify CLI behavior and argument parsing.
For actual API integration tests, see tests/integration/test_agent_api.py
"""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lyzr_kit.main import app
from lyzr_kit.utils.auth import AuthError

runner = CliRunner()


class TestAgentLs:
    """Tests for 'lk agent ls' command."""

    def test_ls_shows_builtin_agents(self):
        """ls should list built-in agents from collection."""
        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        assert "chat-agent" in result.output
        assert "qa-agent" in result.output

    def test_ls_shorthand(self):
        """'lk a ls' should work as shorthand."""
        result = runner.invoke(app, ["a", "ls"])
        assert result.exit_code == 0
        assert "chat-agent" in result.output

    def test_ls_shows_table_columns(self):
        """ls should display table with correct columns."""
        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        assert "#" in result.output
        assert "ID" in result.output
        assert "NAME" in result.output
        assert "CATEGORY" in result.output
        assert "STUDIO" in result.output

    def test_ls_shows_serial_numbers(self):
        """ls should show serial numbers from YAML."""
        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        # Check that serial numbers appear (plain numbers, no prefix)
        assert "1" in result.output
        assert "2" in result.output

    def test_ls_shows_two_separate_tables(self):
        """ls should show separate tables for built-in and local agents."""
        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        assert "Built-in Agents" in result.output
        assert "Your Agents" in result.output

    def test_ls_shows_local_agents_in_your_agents_table(self):
        """ls should show local agents in 'Your Agents' table."""
        from pathlib import Path

        from lyzr_kit.schemas.agent import Agent, ModelConfig

        # Create a local agent
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        agent = Agent(
            id="test-local-agent",
            serial=1,
            name="Test Local Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )

        # Write agent YAML
        import yaml

        agent_path = agents_dir / "test-local-agent.yaml"
        data = agent.model_dump(exclude_none=True)
        with open(agent_path, "w") as f:
            yaml.dump(data, f)

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        # Local agent should appear in Your Agents table
        assert "Your Agents" in result.output
        assert "test-local-agent" in result.output

    def test_ls_shows_builtin_and_local_in_separate_tables(self):
        """ls should show built-in and local agents in separate tables."""
        from pathlib import Path

        from lyzr_kit.schemas.agent import Agent, ModelConfig

        # Create a local agent
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        agent = Agent(
            id="my-local-agent",
            serial=1,
            name="My Local Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )

        import yaml

        agent_path = agents_dir / "my-local-agent.yaml"
        data = agent.model_dump(exclude_none=True)
        with open(agent_path, "w") as f:
            yaml.dump(data, f)

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0

        # Find positions of tables
        output = result.output
        builtin_table_pos = output.find("Built-in Agents")
        local_table_pos = output.find("Your Agents")

        # Built-in table should appear before local table
        assert builtin_table_pos < local_table_pos, (
            "Built-in Agents table should appear before Your Agents table"
        )

    @patch("lyzr_kit.commands.agent_list.validate_agents_folder")
    @patch("lyzr_kit.commands.agent_list.StorageManager")
    def test_ls_shows_no_agents_message(self, mock_storage_class, mock_validate):
        """ls should show message when no agents found."""
        from lyzr_kit.storage.validator import ValidationResult

        mock_validate.return_value = ValidationResult(is_valid=True)

        mock_storage = MagicMock()
        mock_storage.list_agents.return_value = []
        mock_storage.local_path = "."
        mock_storage_class.return_value = mock_storage

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        # Shows empty messages in both tables
        assert "No built-in agents" in result.output
        assert "No local agents" in result.output

    def test_ls_fails_with_nested_folder(self):
        """ls should fail when nested folders exist in agents/."""
        from pathlib import Path

        # Create nested folder
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        nested_dir = agents_dir / "nested-folder"
        nested_dir.mkdir()

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 1
        assert "Nested folders" in result.output
        assert "nested-folder" in result.output

    def test_ls_fails_with_invalid_extension(self):
        """ls should fail when non-YAML files exist in agents/."""
        from pathlib import Path

        # Create invalid file
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "readme.txt").write_text("text")

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 1
        assert "Invalid file extensions" in result.output
        assert "readme.txt" in result.output

    def test_ls_fails_with_invalid_yaml(self):
        """ls should fail when YAML files have invalid syntax."""
        from pathlib import Path

        # Create invalid YAML
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "broken.yaml").write_text("invalid: yaml: [")

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 1
        assert "Invalid YAML syntax" in result.output

    def test_ls_fails_with_invalid_schema(self):
        """ls should fail when YAML files don't match Agent schema."""
        from pathlib import Path

        # Create invalid schema YAML
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "bad-agent.yaml").write_text("field: value\n")

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 1
        assert "Invalid agent schema" in result.output


class TestAgentHelp:
    """Tests for agent command help."""

    def test_agent_help(self):
        """agent --help should show available subcommands."""
        result = runner.invoke(app, ["agent", "--help"])
        assert result.exit_code == 0
        assert "ls" in result.output
        assert "get" in result.output
        assert "set" in result.output

    def test_agent_ls_help(self):
        """agent ls --help should show command description."""
        result = runner.invoke(app, ["agent", "ls", "--help"])
        assert result.exit_code == 0
        assert "List" in result.output or "list" in result.output

    def test_agent_get_help(self):
        """agent get --help should show command description."""
        result = runner.invoke(app, ["agent", "get", "--help"])
        assert result.exit_code == 0
        assert "SOURCE_ID" in result.output
        assert "Clone" in result.output or "agent" in result.output.lower()

    def test_agent_set_help(self):
        """agent set --help should show command description."""
        result = runner.invoke(app, ["agent", "set", "--help"])
        assert result.exit_code == 0
        assert "IDENTIFIER" in result.output
        assert "Sync" in result.output or "platform" in result.output.lower()


class TestAgentGetSerialNumbers:
    """Tests for serial number support in 'lk agent get' command."""

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    @patch("lyzr_kit.commands.agent_get.PlatformClient")
    def test_get_accepts_serial_number(self, mock_platform_class, mock_load_auth, mock_validate):
        """get should accept plain serial number for built-in agents."""
        from lyzr_kit.utils.auth import AuthConfig
        from lyzr_kit.utils.platform import AgentResponse

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
        from lyzr_kit.utils.auth import AuthConfig

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
        from lyzr_kit.utils.auth import AuthConfig

        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        result = runner.invoke(app, ["agent", "get", "99"])
        assert result.exit_code == 1
        # Should show the agent list after error
        assert "Agents" in result.output


class TestAgentSetSerialNumbers:
    """Tests for serial number support in 'lk agent set' command."""

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_fails_with_invalid_local_serial(self, mock_load_auth, mock_validate):
        """set should fail when local serial number not found."""
        from lyzr_kit.utils.auth import AuthConfig

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
        from lyzr_kit.utils.auth import AuthConfig

        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        result = runner.invoke(app, ["agent", "set", "99"])
        assert result.exit_code == 1
        # Should show the agent list after error
        assert "Agents" in result.output


class TestAgentChatSerialNumbers:
    """Tests for serial number support in 'lk agent chat' command."""

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_chat_fails_with_invalid_local_serial(self, mock_load_auth, mock_validate):
        """chat should fail when local serial number not found."""
        from lyzr_kit.utils.auth import AuthConfig

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
        from lyzr_kit.utils.auth import AuthConfig

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
        from lyzr_kit.utils.auth import AuthConfig
        from lyzr_kit.utils.platform import PlatformError

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
        from lyzr_kit.utils.auth import AuthConfig
        from lyzr_kit.utils.platform import AgentResponse

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
        from unittest.mock import patch

        from lyzr_kit.utils.auth import AuthConfig

        with (
            patch("lyzr_kit.commands._auth_helper.validate_auth", return_value=True),
            patch("lyzr_kit.commands._auth_helper.load_auth") as mock_load,
        ):
            mock_load.return_value = AuthConfig(api_key="test-key")

            result = runner.invoke(app, ["agent", "get", "chat-agent"], input="n\n")
            assert result.exit_code == 0
            assert "Cancelled" in result.output


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
        from lyzr_kit.utils.auth import AuthConfig

        mock_load_auth.return_value = AuthConfig(api_key="test-key")
        mock_validate.return_value = True

        result = runner.invoke(app, ["agent", "set", "nonexistent-agent"])
        assert result.exit_code == 1
        assert "not found in agents/" in result.output

    @patch("lyzr_kit.commands._auth_helper.validate_auth")
    @patch("lyzr_kit.commands._auth_helper.load_auth")
    def test_set_fails_with_invalid_yaml(self, mock_load_auth, mock_validate):
        """set should fail with YAML syntax error."""
        from pathlib import Path

        from lyzr_kit.utils.auth import AuthConfig

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
        from pathlib import Path

        from lyzr_kit.utils.auth import AuthConfig

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
        from pathlib import Path

        from lyzr_kit.utils.auth import AuthConfig

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
        from pathlib import Path

        from lyzr_kit.utils.auth import AuthConfig

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
        from pathlib import Path

        from lyzr_kit.utils.auth import AuthConfig
        from lyzr_kit.utils.platform import PlatformError

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
        from lyzr_kit.utils.auth import AuthConfig

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
        from lyzr_kit.utils.auth import AuthConfig

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
        from pathlib import Path

        from lyzr_kit.utils.auth import AuthConfig

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
        from pathlib import Path

        from lyzr_kit.utils.auth import AuthConfig

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


class TestStreamingHelpers:
    """Tests for streaming chat helper functions."""

    def test_separate_thinking_content_with_think_tags(self):
        """Should extract thinking content from <think> tags."""
        from lyzr_kit.commands.agent_chat import _separate_thinking_content

        content = "<think>I am analyzing the question</think>Here is my response"
        thinking, actual = _separate_thinking_content(content)
        assert thinking == "I am analyzing the question"
        assert actual == "Here is my response"

    def test_separate_thinking_content_without_think_tags(self):
        """Should return None for thinking when no <think> tags."""
        from lyzr_kit.commands.agent_chat import _separate_thinking_content

        content = "Just a regular response"
        thinking, actual = _separate_thinking_content(content)
        assert thinking is None
        assert actual == "Just a regular response"

    def test_separate_thinking_content_multiline(self):
        """Should handle multiline thinking content."""
        from lyzr_kit.commands.agent_chat import _separate_thinking_content

        content = "<think>Step 1: Analyze\nStep 2: Process</think>The answer is 42"
        thinking, actual = _separate_thinking_content(content)
        assert thinking == "Step 1: Analyze\nStep 2: Process"
        assert actual == "The answer is 42"

    def test_decode_sse_data_escapes(self):
        """Should decode common escape sequences."""
        from lyzr_kit.commands.agent_chat import _decode_sse_data

        data = 'Hello\\nWorld\\t"quoted"'
        decoded = _decode_sse_data(data)
        assert decoded == 'Hello\nWorld\t"quoted"'

    def test_decode_sse_data_html_entities(self):
        """Should decode HTML entities."""
        from lyzr_kit.commands.agent_chat import _decode_sse_data

        data = "&lt;tag&gt; &amp; &quot;text&quot;"
        decoded = _decode_sse_data(data)
        assert decoded == '<tag> & "text"'

    def test_stream_state_initial_values(self):
        """StreamState should have correct initial values."""
        from lyzr_kit.commands.agent_chat import StreamState

        state = StreamState()
        assert state.content == ""
        assert state.events == []
        assert state.is_streaming is False
        assert state.start_time == 0.0
        assert state.first_chunk_time == 0.0
        assert state.end_time == 0.0
        assert state.tokens_in == 0
        assert state.tokens_out == 0
        assert state.error is None

    def test_stream_state_latency_calculation(self):
        """StreamState should calculate latency correctly."""
        from lyzr_kit.commands.agent_chat import StreamState

        state = StreamState()
        state.start_time = 1000.0
        state.first_chunk_time = 1000.5
        state.end_time = 1002.0

        assert state.latency_ms == 500.0  # 0.5 seconds = 500ms
        assert state.total_time_ms == 2000.0  # 2 seconds = 2000ms

    def test_stream_state_clear(self):
        """StreamState clear should reset all values."""
        from lyzr_kit.commands.agent_chat import StreamState

        state = StreamState()
        state.content = "test"
        state.is_streaming = True
        state.start_time = 100.0
        state.error = "some error"

        state.clear()

        assert state.content == ""
        assert state.is_streaming is False
        assert state.start_time == 0.0
        assert state.error is None


class TestWebSocketHelpers:
    """Tests for WebSocket event handling."""

    def test_chat_event_format_tool_call(self):
        """ChatEvent should format tool call events."""
        from datetime import datetime

        from lyzr_kit.commands._websocket import ChatEvent

        event = ChatEvent(
            event_type="tool_call_prepare",
            timestamp=datetime.now(),
            function_name="search_web",
        )
        assert event.format_display() == "[Tool] Calling search_web..."

    def test_chat_event_format_tool_response(self):
        """ChatEvent should format tool response events."""
        from datetime import datetime

        from lyzr_kit.commands._websocket import ChatEvent

        event = ChatEvent(
            event_type="tool_response",
            timestamp=datetime.now(),
            function_name="search_web",
            response='{"results": [1, 2, 3]}',
        )
        display = event.format_display()
        assert "[Tool] search_web →" in display

    def test_chat_event_format_llm_response(self):
        """ChatEvent should format LLM response events."""
        from datetime import datetime

        from lyzr_kit.commands._websocket import ChatEvent

        event = ChatEvent(
            event_type="llm_response",
            timestamp=datetime.now(),
        )
        assert event.format_display() == "[LLM] Generating response..."

    def test_chat_event_format_memory(self):
        """ChatEvent should format memory events."""
        from datetime import datetime

        from lyzr_kit.commands._websocket import ChatEvent

        event = ChatEvent(
            event_type="context_memory_updated",
            timestamp=datetime.now(),
        )
        assert event.format_display() == "[Memory] Context updated"

    def test_chat_event_format_artifact(self):
        """ChatEvent should format artifact events."""
        from datetime import datetime

        from lyzr_kit.commands._websocket import ChatEvent

        event = ChatEvent(
            event_type="artifact_create_success",
            timestamp=datetime.now(),
            arguments={"name": "chart.png"},
        )
        assert event.format_display() == "[Artifact] Created: chart.png"

    def test_parse_event_basic(self):
        """parse_event should parse basic event data."""
        from lyzr_kit.commands._websocket import parse_event

        data = {
            "event_type": "tool_call_prepare",
            "function_name": "test_func",
            "timestamp": "2024-01-01T12:00:00Z",
        }
        event = parse_event(data)
        assert event is not None
        assert event.event_type == "tool_call_prepare"
        assert event.function_name == "test_func"

    def test_parse_event_ignores_keepalive(self):
        """parse_event should ignore keepalive events."""
        from lyzr_kit.commands._websocket import parse_event

        data = {"event_type": "keepalive"}
        event = parse_event(data)
        assert event is None

    def test_event_state_deduplication(self):
        """EventState should deduplicate events."""
        from datetime import datetime

        from lyzr_kit.commands._websocket import ChatEvent, EventState

        state = EventState()
        event = ChatEvent(
            event_type="test",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            function_name="func1",
        )

        # First add should succeed
        assert state.add_event(event) is True
        assert len(state.events) == 1

        # Duplicate should be rejected
        assert state.add_event(event) is False
        assert len(state.events) == 1

    def test_event_state_clear(self):
        """EventState clear should reset all state."""
        from datetime import datetime

        from lyzr_kit.commands._websocket import ChatEvent, EventState

        state = EventState()
        state.add_event(ChatEvent(event_type="test", timestamp=datetime.now()))
        state.error = "test error"

        state.clear()

        assert len(state.events) == 0
        assert state.error is None


class TestChatUIBoxes:
    """Tests for chat UI box builders."""

    def test_build_session_box_returns_panel(self):
        """_build_session_box should return a Panel with session info."""
        from unittest.mock import MagicMock

        from rich.panel import Panel

        from lyzr_kit.commands.agent_chat import _build_session_box

        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.model = "gpt-4o"

        panel = _build_session_box(mock_agent, "abc12345-def6-7890", "14:32:15")

        assert isinstance(panel, Panel)
        assert panel.title is not None
        assert "Session" in str(panel.title)
        assert panel.border_style == "blue"

    def test_build_session_box_with_default_model(self):
        """_build_session_box should handle None model."""
        from unittest.mock import MagicMock

        from lyzr_kit.commands.agent_chat import _build_session_box

        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.model = None

        # Should not raise
        panel = _build_session_box(mock_agent, "session-id", "12:00:00")
        assert panel is not None

    def test_build_session_box_with_model_config(self):
        """_build_session_box should extract model name from ModelConfig."""
        from unittest.mock import MagicMock

        from lyzr_kit.commands.agent_chat import _build_session_box

        mock_model = MagicMock()
        mock_model.name = "gpt-4o-mini"

        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.model = mock_model

        # Should not raise and should use model.name
        panel = _build_session_box(mock_agent, "session-id", "12:00:00")
        assert panel is not None

    def test_build_user_box_returns_panel(self):
        """_build_user_box should return a Panel with user message."""
        from rich.panel import Panel

        from lyzr_kit.commands.agent_chat import _build_user_box

        panel = _build_user_box("Hello, world!", "14:32:20")

        assert isinstance(panel, Panel)
        assert panel.border_style == "cyan"
        assert "You" in str(panel.title)

    def test_build_agent_box_returns_panel(self):
        """_build_agent_box should return a Panel."""
        from rich.panel import Panel

        from lyzr_kit.commands.agent_chat import StreamState, _build_agent_box

        state = StreamState()
        state.content = "This is the response"
        state.is_streaming = False
        state.start_time = 1000.0
        state.end_time = 1001.5

        panel = _build_agent_box(state, "14:32:21")

        assert isinstance(panel, Panel)
        assert panel.border_style == "green"
        assert "Agent" in str(panel.title)

    def test_build_agent_box_error_style(self):
        """_build_agent_box should use red style for error-only state."""
        from lyzr_kit.commands.agent_chat import StreamState, _build_agent_box

        state = StreamState()
        state.error = "API error occurred"
        state.content = ""  # No content, error only
        state.is_streaming = False
        state.start_time = 1000.0
        state.end_time = 1001.0

        panel = _build_agent_box(state, "14:32:21")

        assert panel.border_style == "red"
        assert "Error" in str(panel.title)

    def test_build_agent_box_streaming_state(self):
        """_build_agent_box should show waiting message when streaming with no content."""
        from lyzr_kit.commands.agent_chat import StreamState, _build_agent_box

        state = StreamState()
        state.is_streaming = True
        state.content = ""

        panel = _build_agent_box(state, "14:32:21")

        assert panel.border_style == "green"
        # Subtitle should be None during streaming (no metrics yet)
        # Panel should contain "Waiting for response..."

    def test_build_agent_box_with_events(self):
        """_build_agent_box should include events in content."""
        from datetime import datetime

        from lyzr_kit.commands._websocket import ChatEvent
        from lyzr_kit.commands.agent_chat import StreamState, _build_agent_box

        state = StreamState()
        state.content = "Response text"
        state.is_streaming = False
        state.start_time = 1000.0
        state.end_time = 1001.0
        state.add_event(
            ChatEvent(
                event_type="tool_call_prepare",
                timestamp=datetime.now(),
                function_name="search_web",
            )
        )

        panel = _build_agent_box(state, "14:32:21")

        assert panel is not None
        assert len(state.events) == 1

    def test_build_agent_box_shows_latency(self):
        """_build_agent_box should show latency in subtitle after streaming."""
        from lyzr_kit.commands.agent_chat import StreamState, _build_agent_box

        state = StreamState()
        state.content = "Response"
        state.is_streaming = False
        state.start_time = 1000.0
        state.end_time = 1001.5  # 1.5 seconds

        panel = _build_agent_box(state, "14:32:21")

        # Subtitle should contain latency
        assert panel.subtitle is not None
        assert "1.50s" in str(panel.subtitle)
