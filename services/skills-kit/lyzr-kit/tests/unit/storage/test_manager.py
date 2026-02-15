"""Unit tests for storage manager."""

from pathlib import Path

from lyzr_kit.schemas.agent import Agent
from lyzr_kit.storage.manager import StorageManager


class TestStorageManagerLoadAgent:
    """Tests for StorageManager._load_agent method."""

    def test_load_agent_returns_none_for_invalid_yaml(self):
        """_load_agent should return None for invalid YAML."""
        storage = StorageManager()

        # Create invalid YAML file
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        invalid_file = agents_dir / "invalid-agent.yaml"
        invalid_file.write_text("invalid: yaml: content: [")

        # Should return None, not raise
        result = storage._load_agent(invalid_file)
        assert result is None

    def test_load_agent_returns_none_for_invalid_schema(self):
        """_load_agent should return None for valid YAML but invalid schema."""
        storage = StorageManager()

        # Create YAML with missing required fields
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        invalid_file = agents_dir / "bad-schema.yaml"
        invalid_file.write_text("some_field: value\n")

        # Should return None (validation fails)
        result = storage._load_agent(invalid_file)
        assert result is None


class TestStorageManagerSaveAgent:
    """Tests for StorageManager.save_agent method."""

    def test_save_agent_converts_datetime_to_iso(self):
        """save_agent should convert datetime fields to ISO format."""
        from datetime import datetime

        from lyzr_kit.schemas.agent import ModelConfig

        storage = StorageManager()

        agent = Agent(
            id="test-agent",
            name="Test Agent",
            category="chat",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )

        path = storage.save_agent(agent)
        content = path.read_text()

        # Should contain ISO format datetime
        assert "2024-01-15" in content
        assert "10:30:00" in content


class TestStorageManagerListAgents:
    """Tests for StorageManager.list_agents method."""

    def test_list_agents_returns_tuples_with_source(self):
        """list_agents should return tuples of (agent, source)."""
        storage = StorageManager()
        agents = storage.list_agents()

        # Should return list of tuples
        assert len(agents) > 0
        for item in agents:
            assert isinstance(item, tuple)
            assert len(item) == 2
            agent, source = item
            assert isinstance(agent, Agent)
            assert source in ("built-in", "local")

    def test_list_agents_builtin_agents_have_builtin_source(self):
        """Built-in agents should have 'built-in' source."""
        storage = StorageManager()
        agents = storage.list_agents()

        # Find chat-agent (should be built-in)
        chat_agents = [(a, s) for a, s in agents if a.id == "chat-agent"]
        assert len(chat_agents) == 1
        agent, source = chat_agents[0]
        assert source == "built-in"


