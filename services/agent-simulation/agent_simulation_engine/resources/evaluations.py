"""
Evaluations resource for the Agent Simulation Engine SDK.
"""

from typing import List, Optional, TYPE_CHECKING

from ..models import (
    Evaluation,
    EvaluationsResponse,
    EvaluationGenerateResponse,
)

if TYPE_CHECKING:
    from ..client import ASIMEngine


class Evaluations:
    """
    Manage evaluations for agent testing.

    Usage:
        # Create an evaluation run
        eval_run = client.evaluations.create(
            environment_id,
            evaluation_run_name="Round 1",
            metrics=["task_completion", "hallucinations"]
        )

        # List all evaluations
        evals = client.evaluations.list(environment_id)

        # Get a specific evaluation
        eval = client.evaluations.get(environment_id, evaluation_id)
    """

    def __init__(self, engine: "ASIMEngine"):
        self._engine = engine

    def create(
        self,
        environment_id: str,
        evaluation_run_name: str,
        simulation_ids: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
    ) -> EvaluationGenerateResponse:
        """
        Generate bulk evaluations for an agent on multiple simulations.

        This creates an evaluation job and queues tasks for each simulation.
        Use client.jobs.get_evaluation_status() to poll for completion.

        Args:
            environment_id: The environment ID
            evaluation_run_name: Name for this evaluation run
            simulation_ids: Optional list of simulation IDs (uses all if None)
            metrics: Optional list of metrics to evaluate
                     Default: ["task_completion", "hallucinations", "answer_relevancy"]

        Returns:
            EvaluationGenerateResponse with evaluation_run_id and job_id
        """
        data = {"evaluation_run_name": evaluation_run_name}
        if simulation_ids:
            data["simulation_ids"] = simulation_ids
        if metrics:
            data["metrics"] = metrics

        response = self._engine.post(
            f"/{environment_id}/evaluations/generate",
            json=data
        )
        return EvaluationGenerateResponse(**response)

    def list(
        self,
        environment_id: str,
        simulation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> EvaluationsResponse:
        """
        Get all evaluations for an environment.

        Args:
            environment_id: The environment ID
            simulation_id: Optional filter by simulation ID
            agent_id: Optional filter by agent ID

        Returns:
            EvaluationsResponse with list of evaluations and count
        """
        params = {}
        if simulation_id:
            params["simulation_id"] = simulation_id
        if agent_id:
            params["agent_id"] = agent_id

        response = self._engine.get(
            f"/{environment_id}/evaluations",
            params=params if params else None
        )
        return EvaluationsResponse(
            evaluations=[Evaluation(**e) for e in response.get("evaluations", [])],
            count=response.get("count", 0)
        )

    def get(self, environment_id: str, evaluation_id: str) -> Evaluation:
        """
        Get an evaluation result by ID.

        Args:
            environment_id: The environment ID
            evaluation_id: The evaluation ID

        Returns:
            Evaluation result
        """
        response = self._engine.get(f"/{environment_id}/evaluations/{evaluation_id}")
        return Evaluation(**response.get("evaluation", response))
