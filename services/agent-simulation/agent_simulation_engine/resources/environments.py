"""
Environments resource for the Agent Simulation Engine SDK.
"""

from typing import Optional, TYPE_CHECKING

from ..models import (
    Environment,
    EnvironmentCreateResponse,
    DeleteResponse,
)

if TYPE_CHECKING:
    from ..client import ASIMEngine


class Environments:
    """
    Manage environments (world models) for agent testing.

    Usage:
        # Create an environment
        env = client.environments.create(agent_id="...", name="My Tests")

        # Get environment details
        env = client.environments.get(environment_id)

        # List environments for an agent
        envs = client.environments.list_by_agent(agent_id)

        # Delete an environment
        client.environments.delete(environment_id)
    """

    def __init__(self, engine: "ASIMEngine"):
        self._engine = engine

    def create(
        self,
        agent_id: str,
        name: Optional[str] = None,
    ) -> EnvironmentCreateResponse:
        """
        Create a new environment (world model) by cloning an agent.

        Args:
            agent_id: The ID of the agent to create an environment for
            name: Optional name for the environment

        Returns:
            EnvironmentCreateResponse with environment_id, agent_id, name, created_at
        """
        data = {"agent_id": agent_id}
        if name:
            data["name"] = name

        response = self._engine.post("/", json=data)
        return EnvironmentCreateResponse(**response)

    def get(self, environment_id: str) -> Environment:
        """
        Get complete environment with all nested resources.

        Args:
            environment_id: The environment ID

        Returns:
            Environment with full details
        """
        response = self._engine.get(f"/{environment_id}")
        return Environment(**response)

    def list_by_agent(self, agent_id: str) -> list[Environment]:
        """
        Get all environments for a specific agent.

        Args:
            agent_id: The agent ID

        Returns:
            List of environments
        """
        response = self._engine.get(f"/by_agent/{agent_id}")
        return [Environment(**env) for env in response.get("environments", [])]

    def delete(self, environment_id: str) -> DeleteResponse:
        """
        Delete environment and all associated resources.

        Args:
            environment_id: The environment ID

        Returns:
            DeleteResponse with success message
        """
        response = self._engine.delete(f"/{environment_id}")
        return DeleteResponse(**response)
