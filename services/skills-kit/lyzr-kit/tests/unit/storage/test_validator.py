"""Unit tests for storage validator."""

from pathlib import Path

from pydantic import ValidationError

from lyzr_kit.schemas.agent import Agent
from lyzr_kit.storage.validator import (
    ValidationResult,
    detect_cycle,
    format_cycle_error,
    format_schema_errors,
    format_subagent_errors,
    format_validation_errors,
    validate_agent_yaml_file,
    validate_agents_folder,
    validate_sub_agents,
)


class TestValidateAgentsFolder:
    """Tests for validate_agents_folder function."""

    def test_valid_empty_folder(self):
        """Empty agents folder should be valid."""
        # ..local-kit/agents doesn't exist yet
        result = validate_agents_folder(Path.cwd() / "..local-kit")
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_valid_with_yaml_files(self):
        """Folder with valid YAML files should be valid."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Create valid agent YAML
        valid_yaml = agents_dir / "test-agent.yaml"
        valid_yaml.write_text("""
id: test-agent
name: Test Agent
category: chat
model:
  provider: openai
  name: gpt-4
  credential_id: cred-1
""")

        result = validate_agents_folder(Path.cwd() / ".local-kit")
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_detects_nested_folders(self):
        """Should detect nested folders as invalid."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Create nested folder
        nested_dir = agents_dir / "nested-folder"
        nested_dir.mkdir()

        result = validate_agents_folder(Path.cwd() / ".local-kit")
        assert result.is_valid is False
        assert len(result.nested_folders) == 1
        assert result.nested_folders[0].name == "nested-folder"

    def test_detects_multiple_nested_folders(self):
        """Should detect all nested folders."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple nested folders
        (agents_dir / "folder1").mkdir()
        (agents_dir / "folder2").mkdir()

        result = validate_agents_folder(Path.cwd() / ".local-kit")
        assert result.is_valid is False
        assert len(result.nested_folders) == 2

    def test_detects_invalid_file_extensions(self):
        """Should detect non-YAML files as invalid."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Create invalid files
        (agents_dir / "readme.txt").write_text("some text")
        (agents_dir / "config.json").write_text("{}")

        result = validate_agents_folder(Path.cwd() / ".local-kit")
        assert result.is_valid is False
        assert len(result.invalid_extensions) == 2

    def test_detects_invalid_yaml_syntax(self):
        """Should detect YAML files with invalid syntax."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Create invalid YAML
        invalid_yaml = agents_dir / "broken.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [")

        result = validate_agents_folder(Path.cwd() / ".local-kit")
        assert result.is_valid is False
        assert len(result.invalid_yaml_files) == 1
        assert result.invalid_yaml_files[0].name == "broken.yaml"

    def test_detects_empty_yaml_file(self):
        """Should detect empty YAML files as invalid."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Create empty YAML
        empty_yaml = agents_dir / "empty.yaml"
        empty_yaml.write_text("")

        result = validate_agents_folder(Path.cwd() / ".local-kit")
        assert result.is_valid is False
        assert len(result.invalid_yaml_files) == 1

    def test_detects_invalid_schema(self):
        """Should detect YAML files that don't match Agent schema."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Create YAML with missing required fields
        invalid_schema = agents_dir / "bad-schema.yaml"
        invalid_schema.write_text("""
some_field: value
other_field: 123
""")

        result = validate_agents_folder(Path.cwd() / ".local-kit")
        assert result.is_valid is False
        assert len(result.invalid_schema_files) == 1
        assert result.invalid_schema_files[0].name == "bad-schema.yaml"

    def test_detects_all_issue_types(self):
        """Should detect all types of issues in one validation."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Create nested folder
        (agents_dir / "nested").mkdir()

        # Create invalid extension file
        (agents_dir / "readme.txt").write_text("text")

        # Create invalid YAML
        (agents_dir / "broken.yaml").write_text("invalid: yaml: [")

        # Create invalid schema
        (agents_dir / "bad-schema.yaml").write_text("field: value")

        result = validate_agents_folder(Path.cwd() / ".local-kit")
        assert result.is_valid is False
        assert len(result.nested_folders) == 1
        assert len(result.invalid_extensions) == 1
        assert len(result.invalid_yaml_files) == 1
        assert len(result.invalid_schema_files) == 1


