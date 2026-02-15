"""Integration tests for agent API operations.

These tests use the real Lyzr API and require valid credentials.
Credentials are read from the root .env file (which is gitignored).

To run integration tests:
1. Create .env in project root with LYZR_API_KEY, LYZR_USER_ID, LYZR_MEMBERSTACK_TOKEN
2. Run: uv run pytest tests/integration/ -v -s
"""

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lyzr_kit.main import app

runner = CliRunner()

# Path to root .env file (gitignored, contains real credentials)
ROOT_DIR = Path(__file__).parent.parent.parent
ROOT_ENV_FILE = ROOT_DIR / ".env"


def _has_valid_credentials() -> bool:
    """Check if root .env has valid LYZR credentials."""
    if not ROOT_ENV_FILE.exists():
        return False
    content = ROOT_ENV_FILE.read_text()
    # Check for real API key (not placeholder)
    has_api_key = "LYZR_API_KEY=" in content
    is_placeholder = "test-placeholder" in content or "your-api-key" in content
    return has_api_key and not is_placeholder


# Skip all tests if no valid credentials in root .env
pytestmark = pytest.mark.skipif(
    not _has_valid_credentials(),
    reason="No valid .env file with LYZR credentials in project root. "
    "Create .env with LYZR_API_KEY to run integration tests.",
)


@pytest.fixture(autouse=True)
def clean_agents_dir():
    """Clean agents directory before and after each test."""
    agents_dir = Path.cwd() / "agents"
    if agents_dir.exists():
        shutil.rmtree(agents_dir)
    yield
    if agents_dir.exists():
        shutil.rmtree(agents_dir)


class TestAgentGet:
    """Integration tests for 'lk agent get' command."""

    def test_get_creates_agent_on_platform(self):
        """'lk agent get' should create agent on the platform."""
        result = runner.invoke(app, ["agent", "get", "chat-agent", "my-chat-agent"])

        print(f"\n--- OUTPUT ---\n{result.output}\n--------------")

        assert result.exit_code == 0
        assert "created successfully" in result.output
        assert "Agent ID:" in result.output
        assert "Platform URL:" in result.output
        assert "Chat URL:" in result.output
        assert "API Endpoint:" in result.output

        # Verify local file was created with platform IDs (using new_id)
        local_file = Path.cwd() / "agents" / "my-chat-agent.yaml"
        assert local_file.exists()

        content = local_file.read_text()
        assert "platform_agent_id:" in content
        assert "platform_env_id:" in content
        assert "endpoint:" in content
        assert "is_active: true" in content

    def test_get_fails_for_nonexistent_agent(self):
        """'lk agent get' should fail for agent not in collection."""
        result = runner.invoke(app, ["agent", "get", "nonexistent-agent", "my-new-agent"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_get_fails_if_already_exists(self):
        """'lk agent get' should fail if new_id already exists."""
        # First get succeeds
        result1 = runner.invoke(app, ["agent", "get", "qa-agent", "my-qa-agent"])
        assert result1.exit_code == 0

        # Second get with same new_id fails
        result2 = runner.invoke(app, ["agent", "get", "chat-agent", "my-qa-agent"])
        assert result2.exit_code == 1
        assert "already exists" in result2.output


class TestAgentSet:
    """Integration tests for 'lk agent set' command."""

    def test_set_updates_agent_on_platform(self):
        """'lk agent set' should update agent on the platform."""
        # First create the agent
        get_result = runner.invoke(app, ["agent", "get", "summarizer", "my-summarizer"])
        print(f"\n--- GET OUTPUT ---\n{get_result.output}\n--------------")
        assert get_result.exit_code == 0

        # Then update it
        set_result = runner.invoke(app, ["agent", "set", "my-summarizer"])
        print(f"\n--- SET OUTPUT ---\n{set_result.output}\n--------------")

        assert set_result.exit_code == 0
        assert "updated successfully" in set_result.output
        assert "Agent ID:" in set_result.output
        assert "Platform URL:" in set_result.output
        assert "Chat URL:" in set_result.output

    def test_set_fails_if_not_in_local(self):
        """'lk agent set' should fail if agent not in agents/."""
        result = runner.invoke(app, ["agent", "set", "chat-agent"])

        assert result.exit_code == 1
        assert "not found" in result.output


class TestAgentLs:
    """Integration tests for 'lk agent ls' command."""

    def test_ls_shows_builtin_agents(self):
        """'lk agent ls' should list built-in agents."""
        result = runner.invoke(app, ["agent", "ls"])

        assert result.exit_code == 0
        assert "chat-agent" in result.output
        assert "qa-agent" in result.output

    def test_ls_shows_local_agents_with_endpoint(self):
        """'lk agent ls' should show local agents with their endpoint."""
        # First create a local agent
        get_result = runner.invoke(app, ["agent", "get", "code-reviewer", "my-code-reviewer"])
        assert get_result.exit_code == 0

        # List should show it in Your Agents table with endpoint
        ls_result = runner.invoke(app, ["agent", "ls"])
        print(f"\n--- LS OUTPUT ---\n{ls_result.output}\n--------------")

        assert ls_result.exit_code == 0
        assert "Your Agents" in ls_result.output
        assert "my-code-reviewer" in ls_result.output
        # Endpoint URL may be truncated in table output
        assert "agent-prod.studio" in ls_result.output or "agent-prod" in ls_result.output


class TestFullWorkflow:
    """Integration tests for the full agent workflow."""

    def test_get_modify_set_workflow(self):
        """Test the full workflow: get -> modify -> set."""
        # Step 1: Get agent from collection
        print("\n=== Step 1: Get agent ===")
        get_result = runner.invoke(app, ["agent", "get", "translator", "my-translator"])
        print(get_result.output)
        assert get_result.exit_code == 0
        assert "created successfully" in get_result.output

        # Step 2: Verify local file
        print("\n=== Step 2: Verify local file ===")
        local_file = Path.cwd() / "agents" / "my-translator.yaml"
        assert local_file.exists()
        content = local_file.read_text()
        print(f"Content preview:\n{content[:500]}...")

        # Step 3: Modify the agent (update temperature)
        print("\n=== Step 3: Modify agent ===")
        if "temperature: 0.3" in content:
            updated_content = content.replace("temperature: 0.3", "temperature: 0.5")
        else:
            updated_content = content.replace("temperature: 0.7", "temperature: 0.5")
        local_file.write_text(updated_content)
        print("Updated temperature to 0.5")

        # Step 4: Update on platform
        print("\n=== Step 4: Update on platform ===")
        set_result = runner.invoke(app, ["agent", "set", "my-translator"])
        print(set_result.output)
        assert set_result.exit_code == 0
        assert "updated successfully" in set_result.output

        # Step 5: Verify in list
        print("\n=== Step 5: Verify in list ===")
        ls_result = runner.invoke(app, ["agent", "ls"])
        print(ls_result.output)
        assert "my-translator" in ls_result.output
        assert "Your Agents" in ls_result.output  # Separate table for local agents
        # Endpoint URL may be truncated in table output
        assert "agent-prod.studio" in ls_result.output or "agent-prod" in ls_result.output

        print("\n=== Full workflow completed successfully! ===")
