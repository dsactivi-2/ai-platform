"""Base event types for governance operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of governance events."""

    # Execution lifecycle
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_CANCELLED = "execution.cancelled"

    # State management
    STATE_CAPTURED = "state.captured"
    STATE_RESTORED = "state.restored"
    CHECKPOINT_REACHED = "checkpoint.reached"

    # Approval workflow
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_TIMEOUT = "approval.timeout"

    # Policy enforcement
    POLICY_EVALUATED = "policy.evaluated"
    POLICY_PASSED = "policy.passed"
    POLICY_FAILED = "policy.failed"
    POLICY_VIOLATED = "policy.violated"

    # Actions
    PRE_ACTION_STARTED = "pre_action.started"
    PRE_ACTION_COMPLETED = "pre_action.completed"
    PRE_ACTION_FAILED = "pre_action.failed"
    POST_ACTION_STARTED = "post_action.started"
    POST_ACTION_COMPLETED = "post_action.completed"
    POST_ACTION_FAILED = "post_action.failed"

    # Custom events
    CUSTOM = "custom"


class Event(BaseModel):
    """
    Base event class for governance operations.

    All governance events inherit from this class and are emitted
    to the event system for tracking, auditing, and notification.
    """

    # Event metadata
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Execution context
    execution_id: str
    function_name: str

    # Event data
    data: Dict[str, Any] = Field(default_factory=dict)

    # Additional context
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    # Source tracking
    source: str = "governor"
    source_version: str = "0.1.0"

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def create(
        cls,
        event_type: EventType,
        execution_id: str,
        function_name: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
    ) -> Event:
        """
        Create a new event.

        Args:
            event_type: Type of event
            execution_id: ID of the execution
            function_name: Name of the governed function
            data: Event-specific data
            metadata: Additional metadata
            tags: Tags for categorization

        Returns:
            New Event instance
        """
        return cls(
            event_type=event_type,
            execution_id=execution_id,
            function_name=function_name,
            data=data or {},
            metadata=metadata or {},
            tags=tags or [],
        )


# Convenience event creators
class ExecutionStartedEvent(Event):
    """Event emitted when execution starts."""

    def __init__(self, execution_id: str, function_name: str, inputs: Dict[str, Any], **kwargs: Any):
        super().__init__(
            event_type=EventType.EXECUTION_STARTED,
            execution_id=execution_id,
            function_name=function_name,
            data={"inputs": inputs},
            **kwargs,
        )


class ExecutionCompletedEvent(Event):
    """Event emitted when execution completes successfully."""

    def __init__(
        self, execution_id: str, function_name: str, outputs: Any, duration_ms: float, **kwargs: Any
    ):
        super().__init__(
            event_type=EventType.EXECUTION_COMPLETED,
            execution_id=execution_id,
            function_name=function_name,
            data={"outputs": outputs, "duration_ms": duration_ms},
            **kwargs,
        )


class ExecutionFailedEvent(Event):
    """Event emitted when execution fails."""

    def __init__(
        self, execution_id: str, function_name: str, error: str, error_type: str, **kwargs: Any
    ):
        super().__init__(
            event_type=EventType.EXECUTION_FAILED,
            execution_id=execution_id,
            function_name=function_name,
            data={"error": error, "error_type": error_type},
            **kwargs,
        )


class ApprovalRequestedEvent(Event):
    """Event emitted when approval is requested."""

    def __init__(
        self,
        execution_id: str,
        function_name: str,
        approvers: list[str],
        timeout_seconds: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(
            event_type=EventType.APPROVAL_REQUESTED,
            execution_id=execution_id,
            function_name=function_name,
            data={"approvers": approvers, "timeout_seconds": timeout_seconds},
            **kwargs,
        )


class ApprovalGrantedEvent(Event):
    """Event emitted when approval is granted."""

    def __init__(
        self, execution_id: str, function_name: str, approver: str, reason: Optional[str] = None, **kwargs: Any
    ):
        super().__init__(
            event_type=EventType.APPROVAL_GRANTED,
            execution_id=execution_id,
            function_name=function_name,
            data={"approver": approver, "reason": reason},
            **kwargs,
        )


class ApprovalRejectedEvent(Event):
    """Event emitted when approval is rejected."""

    def __init__(
        self, execution_id: str, function_name: str, approver: str, reason: Optional[str] = None, **kwargs: Any
    ):
        super().__init__(
            event_type=EventType.APPROVAL_REJECTED,
            execution_id=execution_id,
            function_name=function_name,
            data={"approver": approver, "reason": reason},
            **kwargs,
        )


class PolicyViolatedEvent(Event):
    """Event emitted when a policy is violated."""

    def __init__(
        self,
        execution_id: str,
        function_name: str,
        policy_name: str,
        violation_reason: str,
        **kwargs: Any,
    ):
        super().__init__(
            event_type=EventType.POLICY_VIOLATED,
            execution_id=execution_id,
            function_name=function_name,
            data={"policy_name": policy_name, "violation_reason": violation_reason},
            **kwargs,
        )
