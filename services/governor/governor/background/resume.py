"""Auto-resume manager for approved executions."""

from __future__ import annotations

import asyncio
from typing import Callable, Coroutine, Any, Optional

from governor.approval.manager import ApprovalManager, get_default_approval_manager
from governor.background.queue import BackgroundJobQueue, get_default_queue
from governor.core.context import ExecutionStatus
from governor.events.base import Event, EventType
from governor.events.emitter import EventEmitter, get_default_emitter
from governor.replay.engine import ReplayEngine
from governor.storage.base import StorageBackend


class AutoResumeManager:
    """
    Automatically resumes executions when approval is granted.

    Listens for ApprovalGrantedEvent and resumes the execution
    from its saved state.
    """

    def __init__(
        self,
        storage: StorageBackend,
        job_queue: Optional[BackgroundJobQueue] = None,
        emitter: Optional[EventEmitter] = None,
        approval_manager: Optional[ApprovalManager] = None,
    ):
        """
        Initialize auto-resume manager.

        Args:
            storage: Storage backend with execution state
            job_queue: Background job queue (optional)
            emitter: Event emitter (defaults to global)
            approval_manager: Approval manager (defaults to global)
        """
        self.storage = storage
        self.job_queue = job_queue
        self.emitter = emitter or get_default_emitter()
        self.approval_manager = approval_manager or get_default_approval_manager()
        self.replay_engine = ReplayEngine(storage)
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Register functions for resume
        self._resume_functions: dict[str, Callable] = {}

    async def start(self) -> None:
        """Start monitoring for approval events."""
        if not self._running:
            self._running = True

            # Subscribe to approval events
            self.emitter.on(EventType.APPROVAL_GRANTED, self._handle_approval_granted)

            # Start monitoring task
            self._monitor_task = asyncio.create_task(self._monitor_approvals())

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False

        # Unsubscribe from events
        self.emitter.off(EventType.APPROVAL_GRANTED, self._handle_approval_granted)

        # Cancel monitor task
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    def register_function(self, function_name: str, func: Callable) -> None:
        """
        Register a function for auto-resume.

        Args:
            function_name: Name of the governed function
            func: The actual function to resume

        Example:
            ```python
            auto_resume = AutoResumeManager(storage)

            @govern(...)
            async def my_function(data):
                return result

            # Register for auto-resume
            auto_resume.register_function("my_function", my_function)
            await auto_resume.start()
            ```
        """
        self._resume_functions[function_name] = func

    async def _handle_approval_granted(self, event: Event) -> None:
        """Handle approval granted event."""
        execution_id = event.execution_id

        # Get execution context
        context = await self.storage.get_execution(execution_id)
        if not context:
            return

        # Check if we have the function registered
        func = self._resume_functions.get(context.function_name)
        if not func:
            print(
                f"⚠️  Function {context.function_name} not registered for auto-resume. "
                "Call auto_resume.register_function() to enable auto-resume."
            )
            return

        # Resume execution
        await self._resume_execution(execution_id, context.function_name, func)

    async def _resume_execution(
        self, execution_id: str, function_name: str, func: Callable
    ) -> None:
        """Resume an execution from saved state."""
        try:
            # Get last snapshot
            snapshot = await self.replay_engine.get_last_snapshot(execution_id)
            if not snapshot:
                print(f"❌ No snapshot found for execution {execution_id}")
                return

            # Restore state
            state = snapshot.restore_state()
            args = state.get("function_args", {}).get("args", ())
            kwargs = state.get("function_kwargs", {})

            print(f"▶️  Auto-resuming {function_name} (execution: {execution_id})")

            # Submit to job queue if available, otherwise execute directly
            if self.job_queue:
                job_id = await self.job_queue.submit_job(
                    execution_id=execution_id, func=func, args=args, kwargs=kwargs
                )
                print(f"   Submitted as background job: {job_id}")
            else:
                # Execute directly
                result = await func(*args, **kwargs)
                print(f"   ✓ Resumed execution completed: {result}")

        except Exception as e:
            print(f"❌ Failed to resume execution {execution_id}: {e}")

    async def _monitor_approvals(self) -> None:
        """Monitor for approved executions that need resuming."""
        while self._running:
            try:
                # Check for approved executions
                approved_executions = await self.storage.list_executions(
                    status=ExecutionStatus.APPROVED, limit=100
                )

                for context in approved_executions:
                    # Check if function is registered
                    func = self._resume_functions.get(context.function_name)
                    if func:
                        await self._resume_execution(
                            context.execution_id, context.function_name, func
                        )

            except Exception as e:
                print(f"Error in approval monitor: {e}")

            # Check every few seconds
            await asyncio.sleep(5)

    async def resume_by_execution_id(
        self, execution_id: str, func: Optional[Callable] = None
    ) -> Any:
        """
        Manually resume an execution by ID.

        Args:
            execution_id: Execution ID to resume
            func: Optional function (if not registered)

        Returns:
            Result of the execution

        Raises:
            ValueError: If execution not found or function not provided

        Example:
            ```python
            # Resume a specific execution
            result = await auto_resume.resume_by_execution_id(
                "exec-123",
                func=my_governed_function
            )
            ```
        """
        context = await self.storage.get_execution(execution_id)
        if not context:
            raise ValueError(f"Execution {execution_id} not found")

        # Get function
        resume_func = func or self._resume_functions.get(context.function_name)
        if not resume_func:
            raise ValueError(
                f"Function {context.function_name} not registered. "
                "Provide func parameter or call register_function()"
            )

        # Get snapshot
        snapshot = await self.replay_engine.get_last_snapshot(execution_id)
        if not snapshot:
            raise ValueError(f"No snapshot found for execution {execution_id}")

        # Restore and execute
        state = snapshot.restore_state()
        args = state.get("function_args", {}).get("args", ())
        kwargs = state.get("function_kwargs", {})

        return await resume_func(*args, **kwargs)
