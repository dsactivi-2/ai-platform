"""
Hardening resource for the Agent Simulation Engine SDK.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..models import (
    HardeningResponse,
    AgentConfig,
    ContinueRunResponse,
)

if TYPE_CHECKING:
    from ..client import ASIMEngine


class Hardening:
    """
    Agent hardening operations for the reinforcement learning loop.

    The hardening workflow:
    1. Run evaluations and identify failures
    2. Call harden_agent() to analyze failures and generate improved config
    3. Call continue_run() to start a new round with the improved agent
    4. Repeat until all evaluations pass

    Usage:
        # First, complete an evaluation round
        # Then harden the agent based on failures
        hardening = client.hardening.harden_agent(
            environment_id=env_id,
            run_id=run.evaluation_run_id,
            round_number=1
        )

        print("Original:", hardening.original_config.agent_instructions)
        print("Improved:", hardening.improved_config.agent_instructions)

        # Continue with the improved config
        new_round = client.hardening.continue_run(
            environment_id=env_id,
            run_id=run.evaluation_run_id,
            round_number=1,
            agent_config=hardening.improved_config.model_dump()
        )

        # Poll the new job until complete
        # Repeat the hardening loop
    """

    def __init__(self, engine: "ASIMEngine"):
        self._engine = engine

    def harden_agent(
        self,
        environment_id: str,
        run_id: str,
        round_number: int,
        evaluation_ids: Optional[List[str]] = None,
    ) -> HardeningResponse:
        """
        Call agent hardening to improve agent configuration based on evaluations.

        If evaluation_ids is provided, analyzes those specific evaluations.
        Otherwise, analyzes all failed evaluations from the specified round.

        Args:
            environment_id: The environment ID
            run_id: The evaluation run ID
            round_number: The round number to analyze
            evaluation_ids: Optional specific evaluation IDs to analyze

        Returns:
            HardeningResponse with original and improved agent configs
        """
        data = {"round_number": round_number}
        if evaluation_ids:
            data["evaluation_ids"] = evaluation_ids

        response = self._engine.post(
            f"/{environment_id}/evaluation-runs/{run_id}/agent-hardening",
            json=data
        )
        return HardeningResponse(
            message=response["message"],
            original_config=AgentConfig(**response["original_config"]),
            improved_config=AgentConfig(**response["improved_config"]),
        )

    def continue_run(
        self,
        environment_id: str,
        run_id: str,
        round_number: int,
        agent_config: Dict[str, Any],
        simulation_ids: Optional[List[str]] = None,
    ) -> ContinueRunResponse:
        """
        Continue evaluation run with a new round using improved agent config.

        Args:
            environment_id: The environment ID
            run_id: The evaluation run ID
            round_number: The current round number (new round will be round_number + 1)
            agent_config: The improved agent configuration from hardening
            simulation_ids: Optional list of simulation IDs (uses all from previous round if None)

        Returns:
            ContinueRunResponse with new round number and job_id for tracking
        """
        data = {
            "round_number": round_number,
            "agent_config": agent_config,
        }
        if simulation_ids:
            data["simulation_ids"] = simulation_ids

        response = self._engine.post(
            f"/{environment_id}/evaluation-runs/{run_id}/continue",
            json=data
        )
        return ContinueRunResponse(**response)
