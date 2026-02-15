"""Execution context for governance operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Status of an execution."""

    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionContext(BaseModel):
    """
    Context for a governed execution.

    Tracks the complete lifecycle of a governed function execution,
    including state, status, checkpoints, and metadata.
    """

    # Unique identifier
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Function metadata
    function_name: str
    function_module: str
    function_qualname: str

    # Execution details
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None

    # Input/Output
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None

    # State management
    state_snapshots: List[Dict[str, Any]] = Field(default_factory=list)
    current_checkpoint: Optional[str] = None
    checkpoint_history: List[str] = Field(default_factory=list)

    # Approval tracking
    approval_required: bool = False
    approval_requested_at: Optional[datetime] = None
    approval_decided_at: Optional[datetime] = None
    approver: Optional[str] = None
    approval_reason: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Parent/child relationships for nested governed calls
    parent_execution_id: Optional[str] = None
    child_execution_ids: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        use_enum_values = True

    def add_checkpoint(self, checkpoint: str) -> None:
        """Add a checkpoint to the execution history."""
        self.current_checkpoint = checkpoint
        self.checkpoint_history.append(checkpoint)

    def add_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Add a state snapshot."""
        self.state_snapshots.append(snapshot)

    def mark_running(self) -> None:
        """Mark execution as running."""
        self.status = ExecutionStatus.RUNNING

    def mark_awaiting_approval(self) -> None:
        """Mark execution as awaiting approval."""
        self.status = ExecutionStatus.AWAITING_APPROVAL
        self.approval_requested_at = datetime.now(timezone.utc)

    def mark_approved(self, approver: str, reason: Optional[str] = None) -> None:
        """Mark execution as approved."""
        self.status = ExecutionStatus.APPROVED
        self.approval_decided_at = datetime.now(timezone.utc)
        self.approver = approver
        self.approval_reason = reason

    def mark_rejected(self, approver: str, reason: Optional[str] = None) -> None:
        """Mark execution as rejected."""
        self.status = ExecutionStatus.REJECTED
        self.approval_decided_at = datetime.now(timezone.utc)
        self.approver = approver
        self.approval_reason = reason

    def mark_completed(self, output: Any) -> None:
        """Mark execution as completed."""
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.outputs = output
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = delta.total_seconds() * 1000

    def mark_failed(self, error: Exception) -> None:
        """Mark execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error = str(error)
        self.error_type = type(error).__name__
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = delta.total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(mode="json")
