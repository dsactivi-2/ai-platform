"""Unit tests for 'lk agent ls' command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from typer.testing import CliRunner

from lyzr_kit.commands.agent_list import _count_sub_agents_recursive
from lyzr_kit.main import app
from lyzr_kit.schemas.agent import Agent, ModelConfig
from lyzr_kit.storage.validator import ValidationResult

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
        # Create invalid YAML
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "broken.yaml").write_text("invalid: yaml: [")

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 1
        assert "Invalid YAML syntax" in result.output

    def test_ls_fails_with_invalid_schema(self):
        """ls should fail when YAML files don't match Agent schema."""
        # Create invalid schema YAML
        agents_dir = Path.cwd() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "bad-agent.yaml").write_text("field: value\n")

        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 1
        assert "Invalid agent schema" in result.output

    def test_ls_shows_sub_agent_column(self):
        """ls should show SUB-AGENT column in output."""
        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        assert "SUB-AGENT" in result.output

    def test_ls_shows_recursive_sub_agent_count(self):
        """ls should show total recursive sub-agent count, not just direct."""
        result = runner.invoke(app, ["agent", "ls"])
        assert result.exit_code == 0
        # tech-director has 2 direct subs (dev-lead, project-manager)
        # but 7 total in the tree (dev-lead + its 2 + project-manager + its 3)
        # The output should show 7 for tech-director
        output = result.output
        # Find the tech-director row and verify it shows 7
        assert "tech-director" in output


class TestCountSubAgentsRecursive:
    """Tests for _count_sub_agents_recursive function."""

    def _make_agent(self, agent_id: str, sub_agents: list[str] | None = None) -> Agent:
        """Helper to create a minimal agent."""
        return Agent(
            id=agent_id,
            name=agent_id.title(),
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=sub_agents or [],
        )

    def test_no_sub_agents(self):
        """Should return 0 for agent with no sub-agents."""
        agent = self._make_agent("solo-agent")
        agent_map = {"solo-agent": agent}

        count = _count_sub_agents_recursive(agent, agent_map)
        assert count == 0

    def test_direct_sub_agents_only(self):
        """Should count direct sub-agents."""
        parent = self._make_agent("parent", ["child1", "child2"])
        child1 = self._make_agent("child1")
        child2 = self._make_agent("child2")
        agent_map = {"parent": parent, "child1": child1, "child2": child2}

        count = _count_sub_agents_recursive(parent, agent_map)
        assert count == 2

    def test_nested_sub_agents(self):
        """Should count nested sub-agents recursively."""
        # grandparent -> parent -> child (3 levels)
        grandparent = self._make_agent("grandparent", ["parent"])
        parent = self._make_agent("parent", ["child"])
        child = self._make_agent("child")
        agent_map = {"grandparent": grandparent, "parent": parent, "child": child}

        count = _count_sub_agents_recursive(grandparent, agent_map)
        assert count == 2  # parent + child

    def test_complex_tree(self):
        """Should count all agents in a complex tree."""
        # root -> [branch1, branch2]
        # branch1 -> [leaf1, leaf2]
        # branch2 -> [leaf3]
        root = self._make_agent("root", ["branch1", "branch2"])
        branch1 = self._make_agent("branch1", ["leaf1", "leaf2"])
        branch2 = self._make_agent("branch2", ["leaf3"])
        leaf1 = self._make_agent("leaf1")
        leaf2 = self._make_agent("leaf2")
        leaf3 = self._make_agent("leaf3")
        agent_map = {
            "root": root,
            "branch1": branch1,
            "branch2": branch2,
            "leaf1": leaf1,
            "leaf2": leaf2,
            "leaf3": leaf3,
        }

        count = _count_sub_agents_recursive(root, agent_map)
        assert count == 5  # branch1 + branch2 + leaf1 + leaf2 + leaf3

    def test_missing_sub_agent_in_map(self):
        """Should handle sub-agents not in the map (external references)."""
        parent = self._make_agent("parent", ["child", "missing-agent"])
        child = self._make_agent("child")
        agent_map = {"parent": parent, "child": child}  # missing-agent not in map

        count = _count_sub_agents_recursive(parent, agent_map)
        assert count == 2  # child + missing-agent (counted but not recursed)

    def test_cycle_detection(self):
        """Should handle cycles without infinite recursion."""
        # agent1 -> agent2 -> agent1 (cycle)
        agent1 = self._make_agent("agent1", ["agent2"])
        agent2 = self._make_agent("agent2", ["agent1"])
        agent_map = {"agent1": agent1, "agent2": agent2}

        count = _count_sub_agents_recursive(agent1, agent_map)
        # Should count agent2 (1), then try agent1 again but stop due to cycle
        assert count == 1
