"""Core storage manager for lyzr-kit resources."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import ValidationError

from lyzr_kit.schemas.agent import Agent

# Built-in resources bundled with the package
COLLECTION_DIR = Path(__file__).parent.parent / "collection"


class AgentLoadError(Exception):
    """Raised when loading an agent fails."""

    def __init__(
        self, message: str, yaml_error: bool = False, schema_error: ValidationError | None = None
    ):
        super().__init__(message)
        self.yaml_error = yaml_error
        self.schema_error = schema_error


class StorageManager:
    """Manages storage for agents, tools, and features."""

    def __init__(
        self,
        builtin_path: str | Path | None = None,
        local_path: str | Path | None = None,
    ) -> None:
        """Initialize storage manager.

        Args:
            builtin_path: Path to built-in resources. Defaults to package collection.
            local_path: Path to local resources. Defaults to current working directory.
        """
        self.builtin_path = Path(builtin_path) if builtin_path else COLLECTION_DIR
        try:
            self.local_path = Path(local_path) if local_path else Path.cwd()
        except (FileNotFoundError, OSError):
            self.local_path = Path(".")

    def _ensure_local_dir(self, resource_type: str) -> Path:
        """Ensure local directory exists for resource type."""
        path = self.local_path / resource_type
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _list_yaml_files(self, directory: Path) -> list[Path]:
        """List all YAML files in a directory."""
        if not directory.exists() or not directory.is_dir():
            return []
        try:
            return list(directory.glob("*.yaml"))
        except OSError:
            return []

    def _load_agent(self, path: Path, raise_on_error: bool = False) -> Agent | None:
        """Load an agent from a YAML file.

        Args:
            path: Path to the YAML file.
            raise_on_error: If True, raise AgentLoadError on failure.
                           If False, silently return None.

        Returns:
            Agent object or None (if raise_on_error=False and loading fails).

        Raises:
            AgentLoadError: If raise_on_error=True and loading fails.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            if data is None:
                if raise_on_error:
                    raise AgentLoadError(f"Empty YAML file: {path.name}", yaml_error=True)
                return None

            return Agent.model_validate(data)

        except yaml.YAMLError as e:
            if raise_on_error:
                raise AgentLoadError(f"Invalid YAML syntax: {e}", yaml_error=True) from e
            return None

        except ValidationError as e:
            if raise_on_error:
                raise AgentLoadError(
                    f"Schema validation failed for {path.name}", schema_error=e
                ) from e
            return None

        except Exception as e:
            if raise_on_error:
                raise AgentLoadError(f"Failed to load {path.name}: {e}") from e
            return None

    def list_agents(
        self, source: Literal["all", "built-in", "local"] = "all"
    ) -> list[tuple[Agent, str]]:
        """List agents from built-in and/or local directories.

        Args:
            source: Filter by source - "all", "built-in", or "local".

        Returns:
            List of tuples containing (agent, source_type) where source_type is
            "built-in" or "local". Sorted by serial number.
        """
        agents: list[tuple[Agent, str]] = []

        # Built-in agents
        if source in ("all", "built-in"):
            builtin_dir = self.builtin_path / "agents"
            for yaml_file in self._list_yaml_files(builtin_dir):
                agent = self._load_agent(yaml_file)
                if agent:
                    agents.append((agent, "built-in"))

        # Local agents
        if source in ("all", "local"):
            local_dir = self.local_path / "agents"
            for yaml_file in self._list_yaml_files(local_dir):
                agent = self._load_agent(yaml_file)
                if agent:
                    agents.append((agent, "local"))

        # Sort: built-in first (by serial), then local (by serial)
        def sort_key(item: tuple[Agent, str]) -> tuple[int, int]:
            agent, src = item
            serial = agent.serial if agent.serial is not None else 999999
            # Built-in = 0, local = 1 (so built-in comes first)
            source_order = 0 if src == "built-in" else 1
            return (source_order, serial)

        agents.sort(key=sort_key)
        return agents

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get an agent by ID from local or built-in directory.

        Searches all YAML files and matches by the 'id' field inside the file.
        Local agents take precedence over built-in agents.
        """
        # Check local first
        local_dir = self.local_path / "agents"
        for yaml_file in self._list_yaml_files(local_dir):
            agent = self._load_agent(yaml_file)
            if agent and agent.id == agent_id:
                return agent

        # Check built-in
        builtin_dir = self.builtin_path / "agents"
        for yaml_file in self._list_yaml_files(builtin_dir):
            agent = self._load_agent(yaml_file)
            if agent and agent.id == agent_id:
                return agent

        return None

    def save_agent(self, agent: Agent) -> Path:
        """Save an agent to local directory.

        Adds a comment warning not to modify the serial number.
        """
        self._ensure_local_dir("agents")
        path = self.local_path / "agents" / f"{agent.id}.yaml"

        data = agent.model_dump(exclude_none=True, exclude_unset=False)
        # Convert datetime to ISO format string
        for key in ["created_at", "updated_at"]:
            if key in data and data[key] is not None:
                data[key] = data[key].isoformat()

        with open(path, "w") as f:
            f.write("# WARNING: Do NOT modify the 'serial' field below\n")
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return path

    def agent_exists(
        self, agent_id: str, source: Literal["all", "built-in", "local"] = "all"
    ) -> bool:
        """Check if agent exists in built-in and/or local directory.

        Args:
            agent_id: The agent ID to check.
            source: Where to search - "all", "built-in", or "local".

        Returns:
            True if agent exists in the specified location(s).
        """
        # Check local
        if source in ("all", "local"):
            local_dir = self.local_path / "agents"
            for yaml_file in self._list_yaml_files(local_dir):
                agent = self._load_agent(yaml_file)
                if agent and agent.id == agent_id:
                    return True

        # Check built-in
        if source in ("all", "built-in"):
            builtin_dir = self.builtin_path / "agents"
            for yaml_file in self._list_yaml_files(builtin_dir):
                agent = self._load_agent(yaml_file)
                if agent and agent.id == agent_id:
                    return True

        return False

    def agent_exists_local(self, agent_id: str) -> bool:
        """Check if agent exists in local directory.

        Note: This is a convenience method. Equivalent to agent_exists(id, source="local").
        """
        return self.agent_exists(agent_id, source="local")

    def list_local_agents(self) -> list[Agent]:
        """List all local agents.

        Note: This is a convenience method. Equivalent to list_agents(source="local").

        Returns:
            List of Agent objects from local directory.
        """
        return [agent for agent, _ in self.list_agents(source="local")]

    def find_agents_using_subagent(self, agent_id: str) -> list[Agent]:
        """Find all local agents that reference agent_id in their sub_agents.

        Args:
            agent_id: The agent ID to search for in sub_agents arrays.

        Returns:
            List of agents that use the given agent_id as a sub-agent.
        """
        using_agents: list[Agent] = []
        for agent in self.list_local_agents():
            if agent_id in agent.sub_agents:
                using_agents.append(agent)
        return using_agents

    def update_subagent_references(self, old_id: str, new_id: str) -> list[str]:
        """Update all sub_agents arrays from old_id to new_id.

        Args:
            old_id: The old agent ID to replace.
            new_id: The new agent ID to use.

        Returns:
            List of agent IDs that were updated.
        """
        updated_agents: list[str] = []
        local_dir = self.local_path / "agents"

        for yaml_file in self._list_yaml_files(local_dir):
            agent = self._load_agent(yaml_file)
            if agent and old_id in agent.sub_agents:
                # Update the sub_agents array
                agent.sub_agents = [new_id if sid == old_id else sid for sid in agent.sub_agents]
                # Save the updated agent
                self.save_agent(agent)
                updated_agents.append(agent.id)

        return updated_agents

    def delete_agent(self, agent_id: str) -> bool:
        """Delete a local agent YAML file.

        Args:
            agent_id: The agent ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        local_dir = self.local_path / "agents"
        yaml_path = local_dir / f"{agent_id}.yaml"

        if yaml_path.exists():
            yaml_path.unlink()
            return True
        return False