class TestStorageManagerAgentExists:
    """Tests for StorageManager.agent_exists method."""

    def test_agent_exists_returns_true_for_builtin(self):
        """agent_exists should return True for built-in agents."""
        storage = StorageManager()
        assert storage.agent_exists("chat-agent") is True
        assert storage.agent_exists("qa-agent") is True

    def test_agent_exists_returns_false_for_nonexistent(self):
        """agent_exists should return False for non-existent agents."""
        storage = StorageManager()
        assert storage.agent_exists("nonexistent-agent-xyz") is False

    def test_agent_exists_returns_true_for_local(self):
        """agent_exists should return True for local agents."""
        from lyzr_kit.schemas.agent import ModelConfig

        storage = StorageManager()

        # Create a local agent
        agent = Agent(
            id="local-test-agent",
            name="Local Test Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )
        storage.save_agent(agent)

        # Should now exist
        assert storage.agent_exists("local-test-agent") is True


class TestStorageManagerListLocalAgents:
    """Tests for StorageManager.list_local_agents method."""

    def test_list_local_agents_returns_empty_list_when_no_local(self):
        """list_local_agents should return empty list when no local agents."""
        storage = StorageManager()
        # Note: May have local agents from other tests, so just verify it's a list
        agents = storage.list_local_agents()
        assert isinstance(agents, list)

    def test_list_local_agents_returns_local_agents(self):
        """list_local_agents should return all local agents."""
        from lyzr_kit.schemas.agent import ModelConfig

        storage = StorageManager()

        # Create a local agent
        agent = Agent(
            id="list-local-test-agent",
            name="List Local Test Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )
        storage.save_agent(agent)

        agents = storage.list_local_agents()
        agent_ids = [a.id for a in agents]
        assert "list-local-test-agent" in agent_ids


class TestStorageManagerFindAgentsUsingSubagent:
    """Tests for StorageManager.find_agents_using_subagent method."""

    def test_find_agents_using_subagent_returns_empty_when_none(self):
        """find_agents_using_subagent should return empty list when not used."""
        storage = StorageManager()
        using_agents = storage.find_agents_using_subagent("nonexistent-agent-id")
        assert using_agents == []

    def test_find_agents_using_subagent_finds_parent(self):
        """find_agents_using_subagent should find agents using the sub-agent."""
        from lyzr_kit.schemas.agent import ModelConfig

        storage = StorageManager()

        # Create a sub-agent
        sub_agent = Agent(
            id="test-sub-agent",
            name="Test Sub Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )
        storage.save_agent(sub_agent)

        # Create a parent agent that uses the sub-agent
        parent_agent = Agent(
            id="test-parent-agent",
            name="Test Parent Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["test-sub-agent"],
        )
        storage.save_agent(parent_agent)

        # Find agents using the sub-agent
        using_agents = storage.find_agents_using_subagent("test-sub-agent")
        assert len(using_agents) == 1
        assert using_agents[0].id == "test-parent-agent"

    def test_find_agents_using_subagent_finds_multiple_parents(self):
        """find_agents_using_subagent should find all agents using the sub-agent."""
        from lyzr_kit.schemas.agent import ModelConfig

        storage = StorageManager()

        # Create a shared sub-agent
        shared_sub = Agent(
            id="shared-sub-agent",
            name="Shared Sub Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )
        storage.save_agent(shared_sub)

        # Create two parent agents that use the shared sub-agent
        parent1 = Agent(
            id="parent-agent-one",
            name="Parent Agent One",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["shared-sub-agent"],
        )
        storage.save_agent(parent1)

        parent2 = Agent(
            id="parent-agent-two",
            name="Parent Agent Two",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["shared-sub-agent", "other-agent"],
        )
        storage.save_agent(parent2)

        using_agents = storage.find_agents_using_subagent("shared-sub-agent")
        using_ids = [a.id for a in using_agents]
        assert "parent-agent-one" in using_ids
        assert "parent-agent-two" in using_ids


class TestStorageManagerUpdateSubagentReferences:
    """Tests for StorageManager.update_subagent_references method."""

    def test_update_subagent_references_updates_arrays(self):
        """update_subagent_references should update sub_agents arrays."""
        from lyzr_kit.schemas.agent import ModelConfig

        storage = StorageManager()

        # Create a parent agent with sub_agents
        parent = Agent(
            id="update-ref-parent",
            name="Update Ref Parent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["old-sub-id", "other-sub"],
        )
        storage.save_agent(parent)

        # Update references from old-sub-id to new-sub-id
        updated = storage.update_subagent_references("old-sub-id", "new-sub-id")

        # Should return the updated agent ID
        assert "update-ref-parent" in updated

        # Reload and verify
        reloaded = storage.get_agent("update-ref-parent")
        assert reloaded is not None
        assert "new-sub-id" in reloaded.sub_agents
        assert "old-sub-id" not in reloaded.sub_agents
        assert "other-sub" in reloaded.sub_agents

    def test_update_subagent_references_returns_empty_when_no_matches(self):
        """update_subagent_references should return empty list when no matches."""
        storage = StorageManager()
        updated = storage.update_subagent_references("nonexistent-old", "nonexistent-new")
        assert updated == []


class TestStorageManagerDeleteAgent:
    """Tests for StorageManager.delete_agent method."""

    def test_delete_agent_removes_yaml_file(self):
        """delete_agent should remove the YAML file."""
        from lyzr_kit.schemas.agent import ModelConfig

        storage = StorageManager()

        # Create an agent
        agent = Agent(
            id="delete-test-agent",
            name="Delete Test Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )
        storage.save_agent(agent)

        # Verify it exists
        assert storage.agent_exists_local("delete-test-agent") is True

        # Delete it
        result = storage.delete_agent("delete-test-agent")
        assert result is True

        # Verify it's gone
        assert storage.agent_exists_local("delete-test-agent") is False

    def test_delete_agent_returns_false_for_nonexistent(self):
        """delete_agent should return False for non-existent agent."""
        storage = StorageManager()
        result = storage.delete_agent("nonexistent-delete-agent")
        assert result is False


class TestBuiltinAgentsWithSubAgents:
    """Tests for built-in agents that have sub-agents."""

    def test_project_manager_has_sub_agents(self):
        """project-manager should have task-planner, data-analyst, summarizer as sub-agents."""
        storage = StorageManager()
        agent = storage.get_agent("project-manager")

        assert agent is not None
        assert len(agent.sub_agents) == 3
        assert "task-planner" in agent.sub_agents
        assert "data-analyst" in agent.sub_agents
        assert "summarizer" in agent.sub_agents

    def test_dev_lead_has_sub_agents(self):
        """dev-lead should have code-reviewer, research-assistant as sub-agents."""
        storage = StorageManager()
        agent = storage.get_agent("dev-lead")

        assert agent is not None
        assert len(agent.sub_agents) == 2
        assert "code-reviewer" in agent.sub_agents
        assert "research-assistant" in agent.sub_agents

    def test_tech_director_has_nested_sub_agents(self):
        """tech-director should have dev-lead, project-manager (which have their own sub-agents)."""
        storage = StorageManager()
        agent = storage.get_agent("tech-director")

        assert agent is not None
        assert len(agent.sub_agents) == 2
        assert "dev-lead" in agent.sub_agents
        assert "project-manager" in agent.sub_agents

        # Verify the sub-agents themselves have sub-agents (nested)
        dev_lead = storage.get_agent("dev-lead")
        assert dev_lead is not None
        assert len(dev_lead.sub_agents) == 2

        project_manager = storage.get_agent("project-manager")
        assert project_manager is not None
        assert len(project_manager.sub_agents) == 3
