"""Replay engine for state continuation and recovery."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

from governor.core.context import ExecutionContext, ExecutionStatus
from governor.core.state import StateSnapshot
from governor.storage.base import StorageBackend
from governor.storage.memory import InMemoryStorage


class ReplayStrategy(str, Enum):
    """Strategy for replaying execution."""

    FULL = "full"  # Replay entire execution from start
    FROM_CHECKPOINT = "from_checkpoint"  # Resume from specific checkpoint
    FROM_LAST = "from_last"  # Resume from last snapshot
    DEBUG = "debug"  # Replay for debugging (with callbacks)


class ReplayEngine:
    """
    Engine for replaying and continuing executions from saved state.

    Supports multiple replay strategies for recovery, debugging, and testing.
    """

    def __init__(self, storage: Optional[StorageBackend] = None):
        """
        Initialize replay engine.

        Args:
            storage: Storage backend (defaults to InMemoryStorage)
        """
        self.storage = storage or InMemoryStorage()

    async def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """
        Get an execution context by ID.

        Args:
            execution_id: Execution ID

        Returns:
            ExecutionContext if found
        """
        return await self.storage.get_execution(execution_id)

    async def get_snapshots(self, execution_id: str) -> List[StateSnapshot]:
        """
        Get all snapshots for an execution.

        Args:
            execution_id: Execution ID

        Returns:
            List of StateSnapshot instances
        """
        return await self.storage.get_snapshots_by_execution(execution_id)

    async def get_snapshot_at_checkpoint(
        self, execution_id: str, checkpoint: str
    ) -> Optional[StateSnapshot]:
        """
        Get snapshot at a specific checkpoint.

        Args:
            execution_id: Execution ID
            checkpoint: Checkpoint name

        Returns:
            StateSnapshot if found
        """
        snapshots = await self.get_snapshots(execution_id)
        for snapshot in snapshots:
            if snapshot.checkpoint == checkpoint:
                return snapshot
        return None

    async def get_last_snapshot(self, execution_id: str) -> Optional[StateSnapshot]:
        """
        Get the most recent snapshot for an execution.

        Args:
            execution_id: Execution ID

        Returns:
            StateSnapshot if found
        """
        snapshots = await self.get_snapshots(execution_id)
        if snapshots:
            return snapshots[-1]  # Last snapshot
        return None

    async def continue_from_checkpoint(
        self,
        execution_id: str,
        checkpoint: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Any:
        """
        Continue execution from a specific checkpoint.

        Args:
            execution_id: Execution ID
            checkpoint: Checkpoint name to resume from
            func: The governed function to execute

        Returns:
            Function result

        Raises:
            ValueError: If checkpoint not found
        """
        # Get snapshot at checkpoint
        snapshot = await self.get_snapshot_at_checkpoint(execution_id, checkpoint)
        if not snapshot:
            raise ValueError(
                f"No snapshot found for execution {execution_id} at checkpoint '{checkpoint}'"
            )

        # Restore state
        state = snapshot.restore_state()

        # Re-execute function with restored state
        args = state.get("function_args", {}).get("args", ())
        kwargs = state.get("function_kwargs", {})

        return await func(*args, **kwargs)

    async def continue_from_last(
        self, execution_id: str, func: Callable[..., Coroutine[Any, Any, Any]]
    ) -> Any:
        """
        Continue execution from the last snapshot.

        Args:
            execution_id: Execution ID
            func: The governed function to execute

        Returns:
            Function result

        Raises:
            ValueError: If no snapshots found
        """
        snapshot = await self.get_last_snapshot(execution_id)
        if not snapshot:
            raise ValueError(f"No snapshots found for execution {execution_id}")

        # Restore state
        state = snapshot.restore_state()

        # Re-execute function
        args = state.get("function_args", {}).get("args", ())
        kwargs = state.get("function_kwargs", {})

        return await func(*args, **kwargs)

    async def replay_for_debugging(
        self,
        execution_id: str,
        on_checkpoint: Optional[Callable[[str, StateSnapshot], Coroutine[Any, Any, None]]] = None,
    ) -> Dict[str, Any]:
        """
        Replay an execution for debugging purposes.

        Walks through all checkpoints and snapshots, calling callback
        at each point for inspection.

        Args:
            execution_id: Execution ID
            on_checkpoint: Optional callback called at each checkpoint

        Returns:
            Dictionary with replay information
        """
        context = await self.get_execution(execution_id)
        if not context:
            raise ValueError(f"Execution {execution_id} not found")

        snapshots = await self.get_snapshots(execution_id)

        replay_info = {
            "execution_id": execution_id,
            "function_name": context.function_name,
            "status": context.status,
            "checkpoints": context.checkpoint_history,
            "snapshot_count": len(snapshots),
            "snapshots": [],
        }

        # Walk through snapshots
        for snapshot in snapshots:
            snapshot_info = {
                "checkpoint": snapshot.checkpoint,
                "captured_at": snapshot.captured_at.isoformat(),
                "has_state": snapshot.serialized_state is not None,
            }
            replay_info["snapshots"].append(snapshot_info)

            # Call callback if provided
            if on_checkpoint:
                await on_checkpoint(snapshot.checkpoint, snapshot)

        return replay_info

    async def list_failed_executions(self) -> List[ExecutionContext]:
        """
        Get all failed executions that can be retried.

        Returns:
            List of failed ExecutionContext instances
        """
        return await self.storage.list_executions(
            status=ExecutionStatus.FAILED, limit=1000
        )

    async def list_awaiting_approval(self) -> List[ExecutionContext]:
        """
        Get all executions awaiting approval.

        Returns:
            List of ExecutionContext instances awaiting approval
        """
        return await self.storage.list_executions(
            status=ExecutionStatus.AWAITING_APPROVAL, limit=1000
        )

    async def list_rejected_executions(self) -> List[ExecutionContext]:
        """
        Get all rejected executions.

        Returns:
            List of rejected ExecutionContext instances
        """
        return await self.storage.list_executions(
            status=ExecutionStatus.REJECTED, limit=1000
        )
