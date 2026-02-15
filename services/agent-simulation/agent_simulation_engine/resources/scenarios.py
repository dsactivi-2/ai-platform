"""
Scenarios resource for the Agent Simulation Engine SDK.
"""

from typing import List, TYPE_CHECKING

from ..models import (
    Scenario,
    ScenariosResponse,
    DeleteResponse,
)

if TYPE_CHECKING:
    from ..client import ASIMEngine


class Scenarios:
    """
    Manage scenarios (task types) for agent testing.

    Usage:
        # Add scenarios manually
        scenarios = client.scenarios.create(
            environment_id,
            scenarios=[
                {"name": "Simple Query", "description": "Basic information request"},
                {"name": "Complex Research", "description": "Multi-step research task"},
            ]
        )

        # Generate scenarios using AI
        scenarios = client.scenarios.generate(environment_id)

        # List all scenarios
        scenarios = client.scenarios.list(environment_id)

        # Delete a scenario
        client.scenarios.delete(environment_id, scenario_id)
    """

    def __init__(self, engine: "ASIMEngine"):
        self._engine = engine

    def create(
        self,
        environment_id: str,
        scenarios: List[dict],
    ) -> ScenariosResponse:
        """
        Add multiple scenarios to an environment.

        Args:
            environment_id: The environment ID
            scenarios: List of scenario dicts with 'name' and 'description'

        Returns:
            ScenariosResponse with list of created scenarios and count
        """
        response = self._engine.post(
            f"/{environment_id}/scenarios",
            json={"scenarios": scenarios}
        )
        return ScenariosResponse(
            scenarios=[Scenario(**s) for s in response.get("scenarios", [])],
            count=response.get("count", 0)
        )

    def list(self, environment_id: str) -> ScenariosResponse:
        """
        Get all scenarios for an environment.

        Args:
            environment_id: The environment ID

        Returns:
            ScenariosResponse with list of scenarios and count
        """
        response = self._engine.get(f"/{environment_id}/scenarios")
        return ScenariosResponse(
            scenarios=[Scenario(**s) for s in response.get("scenarios", [])],
            count=response.get("count", 0)
        )

    def generate(self, environment_id: str) -> ScenariosResponse:
        """
        Generate scenarios using the AI scenario generator agent.

        Args:
            environment_id: The environment ID

        Returns:
            ScenariosResponse with list of generated scenarios
        """
        response = self._engine.post(f"/{environment_id}/scenarios/generate")
        return ScenariosResponse(
            scenarios=[Scenario(**s) for s in response.get("scenarios", [])],
            count=len(response.get("scenarios", []))
        )

    def delete(self, environment_id: str, scenario_id: str) -> DeleteResponse:
        """
        Delete a scenario from an environment.

        Args:
            environment_id: The environment ID
            scenario_id: The scenario ID to delete

        Returns:
            DeleteResponse with success message
        """
        response = self._engine.delete(f"/{environment_id}/scenarios/{scenario_id}")
        return DeleteResponse(**response)
