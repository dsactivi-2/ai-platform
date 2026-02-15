"""
Dashboard resource for the Agent Simulation Engine SDK.
"""

from typing import TYPE_CHECKING

from ..models import (
    DashboardStats,
    RecentEnvironment,
    RecentEnvironmentsResponse,
    RecentEvaluation,
    RecentEvaluationsResponse,
    RecentJob,
    RecentJobsResponse,
    JobProgress,
    ActiveEvaluationRun,
    ActiveEvaluationRunsResponse,
)

if TYPE_CHECKING:
    from ..client import ASIMEngine


class Dashboard:
    """
    Dashboard operations for overview statistics.

    Usage:
        # Get overall statistics
        stats = client.dashboard.get_stats()
        print(f"Total environments: {stats.total_environments}")
        print(f"Pass rate: {stats.average_pass_rate}%")

        # Get recent environments
        envs = client.dashboard.recent_environments(limit=5)

        # Get recent evaluations
        evals = client.dashboard.recent_evaluations(limit=20)

        # Get recent jobs
        jobs = client.dashboard.recent_jobs(limit=10)

        # Get active evaluation runs
        runs = client.dashboard.active_evaluation_runs(limit=10)
    """

    def __init__(self, engine: "ASIMEngine"):
        self._engine = engine

    def get_stats(self) -> DashboardStats:
        """
        Get overall dashboard statistics.

        Returns:
            DashboardStats with totals and average pass rate
        """
        response = self._engine.get("/dashboard/stats")
        return DashboardStats(**response)

    def recent_environments(self, limit: int = 5) -> RecentEnvironmentsResponse:
        """
        Get recent environments with summary data.

        Args:
            limit: Number of environments to return (1-20, default 5)

        Returns:
            RecentEnvironmentsResponse with list of recent environments
        """
        response = self._engine.get("/dashboard/recent-environments", params={"limit": limit})
        return RecentEnvironmentsResponse(
            environments=[
                RecentEnvironment(**env)
                for env in response.get("environments", [])
            ]
        )

    def recent_evaluations(self, limit: int = 20) -> RecentEvaluationsResponse:
        """
        Get recent evaluation results across all environments.

        Args:
            limit: Number of evaluations to return (1-100, default 20)

        Returns:
            RecentEvaluationsResponse with list of recent evaluations
        """
        response = self._engine.get("/dashboard/recent-evaluations", params={"limit": limit})
        return RecentEvaluationsResponse(
            evaluations=[
                RecentEvaluation(**e)
                for e in response.get("evaluations", [])
            ],
            count=response.get("count", 0)
        )

    def recent_jobs(self, limit: int = 10) -> RecentJobsResponse:
        """
        Get recent simulation and evaluation jobs with progress.

        Args:
            limit: Number of jobs to return (1-50, default 10)

        Returns:
            RecentJobsResponse with list of recent jobs
        """
        response = self._engine.get("/dashboard/recent-jobs", params={"limit": limit})
        jobs = []
        for job in response.get("jobs", []):
            progress_data = job.get("progress", {})
            jobs.append(RecentJob(
                id=job["id"],
                job_type=job["job_type"],
                environment_id=job["environment_id"],
                environment_name=job.get("environment_name"),
                progress=JobProgress(**progress_data) if isinstance(progress_data, dict) else JobProgress(completed=0, total=0, percentage=0),
                status=job["status"],
                started_at=job.get("started_at"),
                completed_at=job.get("completed_at"),
            ))
        return RecentJobsResponse(jobs=jobs)

    def active_evaluation_runs(self, limit: int = 10) -> ActiveEvaluationRunsResponse:
        """
        Get active and recent evaluation runs with progress.

        Args:
            limit: Number of evaluation runs to return (1-50, default 10)

        Returns:
            ActiveEvaluationRunsResponse with list of evaluation runs
        """
        response = self._engine.get("/dashboard/active-evaluation-runs", params={"limit": limit})
        runs = []
        for run in response.get("evaluation_runs", []):
            progress_data = run.get("progress", {})
            runs.append(ActiveEvaluationRun(
                id=run["id"],
                evaluation_run_name=run.get("evaluation_run_name"),
                environment_id=run["environment_id"],
                environment_name=run.get("environment_name"),
                current_round=run.get("current_round", 1),
                total_rounds=run.get("total_rounds", 1),
                progress=JobProgress(**progress_data) if isinstance(progress_data, dict) else JobProgress(completed=0, total=0, percentage=0),
                pass_count=run.get("pass_count", 0),
                fail_count=run.get("fail_count", 0),
                status=run.get("status", "pending"),
                started_at=run.get("started_at"),
                updated_at=run.get("updated_at"),
            ))
        return ActiveEvaluationRunsResponse(evaluation_runs=runs)
