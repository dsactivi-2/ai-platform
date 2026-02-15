"""Background job queue for long-running governance operations."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Optional

from pydantic import BaseModel


class JobStatus(str, Enum):
    """Status of a background job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobResult(BaseModel):
    """Result of a background job."""

    job_id: str
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class BackgroundJob:
    """Represents a background job."""

    job_id: str
    execution_id: str
    func: Callable[..., Coroutine[Any, Any, Any]]
    args: tuple
    kwargs: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BackgroundJobQueue:
    """
    Background job queue for long-running governance operations.

    Handles:
    - Immediate return with job ID
    - State persistence
    - Asynchronous execution
    - Resume on approval
    - Result retrieval

    For production, integrate with Celery, RQ, or other job queues.
    """

    def __init__(self):
        """Initialize the job queue."""
        self._jobs: Dict[str, BackgroundJob] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the background worker."""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        """Stop the background worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def submit_job(
        self,
        execution_id: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        args: tuple,
        kwargs: Dict[str, Any],
    ) -> str:
        """
        Submit a job for background execution.

        Args:
            execution_id: Execution ID for tracking
            func: Async function to execute
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Job ID for tracking

        Example:
            ```python
            queue = BackgroundJobQueue()
            await queue.start()

            # Submit job - returns immediately
            job_id = await queue.submit_job(
                execution_id="exec-123",
                func=my_async_function,
                args=(arg1, arg2),
                kwargs={"key": "value"}
            )

            # Check status later
            result = await queue.get_job_result(job_id)
            ```
        """
        job_id = str(uuid.uuid4())

        job = BackgroundJob(
            job_id=job_id,
            execution_id=execution_id,
            func=func,
            args=args,
            kwargs=kwargs,
        )

        self._jobs[job_id] = job
        return job_id

    async def get_job_result(self, job_id: str) -> Optional[JobResult]:
        """
        Get result of a background job.

        Args:
            job_id: Job ID

        Returns:
            JobResult if found, None otherwise
        """
        job = self._jobs.get(job_id)
        if not job:
            return None

        return JobResult(
            job_id=job.job_id,
            status=job.status,
            result=job.result,
            error=job.error,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    async def wait_for_job(self, job_id: str, timeout: Optional[float] = None) -> JobResult:
        """
        Wait for a job to complete.

        Args:
            job_id: Job ID
            timeout: Optional timeout in seconds

        Returns:
            JobResult when complete

        Raises:
            TimeoutError: If timeout expires
            ValueError: If job not found
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            result = await self.get_job_result(job_id)

            if not result:
                raise ValueError(f"Job {job_id} not found")

            if result.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                return result

            if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

            await asyncio.sleep(0.1)  # Poll interval

    async def _worker(self) -> None:
        """Background worker that processes jobs."""
        while self._running:
            # Find pending jobs
            pending_jobs = [job for job in self._jobs.values() if job.status == JobStatus.PENDING]

            for job in pending_jobs:
                # Execute job
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(timezone.utc)

                try:
                    result = await job.func(*job.args, **job.kwargs)
                    job.result = result
                    job.status = JobStatus.COMPLETED
                except Exception as e:
                    job.error = str(e)
                    job.status = JobStatus.FAILED
                finally:
                    job.completed_at = datetime.now(timezone.utc)

            # Small delay to avoid busy loop
            await asyncio.sleep(0.1)

    def list_jobs(
        self, status: Optional[JobStatus] = None, execution_id: Optional[str] = None
    ) -> list[JobResult]:
        """
        List all jobs with optional filtering.

        Args:
            status: Filter by status
            execution_id: Filter by execution ID

        Returns:
            List of JobResult instances
        """
        jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        if execution_id:
            jobs = [j for j in jobs if j.execution_id == execution_id]

        return [
            JobResult(
                job_id=job.job_id,
                status=job.status,
                result=job.result,
                error=job.error,
                started_at=job.started_at,
                completed_at=job.completed_at,
            )
            for job in jobs
        ]


# Global job queue instance
_default_queue: Optional[BackgroundJobQueue] = None


async def get_default_queue() -> BackgroundJobQueue:
    """Get or create the default global job queue."""
    global _default_queue
    if _default_queue is None:
        _default_queue = BackgroundJobQueue()
        await _default_queue.start()
    return _default_queue
