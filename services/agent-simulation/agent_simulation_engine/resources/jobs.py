"""
Jobs resource for the Agent Simulation Engine SDK.
"""

from typing import List, TYPE_CHECKING

from ..models import (
    JobStatus,
    JobSummary,
    TaskInfo,
    CancelJobResponse,
)

if TYPE_CHECKING:
    from ..client import ASIMEngine


class Jobs:
    """
    Monitor and manage simulation generation jobs.

    Usage:
        # Get job status
        status = client.jobs.get_status(environment_id, job_id)
        print(f"Progress: {status.progress}")
        print(f"Completed: {status.summary.completed}/{status.summary.total}")

        # Poll until complete
        while True:
            status = client.jobs.get_status(environment_id, job_id)
            if status.summary.completed + status.summary.failed == status.summary.total:
                break
            time.sleep(2)

        # List all jobs
        jobs = client.jobs.list(environment_id)

        # Cancel a job
        client.jobs.cancel(environment_id, job_id)
    """

    def __init__(self, engine: "ASIMEngine"):
        self._engine = engine

    def get_status(self, environment_id: str, job_id: str) -> JobStatus:
        """
        Get the status of a simulation generation job.

        Args:
            environment_id: The environment ID
            job_id: The job ID

        Returns:
            JobStatus with progress, summary, and task details
        """
        response = self._engine.get(f"/{environment_id}/jobs/{job_id}")
        return JobStatus(
            job_id=response["job_id"],
            environment_id=response["environment_id"],
            progress=response["progress"],
            summary=JobSummary(**response["summary"]),
            tasks=[TaskInfo(**t) for t in response.get("tasks", [])],
            created_at=response.get("created_at"),
        )

    def list(self, environment_id: str) -> List[JobStatus]:
        """
        Get all simulation generation jobs for an environment.

        Args:
            environment_id: The environment ID

        Returns:
            List of JobStatus objects
        """
        response = self._engine.get(f"/{environment_id}/jobs")
        jobs = []
        for job in response.get("jobs", []):
            jobs.append(JobStatus(
                job_id=job["job_id"],
                environment_id=job["environment_id"],
                progress=job["progress"],
                summary=JobSummary(**job["summary"]),
                tasks=[],  # List endpoint doesn't include full task details
                created_at=job.get("created_at"),
            ))
        return jobs

    def cancel(self, environment_id: str, job_id: str) -> CancelJobResponse:
        """
        Cancel a running simulation generation job.

        This will revoke pending Celery tasks and mark the job as cancelled.
        Note: Only works for simulation jobs, not evaluation jobs.

        Args:
            environment_id: The environment ID
            job_id: The job ID

        Returns:
            CancelJobResponse with cancellation summary
        """
        response = self._engine.post(f"/{environment_id}/jobs/{job_id}/cancel")
        return CancelJobResponse(**response)

    def get_evaluation_status(self, environment_id: str, job_id: str) -> JobStatus:
        """
        Get the status of an evaluation job.

        Args:
            environment_id: The environment ID
            job_id: The evaluation job ID

        Returns:
            JobStatus with progress, summary, and task details
        """
        response = self._engine.get(f"/{environment_id}/evaluation-jobs/{job_id}")
        return JobStatus(
            job_id=response["job_id"],
            environment_id=response["environment_id"],
            progress=response["progress"],
            summary=JobSummary(**response["summary"]),
            tasks=[TaskInfo(**t) for t in response.get("tasks", [])],
            created_at=response.get("created_at"),
            job_type=response.get("job_type", "evaluation"),
        )

    def list_evaluation_jobs(self, environment_id: str) -> List[JobStatus]:
        """
        Get all evaluation jobs for an environment.

        Args:
            environment_id: The environment ID

        Returns:
            List of JobStatus objects for evaluation jobs
        """
        response = self._engine.get(f"/{environment_id}/evaluation-jobs")
        jobs = []
        for job in response.get("jobs", []):
            jobs.append(JobStatus(
                job_id=job["job_id"],
                environment_id=job["environment_id"],
                progress=job["progress"],
                summary=JobSummary(**job["summary"]),
                tasks=[],
                created_at=job.get("created_at"),
                job_type="evaluation",
            ))
        return jobs
