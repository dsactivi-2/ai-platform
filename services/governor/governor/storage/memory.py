"""In-memory storage backend for development and testing."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from governor.core.context import ExecutionContext
from governor.core.state import StateSnapshot
from governor.events.base import Event
from governor.storage.base import StorageBackend


class InMemoryStorage(StorageBackend):
    """
    In-memory storage backend.

    Stores all data in memory. Useful for development, testing,
    and simple deployments. Data is lost when process terminates.
    """

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._executions: Dict[str, ExecutionContext] = {}
        self._snapshots: Dict[str, StateSnapshot] = {}
        self._snapshots_by_execution: Dict[str, List[StateSnapshot]] = defaultdict(list)
        self._events: List[Event] = []
        self._approvals: Dict[str, Dict[str, Any]] = {}

    async def store_execution(self, context: ExecutionContext) -> None:
        """Store or update an execution context."""
        self._executions[context.execution_id] = context

    async def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """Retrieve an execution context by ID."""
        return self._executions.get(execution_id)

    async def list_executions(
        self,
        function_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ExecutionContext]:
        """List execution contexts with optional filtering."""
        executions = list(self._executions.values())

        # Filter by function name
        if function_name:
            executions = [e for e in executions if e.function_name == function_name]

        # Filter by status
        if status:
            executions = [e for e in executions if e.status == status]

        # Sort by start time (newest first)
        executions.sort(key=lambda e: e.started_at, reverse=True)

        # Apply pagination
        return executions[offset : offset + limit]

    async def store_snapshot(self, snapshot: StateSnapshot) -> None:
        """Store a state snapshot."""
        self._snapshots[snapshot.snapshot_id] = snapshot
        self._snapshots_by_execution[snapshot.execution_id].append(snapshot)

    async def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """Retrieve a state snapshot by ID."""
        return self._snapshots.get(snapshot_id)

    async def get_snapshots_by_execution(self, execution_id: str) -> List[StateSnapshot]:
        """Get all snapshots for an execution."""
        return self._snapshots_by_execution.get(execution_id, [])

    async def store_event(self, event: Event) -> None:
        """Store an event."""
        self._events.append(event)

    async def get_events(
        self,
        execution_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        """Get events with optional filtering."""
        events = self._events

        # Filter by execution ID
        if execution_id:
            events = [e for e in events if e.execution_id == execution_id]

        # Filter by event type
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Sort by timestamp (newest first)
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return events[offset : offset + limit]

    async def store_approval(
        self,
        execution_id: str,
        approver: str,
        approved: bool,
        reason: Optional[str] = None,
    ) -> None:
        """Store an approval decision."""
        self._approvals[execution_id] = {
            "execution_id": execution_id,
            "approver": approver,
            "approved": approved,
            "reason": reason,
            "decided_at": datetime.utcnow().isoformat(),
        }

    async def get_approval(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get approval decision for an execution."""
        return self._approvals.get(execution_id)

    def clear(self) -> None:
        """Clear all stored data."""
        self._executions.clear()
        self._snapshots.clear()
        self._snapshots_by_execution.clear()
        self._events.clear()
        self._approvals.clear()
