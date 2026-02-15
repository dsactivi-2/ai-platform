"""Unit tests for sub-agent functionality in CLI commands."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from lyzr_kit.main import app
from lyzr_kit.schemas.agent import Agent, ModelConfig
from lyzr_kit.storage import StorageManager

runner = CliRunner()


def create_test_agent(
    agent_id: str,
    name: str = "Test Agent",
    sub_agents: list[str] | None = None,
    platform_agent_id: str | None = "plat-123",
    platform_env_id: str | None = "env-456",
    is_active: bool = True,
) -> Agent:
    """Helper to create a test agent."""
    return Agent(
        id=agent_id,
        name=name,
        category="chat",
        model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        sub_agents=sub_agents or [],
        platform_agent_id=platform_agent_id,
        platform_env_id=platform_env_id,
        is_active=is_active,
    )


class TestAgentRmWithSubAgents:
    """Tests for 'lk agent rm' command with sub-agent checks."""

    def test_rm_deletes_agent_with_no_references(self):
        """rm should delete agent that is not used as sub-agent."""
        storage = StorageManager()

        # Create an agent with no parent references
        agent = create_test_agent("deletable-agent")
        storage.save_agent(agent)

        # Verify it exists
        assert storage.agent_exists_local("deletable-agent") is True

        # Delete it
        result = runner.invoke(app, ["agent", "rm", "deletable-agent"])
        assert result.exit_code == 0
        assert "deleted successfully" in result.output

        # Verify it's gone
        assert storage.agent_exists_local("deletable-agent") is False

    def test_rm_blocks_deletion_when_used_as_subagent(self):
        """rm should block deletion if agent is used as sub-agent."""
        storage = StorageManager()

        # Create a sub-agent
        sub_agent = create_test_agent("used-sub-agent")
        storage.save_agent(sub_agent)

        # Create a parent that uses it
        parent = create_test_agent("parent-using-sub", sub_agents=["used-sub-agent"])
        storage.save_agent(parent)

        # Try to delete the sub-agent - should fail
        result = runner.invoke(app, ["agent", "rm", "used-sub-agent"])
        assert result.exit_code == 1
        assert "Cannot delete" in result.output
        assert "parent-using-sub" in result.output

        # Verify sub-agent still exists
        assert storage.agent_exists_local("used-sub-agent") is True

    def test_rm_shows_all_parent_agents(self):
        """rm should show all agents using the sub-agent."""
        storage = StorageManager()

        # Create a shared sub-agent
        shared_sub = create_test_agent("shared-sub-for-rm")
        storage.save_agent(shared_sub)

        # Create two parents using it
        parent1 = create_test_agent("rm-parent-one", sub_agents=["shared-sub-for-rm"])
        storage.save_agent(parent1)

        parent2 = create_test_agent("rm-parent-two", sub_agents=["shared-sub-for-rm"])
        storage.save_agent(parent2)

        # Try to delete the sub-agent - should show both parents
        result = runner.invoke(app, ["agent", "rm", "shared-sub-for-rm"])
        assert result.exit_code == 1
        assert "rm-parent-one" in result.output
        assert "rm-parent-two" in result.output

    def test_rm_allows_after_removing_from_subagents(self):
        """rm should succeed after removing from sub_agents arrays."""
        storage = StorageManager()

        # Create a sub-agent
        sub_agent = create_test_agent("removable-sub")
        storage.save_agent(sub_agent)

        # Create a parent using it
        parent = create_test_agent("parent-to-update", sub_agents=["removable-sub"])
        storage.save_agent(parent)

        # First, update parent to remove the sub-agent reference
        parent.sub_agents = []
        storage.save_agent(parent)

        # Now deletion should succeed
        result = runner.invoke(app, ["agent", "rm", "removable-sub"])
        assert result.exit_code == 0
        assert "deleted successfully" in result.output

    def test_rm_fails_for_nonexistent_agent(self):
        """rm should fail for non-existent agent."""
        result = runner.invoke(app, ["agent", "rm", "nonexistent-agent-xyz"])
        assert result.exit_code == 1

    def test_rm_force_removes_from_parents_and_deletes(self):
        """rm --force should remove from parent agents and delete."""
        storage = StorageManager()

        # Create a sub-agent
        sub_agent = create_test_agent("force-delete-sub")
        storage.save_agent(sub_agent)

        # Create a parent that uses it
        parent = create_test_agent("force-delete-parent", sub_agents=["force-delete-sub"])
        storage.save_agent(parent)

        # Delete with --force flag
        result = runner.invoke(app, ["agent", "rm", "force-delete-sub", "--force"])
        assert result.exit_code == 0
        assert "deleted successfully" in result.output

        # Verify sub-agent is gone
        assert storage.agent_exists_local("force-delete-sub") is False

        # Verify parent's sub_agents was updated
        updated_parent = storage.get_agent("force-delete-parent")
        assert updated_parent is not None
        assert "force-delete-sub" not in updated_parent.sub_agents

    def test_rm_force_updates_multiple_parents(self):
        """rm --force should update all parent agents."""
        storage = StorageManager()

        # Create a shared sub-agent
        shared_sub = create_test_agent("shared-force-sub")
        storage.save_agent(shared_sub)

        # Create two parents using it
        parent1 = create_test_agent("force-parent-one", sub_agents=["shared-force-sub"])
        storage.save_agent(parent1)

        parent2 = create_test_agent(
            "force-parent-two", sub_agents=["shared-force-sub", "other-sub"]
        )
        storage.save_agent(parent2)

        # Delete with --force flag
        result = runner.invoke(app, ["agent", "rm", "shared-force-sub", "--force"])
        assert result.exit_code == 0
        assert "force-parent-one" in result.output
        assert "force-parent-two" in result.output

        # Verify both parents were updated
        updated_parent1 = storage.get_agent("force-parent-one")
        assert "shared-force-sub" not in updated_parent1.sub_agents

        updated_parent2 = storage.get_agent("force-parent-two")
        assert "shared-force-sub" not in updated_parent2.sub_agents
        assert "other-sub" in updated_parent2.sub_agents  # Other sub-agents preserved

    def test_rm_force_short_flag(self):
        """rm -f should work as --force."""
        storage = StorageManager()

        # Create a sub-agent and parent
        sub_agent = create_test_agent("short-flag-sub")
        storage.save_agent(sub_agent)

        parent = create_test_agent("short-flag-parent", sub_agents=["short-flag-sub"])
        storage.save_agent(parent)

        # Delete with -f flag
        result = runner.invoke(app, ["agent", "rm", "short-flag-sub", "-f"])
        assert result.exit_code == 0
        assert storage.agent_exists_local("short-flag-sub") is False

    def test_rm_shows_force_hint_when_blocked(self):
        """rm should show --force hint when deletion is blocked."""
        storage = StorageManager()

        # Create a sub-agent and parent
        sub_agent = create_test_agent("hint-test-sub")
        storage.save_agent(sub_agent)

        parent = create_test_agent("hint-test-parent", sub_agents=["hint-test-sub"])
        storage.save_agent(parent)

        # Try to delete without --force
        result = runner.invoke(app, ["agent", "rm", "hint-test-sub"])
        assert result.exit_code == 1
        assert "--force" in result.output


class TestAgentSetWithSubAgents:
    """Tests for 'lk agent set' command with sub-agent validation."""

    @patch("lyzr_kit.commands.agent_set.require_auth")
    @patch("lyzr_kit.commands.agent_set.PlatformClient")
    def test_set_fails_with_invalid_subagent(self, mock_platform, mock_auth):
        """set should fail if sub_agents contains invalid IDs."""
        from lyzr_kit.utils.auth import AuthConfig

        mock_auth.return_value = AuthConfig(api_key="test-key")
        storage = StorageManager()

        # Create an agent with invalid sub_agents
        agent = create_test_agent("agent-with-bad-sub", sub_agents=["nonexistent-sub"])
        storage.save_agent(agent)

        # Try to set - should fail validation
        result = runner.invoke(app, ["agent", "set", "agent-with-bad-sub"])
        assert result.exit_code == 1
        assert "Invalid sub-agent" in result.output
        assert "nonexistent-sub" in result.output

    @patch("lyzr_kit.commands.agent_set.require_auth")
    @patch("lyzr_kit.commands.agent_set.PlatformClient")
    def test_set_succeeds_with_valid_subagents(self, mock_platform, mock_auth):
        """set should succeed when all sub_agents exist locally."""
        from lyzr_kit.utils.auth import AuthConfig
        from lyzr_kit.utils.platform import AgentResponse

        mock_auth.return_value = AuthConfig(api_key="test-key")
        mock_platform.return_value.update_agent.return_value = AgentResponse(
            agent_id="plat-123",
            env_id="env-456",
            endpoint="http://test.endpoint",
            platform_url="http://platform.url",
        )

        storage = StorageManager()

        # Create a valid sub-agent first
        sub_agent = create_test_agent("valid-sub-for-set")
        storage.save_agent(sub_agent)

        # Create parent with valid sub-agent
        parent = create_test_agent("parent-with-valid-sub", sub_agents=["valid-sub-for-set"])
        storage.save_agent(parent)

        # Set should succeed
        result = runner.invoke(app, ["agent", "set", "parent-with-valid-sub"])
        assert result.exit_code == 0
        assert "updated successfully" in result.output

    @patch("lyzr_kit.commands.agent_set.require_auth")
    @patch("lyzr_kit.commands.agent_set.PlatformClient")
    def test_set_updates_subagent_references_on_id_change(self, mock_platform, mock_auth):
        """set should update sub-agent references when ID changes."""
        import uuid

        from lyzr_kit.utils.auth import AuthConfig
        from lyzr_kit.utils.platform import AgentResponse

        mock_auth.return_value = AuthConfig(api_key="test-key")
        mock_platform.return_value.update_agent.return_value = AgentResponse(
            agent_id="plat-123",
            env_id="env-456",
            endpoint="http://test.endpoint",
            platform_url="http://platform.url",
        )

        storage = StorageManager()

        # Use unique IDs to avoid conflicts with leftover test files
        unique_suffix = str(uuid.uuid4())[:8]
        old_id = f"old-sub-{unique_suffix}"
        new_id = f"new-sub-{unique_suffix}"
        parent_id = f"parent-ref-{unique_suffix}"

        # Create a sub-agent with original ID
        sub_agent = create_test_agent(old_id)
        storage.save_agent(sub_agent)

        # Create a parent that references it
        parent = create_test_agent(parent_id, sub_agents=[old_id])
        storage.save_agent(parent)

        # Manually change the sub-agent's ID in the YAML file
        yaml_path = Path.cwd() / "agents" / f"{old_id}.yaml"
        content = yaml_path.read_text()
        content = content.replace(f"id: {old_id}", f"id: {new_id}")
        yaml_path.write_text(content)

        # Run set on the renamed agent
        result = runner.invoke(app, ["agent", "set", old_id])
        assert result.exit_code == 0, (
            f"Expected 0 but got {result.exit_code}. Output: {result.output}"
        )
        assert "updated successfully" in result.output
        assert "Updated sub-agent references" in result.output
        assert parent_id in result.output

        # Verify parent's sub_agents array was updated
        updated_parent = storage.get_agent(parent_id)
        assert updated_parent is not None
        assert new_id in updated_parent.sub_agents
        assert old_id not in updated_parent.sub_agents

        # Verify old file was deleted and new file exists
        assert not (Path.cwd() / "agents" / f"{old_id}.yaml").exists()
        assert storage.agent_exists_local(new_id)

        # Clean up
        storage.delete_agent(new_id)
        storage.delete_agent(parent_id)


class TestAgentGetWithSubAgents:
    """Tests for 'lk agent get' command with sub-agent resolution."""

    def test_get_help_shows_subagent_behavior(self):
        """get help should work correctly."""
        result = runner.invoke(app, ["agent", "get", "--help"])
        assert result.exit_code == 0
        assert "source" in result.output.lower() or "built-in" in result.output.lower()

    def test_builtin_agents_with_subagents_exist(self):
        """Built-in agents with sub-agents should be accessible."""
        storage = StorageManager()

        # Verify project-manager has sub_agents
        pm = storage.get_agent("project-manager")
        assert pm is not None
        assert len(pm.sub_agents) == 3

        # Verify dev-lead has sub_agents
        dl = storage.get_agent("dev-lead")
        assert dl is not None
        assert len(dl.sub_agents) == 2

        # Verify tech-director has nested sub_agents
        td = storage.get_agent("tech-director")
        assert td is not None
        assert len(td.sub_agents) == 2


class TestAgentLsWithSubAgents:
    """Tests for 'lk agent ls' command showing agents with sub-agents."""

    def test_ls_shows_builtin_agents_with_subagents(self):
        """ls should show built-in agents including those with sub-agents."""
        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        assert "project-manager" in result.output
        assert "dev-lead" in result.output
        assert "tech-director" in result.output

    def test_ls_shows_local_agents_with_subagents(self):
        """ls should show local agents that have sub-agents."""
        storage = StorageManager()

        # Create a local agent with sub_agents
        agent = create_test_agent(
            "local-with-subs",
            name="Local With Subs",
            sub_agents=["some-sub-agent"],
        )
        storage.save_agent(agent)

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        # ID may be truncated in narrow terminals, so check partial match
        assert "local-with-su" in result.output


class TestSubAgentSchemaValidation:
    """Tests for sub_agents field in Agent schema."""

    def test_agent_schema_accepts_sub_agents_list(self):
        """Agent schema should accept sub_agents as list of strings."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["agent-1", "agent-2", "agent-3"],
        )
        assert agent.sub_agents == ["agent-1", "agent-2", "agent-3"]

    def test_agent_schema_defaults_to_empty_list(self):
        """Agent schema should default sub_agents to empty list."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )
        assert agent.sub_agents == []

    def test_agent_with_subagents_saves_and_loads(self):
        """Agent with sub_agents should save and load correctly."""
        storage = StorageManager()

        agent = create_test_agent("roundtrip-test", sub_agents=["sub-1", "sub-2"])
        storage.save_agent(agent)

        loaded = storage.get_agent("roundtrip-test")
        assert loaded is not None
        assert loaded.sub_agents == ["sub-1", "sub-2"]


class TestCopyOfIdGeneration:
    """Tests for copy-of-<name> ID generation."""

    def test_generate_copy_id_basic(self):
        """Should generate copy-of-<name> ID."""
        from lyzr_kit.commands.agent_get import _generate_copy_id

        storage = StorageManager()
        result = _generate_copy_id("chat-agent", storage)
        assert result == "copy-of-chat-agent"

    def test_generate_copy_id_handles_conflict(self):
        """Should add suffix on conflict."""
        from lyzr_kit.commands.agent_get import _generate_copy_id

        storage = StorageManager()

        # Create an agent with copy-of-chat-agent ID
        agent = create_test_agent("copy-of-chat-agent")
        storage.save_agent(agent)

        result = _generate_copy_id("chat-agent", storage)
        assert result == "copy-of-chat-agent-2"

    def test_generate_copy_id_handles_multiple_conflicts(self):
        """Should increment suffix until unique."""
        from lyzr_kit.commands.agent_get import _generate_copy_id

        storage = StorageManager()

        # Create agents with conflicting IDs
        storage.save_agent(create_test_agent("copy-of-test"))
        storage.save_agent(create_test_agent("copy-of-test-2"))
        storage.save_agent(create_test_agent("copy-of-test-3"))

        result = _generate_copy_id("test", storage)
        assert result == "copy-of-test-4"


class TestAgentTreeCommand:
    """Tests for lk agent tree command."""

    def test_tree_help(self):
        """tree --help should show command description."""
        result = runner.invoke(app, ["agent", "tree", "--help"])
        assert result.exit_code == 0
        assert "dependency" in result.output.lower() or "tree" in result.output.lower()

    def test_tree_shows_agent_hierarchy(self):
        """tree should show agent and its sub-agents."""
        storage = StorageManager()

        # Create parent with sub-agents
        sub1 = create_test_agent("sub-agent-1")
        sub2 = create_test_agent("sub-agent-2")
        storage.save_agent(sub1)
        storage.save_agent(sub2)

        parent = create_test_agent("parent-agent", sub_agents=["sub-agent-1", "sub-agent-2"])
        storage.save_agent(parent)

        result = runner.invoke(app, ["agent", "tree", "parent-agent"])
        assert result.exit_code == 0
        assert "parent-agent" in result.output
        assert "sub-agent-1" in result.output
        assert "sub-agent-2" in result.output

    def test_tree_shows_missing_sub_agents(self):
        """tree should indicate missing sub-agents."""
        storage = StorageManager()

        parent = create_test_agent("parent-with-missing", sub_agents=["missing-sub"])
        storage.save_agent(parent)

        result = runner.invoke(app, ["agent", "tree", "parent-with-missing"])
        assert result.exit_code == 0
        assert "missing" in result.output.lower()


class TestAgentDoctorCommand:
    """Tests for lk agent doctor command."""

    def test_doctor_help(self):
        """doctor --help should show command description."""
        result = runner.invoke(app, ["agent", "doctor", "--help"])
        assert result.exit_code == 0
        assert "Check" in result.output or "sub-agents" in result.output

    def test_doctor_passes_with_healthy_agents(self):
        """doctor should pass when all agents are healthy."""
        storage = StorageManager()

        agent = create_test_agent("healthy-agent")
        agent.is_active = True
        agent.platform_agent_id = "platform-123"
        storage.save_agent(agent)

        result = runner.invoke(app, ["agent", "doctor"])
        assert result.exit_code == 0
        assert "healthy" in result.output.lower()

    def test_doctor_detects_missing_sub_agents(self):
        """doctor should detect missing sub-agents."""
        storage = StorageManager()

        agent = create_test_agent("broken-agent", sub_agents=["missing-sub"])
        agent.is_active = True
        agent.platform_agent_id = "platform-123"
        storage.save_agent(agent)

        result = runner.invoke(app, ["agent", "doctor"])
        assert result.exit_code == 1
        assert "missing" in result.output.lower() or "not found" in result.output.lower()


class TestAgentRmTreeFlag:
    """Tests for lk agent rm --tree flag."""

    def test_rm_help_shows_tree_flag(self):
        """rm --help should show --tree option."""
        result = runner.invoke(app, ["agent", "rm", "--help"])
        assert result.exit_code == 0
        # Check for 'tree' - ANSI codes may split '--tree' in output
        assert "tree" in result.output.lower()
        assert "sub-agents" in result.output.lower()

    def test_rm_shows_sub_agents_hint(self):
        """rm should show hint about sub-agents when not using --tree."""
        storage = StorageManager()

        sub = create_test_agent("sub-for-rm")
        storage.save_agent(sub)

        parent = create_test_agent("parent-for-rm", sub_agents=["sub-for-rm"])
        storage.save_agent(parent)

        result = runner.invoke(app, ["agent", "rm", "parent-for-rm"])
        assert "sub-agent" in result.output.lower()
        # Check for 'tree' - ANSI codes may split '--tree' in output
        assert "tree" in result.output.lower()

    def test_rm_tree_deletes_sub_agents(self):
        """rm --tree should delete agent and sub-agents."""
        storage = StorageManager()

        sub = create_test_agent("sub-to-delete")
        storage.save_agent(sub)

        parent = create_test_agent("parent-to-delete", sub_agents=["sub-to-delete"])
        storage.save_agent(parent)

        result = runner.invoke(app, ["agent", "rm", "parent-to-delete", "--tree"])
        assert result.exit_code == 0
        assert "deleted" in result.output.lower()

        # Verify both are gone
        assert not storage.agent_exists_local("parent-to-delete")
        assert not storage.agent_exists_local("sub-to-delete")
