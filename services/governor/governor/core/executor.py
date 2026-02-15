"""Core execution engine for governed functions."""

from __future__ import annotations

import inspect
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional

from governor.approval.handlers import ApprovalHandler
from governor.approval.manager import ApprovalManager, get_default_approval_manager
from governor.core.context import ExecutionContext, ExecutionStatus
from governor.core.state import StateSnapshot
from governor.events.base import (
    ApprovalGrantedEvent,
    ApprovalRejectedEvent,
    ApprovalRequestedEvent,
    Event,
    EventType,
    ExecutionCompletedEvent,
    ExecutionFailedEvent,
    ExecutionStartedEvent,
    PolicyViolatedEvent,
)
from governor.events.emitter import EventEmitter, get_default_emitter
from governor.policies.base import Policy, PolicyPhase
from governor.storage.base import StorageBackend
from governor.storage.memory import InMemoryStorage


Action = Callable[[ExecutionContext], Coroutine[Any, Any, None]]


class Executor:
    """
    Core executor for governed functions.

    Orchestrates the complete governance lifecycle:
    1. Pre-actions
    2. Policy evaluation (pre-execution)
    3. Approval (if required)
    4. Main function execution
    5. Policy evaluation (post-execution)
    6. Post-actions
    """

    def __init__(
        self,
        storage: Optional[StorageBackend] = None,
        emitter: Optional[EventEmitter] = None,
        approval_manager: Optional[ApprovalManager] = None,
        approval_handler: Optional[ApprovalHandler] = None,
        on_state_saved: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        """
        Initialize executor.

        Args:
            storage: Storage backend (defaults to InMemoryStorage)
            emitter: Event emitter (defaults to global emitter)
            approval_manager: Approval manager (defaults to global manager)
            approval_handler: Handler for approval requests
            on_state_saved: Callback when state is saved (execution_id, state)
        """
        self.storage = storage or InMemoryStorage()
        self.emitter = emitter or get_default_emitter()
        self.approval_manager = approval_manager or get_default_approval_manager()
        self.approval_handler = approval_handler
        self.on_state_saved = on_state_saved

    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        args: tuple[Any, ...],
        kwargs: Dict[str, Any],
        pre_actions: Optional[List[Action]] = None,
        post_actions: Optional[List[Action]] = None,
        policies: Optional[List[Policy]] = None,
        capture_state: bool = True,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a governed function.

        Args:
            func: The async function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            pre_actions: Actions to run before execution
            post_actions: Actions to run after execution
            policies: Policies to evaluate
            capture_state: Whether to capture state snapshots
            context_data: Additional context data

        Returns:
            The function's return value

        Raises:
            Exception: If execution fails or policies block
        """
        # Create execution context
        context = ExecutionContext(
            function_name=func.__name__,
            function_module=func.__module__,
            function_qualname=func.__qualname__,
            inputs={"args": args, "kwargs": kwargs},
            metadata=context_data or {},
        )

        # Store initial context
        await self.storage.store_execution(context)

        # Emit execution started event
        await self.emitter.emit(
            ExecutionStartedEvent(
                execution_id=context.execution_id,
                function_name=context.function_name,
                inputs=context.inputs,
            )
        )

        try:
            # 1. Run pre-actions
            if pre_actions:
                context.add_checkpoint("pre_actions")
                for action in pre_actions:
                    await action(context)

            # 2. Evaluate pre-execution policies
            if policies:
                context.add_checkpoint("pre_policies")
                await self._evaluate_policies(
                    context, policies, PolicyPhase.PRE_EXECUTION
                )

            # 3. Check if approval is required
            if context.approval_required:
                await self._handle_approval(context)

            # 4. Capture pre-execution state
            if capture_state:
                snapshot = StateSnapshot.capture(
                    execution_id=context.execution_id,
                    checkpoint="pre_execution",
                    snapshot_id=str(uuid.uuid4()),
                    function_args={"args": args},
                    function_kwargs=kwargs,
                )
                context.add_snapshot(snapshot.to_dict())
                await self.storage.store_snapshot(snapshot)

                # Call on_state_saved callback if provided
                if self.on_state_saved:
                    self.on_state_saved(
                        context.execution_id,
                        {
                            "execution_id": context.execution_id,
                            "function_name": context.function_name,
                            "status": context.status,
                            "checkpoint": "pre_execution",
                            "snapshot_id": snapshot.snapshot_id,
                            "inputs": context.inputs,
                            "captured_at": snapshot.captured_at.isoformat(),
                            "approval_required": context.approval_required,
                        }
                    )

            # 5. Execute main function
            context.mark_running()
            context.add_checkpoint("execution")
            await self.storage.store_execution(context)

            result = await func(*args, **kwargs)

            # 6. Capture post-execution state
            if capture_state:
                snapshot = StateSnapshot.capture(
                    execution_id=context.execution_id,
                    checkpoint="post_execution",
                    snapshot_id=str(uuid.uuid4()),
                    function_args={"args": args},
                    function_kwargs=kwargs,
                    intermediate_results=result,
                )
                context.add_snapshot(snapshot.to_dict())
                await self.storage.store_snapshot(snapshot)

            # 7. Evaluate post-execution policies
            if policies:
                context.add_checkpoint("post_policies")
                await self._evaluate_policies(
                    context, policies, PolicyPhase.POST_EXECUTION, outputs=result
                )

            # 8. Run post-actions
            if post_actions:
                context.add_checkpoint("post_actions")
                for action in post_actions:
                    await action(context)

            # 9. Mark completed
            context.mark_completed(result)
            await self.storage.store_execution(context)

            # Emit completion event
            await self.emitter.emit(
                ExecutionCompletedEvent(
                    execution_id=context.execution_id,
                    function_name=context.function_name,
                    outputs=result,
                    duration_ms=context.duration_ms or 0,
                )
            )

            return result

        except Exception as e:
            # Mark failed
            context.mark_failed(e)
            await self.storage.store_execution(context)

            # Emit failure event
            await self.emitter.emit(
                ExecutionFailedEvent(
                    execution_id=context.execution_id,
                    function_name=context.function_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
            )

            raise

    async def _evaluate_policies(
        self,
        context: ExecutionContext,
        policies: List[Policy],
        phase: PolicyPhase,
        outputs: Optional[Any] = None,
    ) -> None:
        """Evaluate policies for a specific phase."""
        for policy in policies:
            # Skip if policy doesn't match this phase
            if policy.phase not in (phase, PolicyPhase.BOTH):
                continue

            result = await policy.evaluate(
                execution_id=context.execution_id,
                function_name=context.function_name,
                inputs=context.inputs,
                outputs=outputs,
                context=context.metadata,
            )

            # Emit policy event
            await self.emitter.emit(
                Event.create(
                    event_type=EventType.POLICY_EVALUATED,
                    execution_id=context.execution_id,
                    function_name=context.function_name,
                    data=result.model_dump(),
                )
            )

            # Handle approval requirement
            if result.should_approve:
                context.approval_required = True

            # Handle blocking failures (but not if approval is required - let approval handler deal with it)
            if result.should_block and not result.passed and not result.should_approve:
                # Emit policy violated event
                await self.emitter.emit(
                    PolicyViolatedEvent(
                        execution_id=context.execution_id,
                        function_name=context.function_name,
                        policy_name=result.policy_name,
                        violation_reason=result.message or "Policy check failed",
                    )
                )

                raise PermissionError(
                    f"Policy '{result.policy_name}' blocked execution: {result.message}"
                )

    async def _handle_approval(self, context: ExecutionContext) -> None:
        """Handle approval requirement."""
        context.mark_awaiting_approval()
        await self.storage.store_execution(context)

        # Get approvers from context or use default
        approvers = context.metadata.get("approvers", ["admin"])
        timeout_seconds = context.metadata.get("approval_timeout", 3600)

        # Emit approval requested event
        await self.emitter.emit(
            ApprovalRequestedEvent(
                execution_id=context.execution_id,
                function_name=context.function_name,
                approvers=approvers,
                timeout_seconds=timeout_seconds,
            )
        )

        # Trigger approval handler if configured
        if self.approval_handler:
            await self.approval_handler.handle_approval_request(
                execution_id=context.execution_id,
                function_name=context.function_name,
                inputs=context.inputs,
                approvers=approvers,
            )

        # Wait for approval decision
        try:
            decision = await self.approval_manager.request_approval(
                execution_id=context.execution_id,
                function_name=context.function_name,
                inputs=context.inputs,
                approvers=approvers,
                timeout_seconds=timeout_seconds,
            )

            # Store approval decision
            await self.storage.store_approval(
                execution_id=context.execution_id,
                approver=decision.approver,
                approved=decision.approved,
                reason=decision.reason,
            )

            if decision.approved:
                context.mark_approved(decision.approver, decision.reason)
                await self.storage.store_execution(context)

                # Emit approval granted event
                await self.emitter.emit(
                    ApprovalGrantedEvent(
                        execution_id=context.execution_id,
                        function_name=context.function_name,
                        approver=decision.approver,
                        reason=decision.reason,
                    )
                )
            else:
                context.mark_rejected(decision.approver, decision.reason)
                await self.storage.store_execution(context)

                # Emit approval rejected event
                await self.emitter.emit(
                    ApprovalRejectedEvent(
                        execution_id=context.execution_id,
                        function_name=context.function_name,
                        approver=decision.approver,
                        reason=decision.reason,
                    )
                )

                raise PermissionError(
                    f"Execution rejected by {decision.approver}: {decision.reason or 'No reason provided'}"
                )

        except TimeoutError:
            # Handle timeout based on policy
            on_timeout = context.metadata.get("approval_on_timeout", "reject")

            if on_timeout == "approve":
                context.mark_approved("system", "Auto-approved on timeout")
                await self.storage.store_execution(context)
            else:
                context.mark_rejected("system", "Approval timeout")
                await self.storage.store_execution(context)

                # Call on_state_saved callback for async pattern (CRITICAL for 202 Accepted)
                if self.on_state_saved:
                    # Get the last snapshot
                    snapshots = context.state_snapshots
                    last_snapshot = snapshots[-1] if snapshots else {}

                    self.on_state_saved(
                        context.execution_id,
                        {
                            "execution_id": context.execution_id,
                            "function_name": context.function_name,
                            "status": context.status,
                            "checkpoint": context.current_checkpoint or "pre_execution",
                            "snapshot_id": last_snapshot.get("snapshot_id"),
                            "inputs": context.inputs,
                            "captured_at": last_snapshot.get("captured_at"),
                            "approval_required": context.approval_required,
                            "timeout": True,  # Flag indicating this is from timeout
                        }
                    )

                raise PermissionError("Approval request timed out")
