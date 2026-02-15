"""
Evaluation Runs resource for the Agent Simulation Engine SDK.
"""

from typing import TYPE_CHECKING

from ..models import (
    EvaluationRun,
    EvaluationRound,
    EvaluationRunSummary,
    EvaluationRunsResponse,
    EvaluationRoundResponse,
    RoundStatistics,
    RoundMetadata,
    SyncRoundResponse,
)

if TYPE_CHECKING:
    from ..client import ASIMEngine


class EvaluationRuns:
    """
    Manage evaluation runs for the reinforcement hardening loop.

    An evaluation run consists of multiple rounds, where each round:
    1. Runs the agent against all simulations
    2. Evaluates the results
    3. (Optionally) Hardens the agent based on failures
    4. Continues with the improved agent in the next round

    Usage:
        # Get an evaluation run
        run = client.evaluation_runs.get(environment_id, run_id)

        # List all evaluation runs
        runs = client.evaluation_runs.list(environment_id)

        # Get a specific round
        round = client.evaluation_runs.get_round(environment_id, run_id, round_number=1)

        # Sync results into a round
        client.evaluation_runs.sync_round(environment_id, run_id, round_number=1)
    """

    def __init__(self, engine: "ASIMEngine"):
        self._engine = engine

    def get(self, environment_id: str, run_id: str) -> EvaluationRun:
        """
        Get the status of an evaluation run with all rounds.

        Args:
            environment_id: The environment ID
            run_id: The evaluation run ID

        Returns:
            EvaluationRun with all rounds and simulation results
        """
        response = self._engine.get(f"/{environment_id}/evaluation-runs/{run_id}")
        run_data = response.get("evaluation_run", response)
        return EvaluationRun(
            id=run_data.get("id", run_data.get("_id", "")),
            environment_id=run_data["environment_id"],
            evaluation_run_name=run_data.get("evaluation_run_name"),
            agent_id=run_data.get("agent_id"),
            agent_name=run_data.get("agent_name"),
            metrics=run_data.get("metrics"),
            simulation_ids=run_data.get("simulation_ids"),
            current_round=run_data.get("current_round", 1),
            status=run_data.get("status"),
            rounds=[EvaluationRound(**r) for r in run_data.get("rounds", [])],
            created_at=run_data.get("created_at"),
            updated_at=run_data.get("updated_at"),
        )

    def list(self, environment_id: str) -> EvaluationRunsResponse:
        """
        Get all evaluation runs for an environment.

        Args:
            environment_id: The environment ID

        Returns:
            EvaluationRunsResponse with list of evaluation run summaries
        """
        response = self._engine.get(f"/{environment_id}/evaluation-runs")
        return EvaluationRunsResponse(
            evaluation_runs=[
                EvaluationRunSummary(**run)
                for run in response.get("evaluation_runs", [])
            ],
            count=response.get("count", 0)
        )

    def get_round(
        self,
        environment_id: str,
        run_id: str,
        round_number: int,
    ) -> EvaluationRoundResponse:
        """
        Get a specific round from an evaluation run.

        Args:
            environment_id: The environment ID
            run_id: The evaluation run ID
            round_number: The round number (1-indexed)

        Returns:
            EvaluationRoundResponse with round details, statistics, and metadata
        """
        response = self._engine.get(
            f"/{environment_id}/evaluation-runs/{run_id}/rounds/{round_number}"
        )
        return EvaluationRoundResponse(
            round=EvaluationRound(**response["round"]),
            statistics=RoundStatistics(**response["statistics"]),
            metadata=RoundMetadata(**response["metadata"]),
        )

    def sync_round(
        self,
        environment_id: str,
        run_id: str,
        round_number: int,
    ) -> SyncRoundResponse:
        """
        Sync evaluation results from the job into the round's simulation_results.

        Call this after the evaluation job completes to populate the round
        with the actual evaluation results.

        Args:
            environment_id: The environment ID
            run_id: The evaluation run ID
            round_number: The round number to sync

        Returns:
            SyncRoundResponse with updated round and results count
        """
        response = self._engine.post(
            f"/{environment_id}/evaluation-runs/{run_id}/rounds/{round_number}/sync"
        )
        return SyncRoundResponse(
            message=response["message"],
            round=EvaluationRound(**response["round"]),
            results_count=response["results_count"],
        )