class TestFormatValidationErrors:
    """Tests for format_validation_errors function."""

    def test_empty_result_returns_empty_string(self):
        """Valid result should return empty string."""
        result = ValidationResult(is_valid=True)
        output = format_validation_errors(result)
        assert output == ""

    def test_formats_nested_folders(self):
        """Should format nested folder errors."""
        result = ValidationResult(is_valid=False)
        result.nested_folders = [Path(".local-kit/agents/nested")]
        result.issues = [None]  # type: ignore  # Just to make is_valid=False work

        output = format_validation_errors(result)
        assert "Nested folders" in output
        assert "nested" in output

    def test_formats_invalid_extensions(self):
        """Should format invalid extension errors."""
        result = ValidationResult(is_valid=False)
        result.invalid_extensions = [Path(".local-kit/agents/readme.txt")]
        result.issues = [None]  # type: ignore

        output = format_validation_errors(result)
        assert "Invalid file extensions" in output
        assert "readme.txt" in output

    def test_formats_invalid_yaml(self):
        """Should format invalid YAML errors."""
        result = ValidationResult(is_valid=False)
        result.invalid_yaml_files = [Path(".local-kit/agents/broken.yaml")]
        result.issues = [None]  # type: ignore

        output = format_validation_errors(result)
        assert "Invalid YAML syntax" in output
        assert "broken.yaml" in output

    def test_formats_invalid_schema(self):
        """Should format invalid schema errors."""
        result = ValidationResult(is_valid=False)
        result.invalid_schema_files = [Path(".local-kit/agents/bad.yaml")]
        result.issues = [None]  # type: ignore

        output = format_validation_errors(result)
        assert "Invalid agent schema" in output
        assert "bad.yaml" in output


class TestValidateAgentYamlFile:
    """Tests for validate_agent_yaml_file function."""

    def test_returns_agent_for_valid_yaml(self):
        """Should return Agent for valid YAML file."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        valid_yaml = agents_dir / "valid-agent.yaml"
        valid_yaml.write_text("""
id: valid-agent
name: Valid Agent
category: chat
model:
  provider: openai
  name: gpt-4
  credential_id: cred-1
