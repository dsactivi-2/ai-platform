"""State snapshot and serialization for governance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from governor.utils.serialization import safe_serialize_bytes, safe_deserialize_bytes


class StateSnapshot(BaseModel):
    """
    Immutable snapshot of execution state at a specific point in time.

    Captures the complete state of a governed execution, allowing for
    replay, debugging, and recovery.
    """

    # Snapshot metadata
    snapshot_id: str
    execution_id: str
    checkpoint: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # State data
    local_vars: Dict[str, Any] = Field(default_factory=dict)
    function_args: Dict[str, Any] = Field(default_factory=dict)
    function_kwargs: Dict[str, Any] = Field(default_factory=dict)
    intermediate_results: Optional[Any] = None

    # Context
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Serialization
    serialized_state: Optional[bytes] = None

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: v.hex() if v else None,
        }

    @classmethod
    def capture(
        cls,
        execution_id: str,
        checkpoint: str,
        snapshot_id: str,
        local_vars: Optional[Dict[str, Any]] = None,
        function_args: Optional[Dict[str, Any]] = None,
        function_kwargs: Optional[Dict[str, Any]] = None,
        intermediate_results: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateSnapshot:
        """
        Capture a state snapshot.

        Args:
            execution_id: ID of the execution
            checkpoint: Name of the checkpoint
            snapshot_id: Unique ID for this snapshot
            local_vars: Local variables at this point
            function_args: Function positional arguments
            function_kwargs: Function keyword arguments
            intermediate_results: Any intermediate results
            metadata: Additional metadata

        Returns:
            StateSnapshot instance
        """
        snapshot = cls(
            snapshot_id=snapshot_id,
            execution_id=execution_id,
            checkpoint=checkpoint,
            local_vars=local_vars or {},
            function_args=function_args or {},
            function_kwargs=function_kwargs or {},
            intermediate_results=intermediate_results,
            metadata=metadata or {},
        )

        # Attempt to serialize complex state using safe JSON serialization
        try:
            state_to_serialize = {
                "local_vars": snapshot.local_vars,
                "function_args": snapshot.function_args,
                "function_kwargs": snapshot.function_kwargs,
                "intermediate_results": snapshot.intermediate_results,
            }
            snapshot.serialized_state = safe_serialize_bytes(state_to_serialize)
        except Exception:
            # If serialization fails, we still have the dict representation
            pass

        return snapshot

    def restore_state(self) -> Dict[str, Any]:
        """
        Restore state from snapshot.

        Returns:
            Dictionary containing the restored state

        Raises:
            ValueError: If state cannot be restored
        """
        if self.serialized_state:
            try:
                return safe_deserialize_bytes(self.serialized_state)
            except Exception as e:
                raise ValueError(f"Failed to deserialize state: {e}") from e

        # Fallback to dict representation
        return {
            "local_vars": self.local_vars,
            "function_args": self.function_args,
            "function_kwargs": self.function_kwargs,
            "intermediate_results": self.intermediate_results,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without serialized bytes)."""
        data = self.model_dump(mode="json")
        # Remove serialized_state from dict representation
        data.pop("serialized_state", None)
        return data
