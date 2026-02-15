"""
Simulations resource for the Agent Simulation Engine SDK.
"""

from typing import List, Optional, TYPE_CHECKING

from ..models import (
    Simulation,
    SimulationsResponse,
    SimulationGenerateResponse,
    DeleteResponse,
)

if TYPE_CHECKING:
    from ..client import ASIMEngine


class Simulations:
    """
    Manage simulations (test cases) for agent testing.

    Usage:
        # Add a simulation manually
        sim = client.simulations.create(
            environment_id,
            name="Pricing Query",
            user_input="How much does premium cost?",
            expected_output="Clear pricing information",
            ground_truth="Premium is $99/month"
        )

        # Generate simulations for all persona x scenario pairs
        job = client.simulations.generate(environment_id)
        # Returns job_id for polling status

        # List all simulations
        sims = client.simulations.list(environment_id)

        # Get a specific simulation
        sim = client.simulations.get(environment_id, simulation_id)

        # Update a simulation
        sim = client.simulations.update(
            environment_id,
            simulation_id,
            name="Updated Name",
            user_input="...",
            expected_output="..."
        )

        # Delete a simulation
        client.simulations.delete(environment_id, simulation_id)
    """

    def __init__(self, engine: "ASIMEngine"):
        self._engine = engine

    def create(
        self,
        environment_id: str,
        name: str,
        user_input: str,
        expected_output: str,
        ground_truth: Optional[str] = None,
        persona_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
    ) -> Simulation:
        """
        Add a single simulation to an environment.

        Args:
            environment_id: The environment ID
            name: Name of the simulation
            user_input: The user input/query to test
            expected_output: Expected behavior/output from the agent
            ground_truth: Optional factual ground truth for evaluation
            persona_id: Optional persona ID this simulation is based on
            scenario_id: Optional scenario ID this simulation is based on

        Returns:
            Created Simulation
        """
        data = {
            "name": name,
            "user_input": user_input,
            "expected_output": expected_output,
        }
        if ground_truth:
            data["ground_truth"] = ground_truth
        if persona_id:
            data["persona_id"] = persona_id
        if scenario_id:
            data["scenario_id"] = scenario_id

        response = self._engine.post(f"/{environment_id}/simulations", json=data)
        return Simulation(**response.get("simulation", response))

    def list(self, environment_id: str) -> SimulationsResponse:
        """
        Get all simulations for an environment.

        Args:
            environment_id: The environment ID

        Returns:
            SimulationsResponse with list of simulations and count
        """
        response = self._engine.get(f"/{environment_id}/simulations")
        return SimulationsResponse(
            simulations=[Simulation(**s) for s in response.get("simulations", [])],
            count=response.get("count", 0)
        )

    def get(self, environment_id: str, simulation_id: str) -> Simulation:
        """
        Get a single simulation by ID.

        Args:
            environment_id: The environment ID
            simulation_id: The simulation ID

        Returns:
            Simulation
        """
        response = self._engine.get(f"/{environment_id}/simulations/{simulation_id}")
        return Simulation(**response.get("simulation", response))

    def update(
        self,
        environment_id: str,
        simulation_id: str,
        name: str,
        user_input: str,
        expected_output: str,
        ground_truth: Optional[str] = None,
        persona_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
    ) -> Simulation:
        """
        Update a simulation by ID.

        Args:
            environment_id: The environment ID
            simulation_id: The simulation ID
            name: Updated name
            user_input: Updated user input
            expected_output: Updated expected output
            ground_truth: Optional updated ground truth
            persona_id: Optional updated persona ID
            scenario_id: Optional updated scenario ID

        Returns:
            Updated Simulation
        """
        data = {
            "name": name,
            "user_input": user_input,
            "expected_output": expected_output,
        }
        if ground_truth is not None:
            data["ground_truth"] = ground_truth
        if persona_id is not None:
            data["persona_id"] = persona_id
        if scenario_id is not None:
            data["scenario_id"] = scenario_id

        response = self._engine.put(
            f"/{environment_id}/simulations/{simulation_id}",
            json=data
        )
        return Simulation(**response.get("simulation", response))

    def delete(self, environment_id: str, simulation_id: str) -> DeleteResponse:
        """
        Delete a simulation by ID.

        Args:
            environment_id: The environment ID
            simulation_id: The simulation ID

        Returns:
            DeleteResponse with success message
        """
        response = self._engine.delete(f"/{environment_id}/simulations/{simulation_id}")
        return DeleteResponse(**response)

    def generate(
        self,
        environment_id: str,
        scenario_ids: Optional[List[str]] = None,
        persona_ids: Optional[List[str]] = None,
    ) -> SimulationGenerateResponse:
        """
        Generate simulations for scenario x persona pairs.

        This triggers async Celery tasks. Use client.jobs.get_status()
        to poll for completion.

        Args:
            environment_id: The environment ID
            scenario_ids: Optional list of scenario IDs (uses all if None)
            persona_ids: Optional list of persona IDs (uses all if None)

        Returns:
            SimulationGenerateResponse with job_id for tracking
        """
        data = {}
        if scenario_ids:
            data["scenario_ids"] = scenario_ids
        if persona_ids:
            data["persona_ids"] = persona_ids

        response = self._engine.post(
            f"/{environment_id}/simulations/generate",
            json=data if data else None
        )
        return SimulationGenerateResponse(**response)