""")

        agent, schema_error, yaml_error = validate_agent_yaml_file(valid_yaml)

        assert agent is not None
        assert agent.id == "valid-agent"
        assert schema_error is None
        assert yaml_error is None

    def test_returns_yaml_error_for_invalid_syntax(self):
        """Should return yaml error for invalid YAML syntax."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        invalid_yaml = agents_dir / "broken.yaml"
        invalid_yaml.write_text("invalid: yaml: [")

        agent, schema_error, yaml_error = validate_agent_yaml_file(invalid_yaml)

        assert agent is None
        assert schema_error is None
        assert yaml_error is not None
        assert "Invalid YAML syntax" in yaml_error

    def test_returns_schema_error_for_invalid_schema(self):
        """Should return schema error for invalid Agent schema."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        bad_schema = agents_dir / "bad-schema.yaml"
        bad_schema.write_text("field: value\nother: 123\n")

        agent, schema_error, yaml_error = validate_agent_yaml_file(bad_schema)

        assert agent is None
        assert schema_error is not None
        assert yaml_error is None

    def test_returns_yaml_error_for_empty_file(self):
        """Should return yaml error for empty YAML file."""
        agents_dir = Path.cwd() / ".local-kit" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        empty_yaml = agents_dir / "empty.yaml"
        empty_yaml.write_text("")

        agent, schema_error, yaml_error = validate_agent_yaml_file(empty_yaml)

        assert agent is None
        assert schema_error is None
        assert yaml_error is not None
        assert "Empty YAML file" in yaml_error


class TestFormatSchemaErrors:
    """Tests for format_schema_errors function."""

    def test_formats_missing_field_errors(self):
        """Should format missing required field errors."""
        # Trigger a validation error by validating invalid data
        try:
            Agent.model_validate({"field": "value"})
        except ValidationError as e:
            output = format_schema_errors(e, "test-agent")

        assert "invalid schema" in output
        assert "Expected fields:" in output
        assert "Your file is missing" in output
        assert "id" in output or "name" in output or "category" in output

    def test_includes_agent_id(self):
        """Should include agent ID in error message."""
        try:
            Agent.model_validate({})
        except ValidationError as e:
            output = format_schema_errors(e, "my-custom-agent")

        assert "my-custom-agent" in output

    def test_includes_fix_hint(self):
        """Should include hint to fix and re-run command."""
        try:
            Agent.model_validate({})
        except ValidationError as e:
            output = format_schema_errors(e, "test-agent")

        assert "Fix the YAML file" in output
        assert "lk agent set test-agent" in output


class TestValidateSubAgents:
    """Tests for validate_sub_agents function."""

    def test_returns_empty_list_when_no_sub_agents(self):
        """Should return empty list when sub_agents is empty."""
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()
        missing = validate_sub_agents([], storage)
        assert missing == []

    def test_returns_empty_list_when_all_exist(self):
        """Should return empty list when all sub-agents exist locally."""
        from lyzr_kit.schemas.agent import ModelConfig
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()

        # Create two local agents
        agent1 = Agent(
            id="sub-agent-one",
            name="Sub Agent One",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )
        storage.save_agent(agent1)

        agent2 = Agent(
            id="sub-agent-two",
            name="Sub Agent Two",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )
        storage.save_agent(agent2)

        # Validate - should find both
        missing = validate_sub_agents(["sub-agent-one", "sub-agent-two"], storage)
        assert missing == []

    def test_returns_missing_ids(self):
        """Should return list of missing sub-agent IDs."""
        from lyzr_kit.schemas.agent import ModelConfig
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()

        # Create one local agent
        agent = Agent(
            id="existing-sub-agent",
            name="Existing Sub Agent",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
        )
        storage.save_agent(agent)

        # Validate with one existing and two missing
        missing = validate_sub_agents(
            ["existing-sub-agent", "missing-agent-1", "missing-agent-2"],
            storage,
        )
        assert len(missing) == 2
        assert "missing-agent-1" in missing
        assert "missing-agent-2" in missing
        assert "existing-sub-agent" not in missing

    def test_does_not_validate_against_builtin(self):
        """Should NOT accept built-in agents as valid sub-agents (local only)."""
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()

        # chat-agent is a built-in agent, NOT a local agent
        missing = validate_sub_agents(["chat-agent"], storage)
        assert "chat-agent" in missing


class TestFormatSubagentErrors:
    """Tests for format_subagent_errors function."""

    def test_formats_single_missing_id(self):
        """Should format error for single missing sub-agent ID."""
        output = format_subagent_errors(["missing-agent"])

        assert "Invalid sub-agent IDs" in output
        assert "'missing-agent' not found" in output
        assert "local agents" in output

    def test_formats_multiple_missing_ids(self):
        """Should format error for multiple missing sub-agent IDs."""
        output = format_subagent_errors(["missing-1", "missing-2", "missing-3"])

        assert "Invalid sub-agent IDs" in output
        assert "'missing-1'" in output
        assert "'missing-2'" in output
        assert "'missing-3'" in output

    def test_includes_hint(self):
        """Should include hint about running lk agent ls."""
        output = format_subagent_errors(["missing-agent"])

        assert "lk agent ls" in output


class TestDetectCycle:
    """Tests for detect_cycle function."""

    def test_returns_none_when_no_sub_agents(self):
        """Should return None when there are no sub-agents."""
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()
        cycle = detect_cycle("agent-a", [], storage)
        assert cycle is None

    def test_returns_none_for_acyclic_graph(self):
        """Should return None for valid acyclic sub-agent relationships."""
        from lyzr_kit.schemas.agent import ModelConfig
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()

        # Create chain: A -> B -> C (no cycle)
        agent_c = Agent(
            id="agent-c",
            name="Agent C",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=[],
        )
        storage.save_agent(agent_c)

        agent_b = Agent(
            id="agent-b",
            name="Agent B",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["agent-c"],
        )
        storage.save_agent(agent_b)

        # Check if A can have B as sub-agent (should be acyclic)
        cycle = detect_cycle("agent-a", ["agent-b"], storage)
        assert cycle is None

    def test_detects_direct_cycle(self):
        """Should detect direct cycle: A -> B -> A."""
        from lyzr_kit.schemas.agent import ModelConfig
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()

        # Create B that references A
        agent_b = Agent(
            id="agent-b",
            name="Agent B",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["agent-a"],  # B -> A creates cycle when A -> B
        )
        storage.save_agent(agent_b)

        # Check if A can have B as sub-agent (should detect cycle A -> B -> A)
        cycle = detect_cycle("agent-a", ["agent-b"], storage)
        assert cycle is not None
        assert cycle == ["agent-a", "agent-b", "agent-a"]

    def test_detects_indirect_cycle(self):
        """Should detect indirect cycle: A -> B -> C -> A."""
        from lyzr_kit.schemas.agent import ModelConfig
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()

        # Create chain that eventually loops back to A
        agent_c = Agent(
            id="agent-c",
            name="Agent C",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["agent-a"],  # C -> A creates cycle
        )
        storage.save_agent(agent_c)

        agent_b = Agent(
            id="agent-b",
            name="Agent B",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["agent-c"],  # B -> C
        )
        storage.save_agent(agent_b)

        # Check if A can have B as sub-agent (should detect cycle A -> B -> C -> A)
        cycle = detect_cycle("agent-a", ["agent-b"], storage)
        assert cycle is not None
        assert cycle == ["agent-a", "agent-b", "agent-c", "agent-a"]

    def test_detects_self_reference(self):
        """Should detect self-reference: A -> A."""
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()

        # Check if A can have A as sub-agent (direct self-reference)
        cycle = detect_cycle("agent-a", ["agent-a"], storage)
        assert cycle is not None
        assert cycle == ["agent-a", "agent-a"]

    def test_handles_multiple_sub_agents(self):
        """Should handle multiple sub-agents and find cycle in one branch."""
        from lyzr_kit.schemas.agent import ModelConfig
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()

        # Create agents: B is safe, C creates cycle
        agent_b = Agent(
            id="agent-b",
            name="Agent B",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=[],  # Safe, no sub-agents
        )
        storage.save_agent(agent_b)

        agent_c = Agent(
            id="agent-c",
            name="Agent C",
            category="chat",
            model=ModelConfig(provider="openai", name="gpt-4", credential_id="cred-1"),
            sub_agents=["agent-a"],  # C -> A creates cycle
        )
        storage.save_agent(agent_c)

        # A has both B and C as sub-agents - should detect cycle through C
        cycle = detect_cycle("agent-a", ["agent-b", "agent-c"], storage)
        assert cycle is not None
        assert "agent-a" in cycle
        assert "agent-c" in cycle

    def test_handles_missing_sub_agent(self):
        """Should handle gracefully when sub-agent doesn't exist."""
        from lyzr_kit.storage.manager import StorageManager

        storage = StorageManager()

        # Check with non-existent sub-agent
        cycle = detect_cycle("agent-a", ["non-existent-agent"], storage)
        assert cycle is None  # No cycle if agent doesn't exist


class TestFormatCycleError:
    """Tests for format_cycle_error function."""

    def test_formats_direct_cycle(self):
        """Should format direct cycle error."""
        output = format_cycle_error(["agent-a", "agent-b", "agent-a"])

        assert "Circular sub-agent dependency" in output
        assert "agent-a → agent-b → agent-a" in output
        assert "acyclic" in output

    def test_formats_longer_cycle(self):
        """Should format longer cycle path."""
        output = format_cycle_error(["a", "b", "c", "d", "a"])

        assert "a → b → c → d → a" in output

    def test_includes_fix_hint(self):
        """Should include hint to remove reference."""
        output = format_cycle_error(["agent-a", "agent-b", "agent-a"])

        assert "Remove one of the references" in output
