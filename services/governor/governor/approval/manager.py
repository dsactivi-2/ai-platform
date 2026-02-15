"""Approval manager for human-in-the-loop governance."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ApprovalDecision(BaseModel):
    """Represents an approval decision."""

    execution_id: str
    approved: bool
    approver: str
    reason: Optional[str] = None
    decided_at: datetime


@dataclass
class PendingApproval:
    """Represents a pending approval request."""

    execution_id: str
    function_name: str
    inputs: Dict[str, Any]
    approvers: list[str]
    timeout_seconds: Optional[int]
    created_at: datetime
    decision_future: asyncio.Future[ApprovalDecision]


class ApprovalManager:
    """
    Manages approval requests and decisions.

    Coordinates between approval handlers (CLI, webhook, callback)
    and tracks pending approvals with timeouts.
    """

    def __init__(self) -> None:
        """Initialize approval manager."""
        self._pending: Dict[str, PendingApproval] = {}
        self._decisions: Dict[str, ApprovalDecision] = {}

    async def request_approval(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        approvers: list[str],
        timeout_seconds: Optional[int] = None,
    ) -> ApprovalDecision:
        """
        Request approval for an execution.

        Args:
            execution_id: Unique execution ID
            function_name: Name of the function to approve
            inputs: Function inputs for context
            approvers: List of approved approvers
            timeout_seconds: Optional timeout in seconds

        Returns:
            ApprovalDecision once decided

        Raises:
            TimeoutError: If timeout expires without decision
        """
        # Create pending approval
        decision_future: asyncio.Future[ApprovalDecision] = asyncio.Future()
        pending = PendingApproval(
            execution_id=execution_id,
            function_name=function_name,
            inputs=inputs,
            approvers=approvers,
            timeout_seconds=timeout_seconds,
            created_at=datetime.now(timezone.utc),
            decision_future=decision_future,
        )

        self._pending[execution_id] = pending

        # Wait for decision with optional timeout
        try:
            if timeout_seconds:
                decision = await asyncio.wait_for(decision_future, timeout=timeout_seconds)
            else:
                decision = await decision_future

            self._decisions[execution_id] = decision
            return decision

        except asyncio.TimeoutError:
            # Clean up pending approval
            self._pending.pop(execution_id, None)
            raise TimeoutError(
                f"Approval request timed out after {timeout_seconds} seconds"
            )

        finally:
            # Remove from pending
            self._pending.pop(execution_id, None)

    def provide_decision(
        self,
        execution_id: str,
        approved: bool,
        approver: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Provide a decision for a pending approval.

        Args:
            execution_id: Execution ID
            approved: Whether approved or rejected
            approver: Who made the decision
            reason: Optional reason for decision

        Returns:
            True if decision was recorded, False if no pending approval found
        """
        pending = self._pending.get(execution_id)
        if not pending:
            return False

        decision = ApprovalDecision(
            execution_id=execution_id,
            approved=approved,
            approver=approver,
            reason=reason,
            decided_at=datetime.now(timezone.utc),
        )

        # Set the result on the future
        if not pending.decision_future.done():
            pending.decision_future.set_result(decision)

        return True

    def get_pending_approvals(self) -> list[PendingApproval]:
        """Get all pending approval requests."""
        return list(self._pending.values())

    def get_decision(self, execution_id: str) -> Optional[ApprovalDecision]:
        """Get a decision if it has been made."""
        return self._decisions.get(execution_id)

    def is_pending(self, execution_id: str) -> bool:
        """Check if an approval is pending."""
        return execution_id in self._pending


# Global approval manager instance
_default_manager: Optional[ApprovalManager] = None


def get_default_approval_manager() -> ApprovalManager:
    """Get or create the default global approval manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ApprovalManager()
    return _default_manager


def set_default_approval_manager(manager: ApprovalManager) -> None:
    """Set the default global approval manager."""
    global _default_manager
    _default_manager = manager
