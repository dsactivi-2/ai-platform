"""Base storage interface for governance data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from governor.core.context import ExecutionContext
from governor.core.state import StateSnapshot
from governor.events.base import Event


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    Defines the interface for storing and retrieving governance data
    including execution contexts, state snapshots, and events.
    """

    @abstractmethod
    async def store_execution(self, context: ExecutionContext) -> None:
        """
        Store or update an execution context.

        Args:
            context: ExecutionContext to store
        """
        pass

    @abstractmethod
    async def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """
        Retrieve an execution context by ID.

        Args:
            execution_id: Unique execution ID

        Returns:
            ExecutionContext if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_executions(
        self,
        function_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ExecutionContext]:
        """
        List execution contexts with optional filtering.

        Args:
            function_name: Filter by function name
            status: Filter by execution status
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of ExecutionContext instances
        """
        pass

    @abstractmethod
    async def store_snapshot(self, snapshot: StateSnapshot) -> None:
        """
        Store a state snapshot.

        Args:
            snapshot: StateSnapshot to store
        """
        pass

    @abstractmethod
    async def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """
        Retrieve a state snapshot by ID.

        Args:
            snapshot_id: Unique snapshot ID

        Returns:
            StateSnapshot if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_snapshots_by_execution(
        self, execution_id: str
    ) -> List[StateSnapshot]:
        """
        Get all snapshots for an execution.

        Args:
            execution_id: Execution ID

        Returns:
            List of StateSnapshot instances
        """
        pass

    @abstractmethod
    async def store_event(self, event: Event) -> None:
        """
        Store an event.

        Args:
            event: Event to store
        """
        pass

    @abstractmethod
    async def get_events(
        self,
        execution_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        """
        Get events with optional filtering.

        Args:
            execution_id: Filter by execution ID
            event_type: Filter by event type
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of Event instances
        """
        pass

    @abstractmethod
    async def store_approval(
        self,
        execution_id: str,
        approver: str,
        approved: bool,
        reason: Optional[str] = None,
    ) -> None:
        """
        Store an approval decision.

        Args:
            execution_id: Execution ID
            approver: Approver identifier
            approved: Whether approved or rejected
            reason: Optional reason for decision
        """
        pass

    @abstractmethod
    async def get_approval(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get approval decision for an execution.

        Args:
            execution_id: Execution ID

        Returns:
            Approval data if found, None otherwise
        """
        pass

    async def close(self) -> None:
        """Close storage connections (optional)."""
        pass
